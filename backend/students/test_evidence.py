import io
import tempfile
from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.core import mail
from django.core.files.base import ContentFile
from django.test import TransactionTestCase, override_settings
from django.views.static import serve
from django.test import RequestFactory
from PIL import Image

from .models import GateCycle, GateController
from .gate import save_violation
from .models import Student, AccessAttempt, AIInspection, Violation, ViolationReport, ViolationEmail, GateController
from .notifications import deliver_notification


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
                   DEFAULT_FROM_EMAIL="system@example.test")
class EvidenceTests(TransactionTestCase):
    def setUp(self):
        GateController.objects.get_or_create(pk=1)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        setting = override_settings(MEDIA_ROOT=self.temp.name)
        setting.enable()
        self.addCleanup(setting.disable)
        self.student = Student.objects.create(student_number="EVIDENCE-1", full_name="First Student",
                                              email="first@example.test", college="SEA")

    def capture(self, student=None, color="red", confirmed=True):
        student = student or self.student
        attempt = AccessAttempt.objects.create(student=student, entered=True, gate_opened=True)
        GateCycle.objects.create(attempt=attempt, phase="CLOSED", outcome="ENTERED")
        inspection = AIInspection.objects.create(student=student, attempt=attempt,
            confirmation_status="CONFIRMED_ALLOW" if confirmed else "PENDING", violations=["Knees exposed"])
        data = io.BytesIO()
        Image.new("RGB", (20, 30), color).save(data, format="PNG")
        inspection.screenshot.save("evidence.png", ContentFile(data.getvalue()))
        return inspection, data.getvalue()

    def test_osa_review_exact_link_media_and_email(self):
        inspection, data = self.capture()
        self.assertTrue(save_violation(inspection.pk))
        report = ViolationReport.objects.get()
        self.assertEqual(report.inspection_id, inspection.pk)
        self.assertEqual(Violation.objects.get().inspection_id, inspection.pk)
        row = self.client.get("/api/students/records/sea/").json()["records"][0]
        self.assertEqual(row["id"], report.pk)
        self.assertEqual(row["evidence_image"], "http://testserver" + inspection.screenshot.url)
        response = serve(RequestFactory().get(inspection.screenshot.url),
                         inspection.screenshot.name, document_root=self.temp.name)
        self.assertEqual(b"".join(response.streaming_content), data)
        response.close()
        notice = ViolationEmail.objects.get()
        # Even an inconsistent queue link must not override the report's evidence.
        other, _ = self.capture(color="blue")
        notice.inspection = other
        notice.save(update_fields=["inspection"])
        self.assertTrue(deliver_notification(notice.pk))
        self.assertEqual(mail.outbox[-1].attachments[0].content, data)

    def test_students_days_and_daily_duplicate_keep_original(self):
        other = Student.objects.create(student_number="EVIDENCE-2", full_name="Second Student",
                                        email="second@example.test", college="SEA")
        with patch("django.utils.timezone.now", return_value=datetime(2026, 9, 20, 2, tzinfo=dt_timezone.utc)):
            first, _ = self.capture()
            self.assertTrue(save_violation(first.pk))
            duplicate, _ = self.capture(color="blue")
            self.assertFalse(save_violation(duplicate.pk))
            second, _ = self.capture(student=other, color="green")
            self.assertTrue(save_violation(second.pk))
        with patch("django.utils.timezone.now", return_value=datetime(2026, 9, 21, 2, tzinfo=dt_timezone.utc)):
            tomorrow, _ = self.capture(color="yellow")
            self.assertTrue(save_violation(tomorrow.pk))
        records = self.client.get("/api/students/records/sea/").json()["records"]
        expected = {(first.student.student_number, "2026-09-20"): first,
                    (second.student.student_number, "2026-09-20"): second,
                    (tomorrow.student.student_number, "2026-09-21"): tomorrow}
        self.assertEqual(len(records), 3)
        for row in records:
            source = expected[(row["studentNumber"], row["date"])]
            self.assertEqual(row["evidence_image"], "http://testserver" + source.screenshot.url)
        self.assertEqual(ViolationEmail.objects.count(), 3)
        self.assertEqual(Violation.objects.count(), 3)

    def test_old_records_and_deleted_inspection_are_null(self):
        report = ViolationReport.objects.create(student=self.student, violation_type="Historical", confirmed_entry=True)
        self.capture()  # Unrelated evidence must never be guessed.
        row = self.client.get("/api/students/records/").json()["records"][0]
        self.assertIsNone(row["evidence_image"])
        inspection, _ = self.capture()
        report.inspection = inspection
        report.save()
        inspection.delete()
        report.refresh_from_db()
        self.assertIsNone(report.inspection_id)
        self.assertIsNone(self.client.get("/api/students/records/").json()["records"][0]["evidence_image"])
