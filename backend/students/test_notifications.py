import io
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.core import mail
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.db import close_old_connections, transaction
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from PIL import Image

from .models import GateCycle, GateController
from .gate import save_violation
from .models import (Student, AccessAttempt, AIInspection, Violation, ViolationReport,
                     ViolationEmail, GateController, GateCycle, EntryLog)
from .notifications import deliver_notification


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
                   DEFAULT_FROM_EMAIL="system@example.test")
class NotificationTests(TransactionTestCase):
    def setUp(self):
        GateController.objects.get_or_create(pk=1)
        self.student = Student.objects.create(student_number="MAIL-1", full_name="Mail Student",
                                              email="student@example.test", college="SOC")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.media = override_settings(MEDIA_ROOT=self.temp.name)
        self.media.enable()
        self.addCleanup(self.media.disable)
        mail.outbox = []

    def inspection(self, student=None, state="CONFIRMED_ALLOW", entered=True, types=None):
        student = student or self.student
        attempt = AccessAttempt.objects.create(student=student, entered=entered, gate_opened=True)
        GateCycle.objects.create(attempt=attempt, phase="CLOSED", outcome="ENTERED" if entered else "PENDING")
        return AIInspection.objects.create(student=student, attempt=attempt,
                                           confirmation_status=state,
                                           violations=types or ["Shoulders", "Knees"])

    def queue(self, inspection=None):
        inspection = inspection or self.inspection()
        self.assertTrue(save_violation(inspection.pk))
        return ViolationEmail.objects.get(inspection=inspection)

    def test_attachment_is_exact_stored_image_and_one_email_for_all_types(self):
        for extension, image_format, mime in [("jpg", "JPEG", "image/jpeg"), ("png", "PNG", "image/png")]:
            with self.subTest(extension=extension):
                student = Student.objects.create(student_number=extension, full_name="Image Student",
                                                 email="image@example.test", college="SOC")
                inspection = self.inspection(student=student)
                data = io.BytesIO()
                Image.new("RGB", (2, 2), "red").save(data, format=image_format)
                inspection.screenshot.save("evidence." + extension, ContentFile(data.getvalue()))
                notice = self.queue(inspection)
                self.assertEqual(len(mail.outbox), 0)
                self.assertTrue(deliver_notification(notice.pk))
                message = mail.outbox.pop()
                self.assertEqual(message.subject, "SHESEETVAI - Dress Code Violation Notice")
                self.assertEqual(message.to, [student.email])
                self.assertIn("Dear Image Student,", message.body)
                self.assertIn("Shoulders, Knees", message.body)
                self.assertNotIn("Entry Denied", message.body)
                self.assertEqual(message.attachments[0].content, data.getvalue())
                self.assertEqual(message.attachments[0].mimetype, mime)
                self.assertEqual(message.attachments[0].filename, "evidence." + extension)
                self.assertFalse(deliver_notification(notice.pk))
                notice.refresh_from_db()
                self.assertEqual(notice.status, "SENT")
                self.assertIsNotNone(notice.sent_at)

    def test_same_day_different_attempt_and_types_do_not_add_rows_or_emails(self):
        first = self.inspection()
        notice = self.queue(first)
        second = self.inspection(types=["Shoes"])
        self.assertFalse(save_violation(second.pk))
        self.assertFalse(save_violation(first.pk))
        self.assertEqual(ViolationReport.objects.count(), 1)
        self.assertEqual(Violation.objects.count(), 1)  # One offense, multiple types.
        self.assertEqual(ViolationEmail.objects.count(), 1)
        self.assertEqual(EntryLog.objects.count(), 2)  # Entry still proceeds.
        second.refresh_from_db()
        self.assertTrue(second.recorded)
        deliver_notification(notice.pk)
        self.assertEqual(len(mail.outbox), 1)

    def test_manila_midnight_allows_next_day_but_not_replay_of_skipped_inspection(self):
        before = datetime(2026, 9, 18, 15, 59, tzinfo=dt_timezone.utc)
        after = datetime(2026, 9, 18, 16, 1, tzinfo=dt_timezone.utc)
        with patch("django.utils.timezone.now", return_value=before):
            self.queue()
            skipped = self.inspection()
            self.assertFalse(save_violation(skipped.pk))
        with patch("django.utils.timezone.now", return_value=after):
            self.assertFalse(save_violation(skipped.pk))
            self.queue()
        self.assertEqual(ViolationReport.objects.count(), 2)
        self.assertEqual(ViolationEmail.objects.count(), 2)

    def test_active_timezone_does_not_change_school_day(self):
        first = datetime(2026, 9, 18, 15, 0, tzinfo=dt_timezone.utc)
        second = datetime(2026, 9, 18, 16, 5, tzinfo=dt_timezone.utc)
        with patch("django.utils.timezone.now", return_value=first):
            self.queue()
        with timezone.override("UTC"), patch("django.utils.timezone.now", return_value=second):
            self.queue()
        self.assertEqual(ViolationReport.objects.count(), 2)

    def test_existing_report_blocks_new_record_without_backfill_email(self):
        ViolationReport.objects.create(student=self.student, violation_type="Existing", confirmed_entry=True)
        self.assertFalse(save_violation(self.inspection().pk))
        self.assertFalse(ViolationEmail.objects.exists())

    def test_different_students_each_get_a_notice(self):
        self.queue()
        other = Student.objects.create(student_number="MAIL-2", full_name="Other",
                                       email="other@example.test", college="SOC")
        self.queue(self.inspection(student=other))
        self.assertEqual(ViolationEmail.objects.count(), 2)

    def test_pending_rejected_unentered_and_cancelled_never_queue(self):
        inspections = [self.inspection(state="PENDING"), self.inspection(state="REJECTED"),
                       self.inspection(entered=False)]
        cancelled = self.inspection()
        GateCycle.objects.filter(attempt=cancelled.attempt).update(outcome="WALKED_AWAY")
        for inspection in inspections + [cancelled]:
            self.assertFalse(save_violation(inspection.pk))
        self.assertFalse(ViolationEmail.objects.exists())
        self.assertFalse(ViolationReport.objects.exists())

    def test_rollback_discards_report_and_notification(self):
        inspection = self.inspection()
        with self.assertRaises(RuntimeError), transaction.atomic():
            self.queue(inspection)
            raise RuntimeError("rollback")
        self.assertFalse(ViolationReport.objects.exists())
        self.assertFalse(ViolationEmail.objects.exists())
        self.assertEqual(mail.outbox, [])
        inspection.refresh_from_db()
        self.assertFalse(inspection.recorded)

    def test_delivery_refuses_uncommitted_transaction(self):
        notice = self.queue()
        with transaction.atomic(), self.assertRaises(RuntimeError):
            deliver_notification(notice.pk)
        notice.refresh_from_db()
        self.assertEqual(notice.status, "PENDING")

    def test_missing_or_invalid_student_email_does_not_break_recording(self):
        for address in ("", "invalid"):
            self.student.email = address
            self.student.save()
            notice = self.queue()
            self.assertFalse(deliver_notification(notice.pk))
            notice.refresh_from_db()
            self.assertEqual(notice.status, "SKIPPED")
            notice.report.delete()
        self.assertEqual(mail.outbox, [])

    def test_absent_or_missing_image_still_sends(self):
        for name in ("", "ai_inspections/missing.jpg"):
            inspection = self.inspection()
            inspection.screenshot = name
            inspection.save()
            notice = self.queue(inspection)
            self.assertTrue(deliver_notification(notice.pk))
            self.assertEqual(mail.outbox[-1].attachments, [])
            self.assertIn("No evidence image", mail.outbox[-1].body)
            notice.report.delete()

    def test_smtp_failure_never_reverses_record_or_automatically_resends(self):
        notice = self.queue()
        with patch("students.notifications.EmailMessage.send", side_effect=TimeoutError("private detail")) as send:
            self.assertFalse(deliver_notification(notice.pk))
            self.assertFalse(deliver_notification(notice.pk))
            self.assertEqual(send.call_count, 1)
        notice.refresh_from_db()
        self.assertEqual(notice.status, "FAILED")
        self.assertEqual(notice.error, "TimeoutError")
        self.assertEqual(ViolationReport.objects.count(), 1)
        self.assertEqual(EntryLog.objects.count(), 1)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
                       EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="")
    def test_unconfigured_smtp_keeps_notice_pending(self):
        notice = self.queue()
        with patch("students.notifications.EmailMessage.send") as send:
            self.assertFalse(deliver_notification(notice.pk))
            send.assert_not_called()
        notice.refresh_from_db()
        self.assertEqual(notice.status, "PENDING")

    def test_unrelated_saves_and_refreshes_do_not_queue(self):
        self.student.save()
        AccessAttempt.objects.create(student=self.student, entered=True, has_violation=True)
        Violation.objects.create(student=self.student, violation_type="Admin record")
        for url in ("/api/students/records/", "/api/students/dashboard/"):
            self.assertEqual(self.client.get(url).status_code, 200)
        self.assertFalse(ViolationEmail.objects.exists())

    def test_worker_command_does_not_resend(self):
        self.queue()
        call_command("send_violation_emails", stdout=io.StringIO())
        call_command("send_violation_emails", stdout=io.StringIO())
        self.assertEqual(len(mail.outbox), 1)

    def test_parallel_claims_send_only_once(self):
        notice = self.queue()
        # Both processes compete on one atomic conditional UPDATE. Retry database
        # contention exactly as the watch worker does, never replay a claimed send.
        def deliver():
            from django.db import OperationalError
            import time
            close_old_connections()
            try:
                for _ in range(20):
                    try:
                        return deliver_notification(notice.pk)
                    except OperationalError:
                        time.sleep(0.01)
                raise AssertionError("worker remained locked")
            finally:
                close_old_connections()
        with patch("students.notifications.EmailMessage.send", return_value=1) as send:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: deliver(), range(2)))
            self.assertEqual(sorted(results), [False, True])
            self.assertEqual(send.call_count, 1)

    def test_concurrent_inspections_create_only_one_daily_report(self):
        ids = [self.inspection().pk, self.inspection().pk]
        def record(pk):
            from django.db import OperationalError
            import time
            close_old_connections()
            try:
                for _ in range(30):
                    try:
                        return save_violation(pk)
                    except OperationalError:
                        time.sleep(0.01)
                raise AssertionError("recorder remained locked")
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(record, ids))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(ViolationReport.objects.count(), 1)
        self.assertEqual(ViolationEmail.objects.count(), 1)

    def test_ai_upload_and_review_api_queue_only_once_after_confirmation(self):
        attempt = AccessAttempt.objects.create(student=self.student, entered=True, gate_opened=True)
        payload = {"student_number": self.student.student_number, "attempt_id": attempt.pk,
                   "status": "VIOLATION", "violations": ["Knees"]}
        response = self.client.post("/api/students/ai-result/", payload, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(ViolationEmail.objects.exists())
        self.assertTrue(self.client.post("/api/students/ai-result/", payload,
                                        content_type="application/json").json()["ignored"])
        review = {"inspection_id": response.json()["inspection_id"], "decision": "YES"}
        self.assertEqual(self.client.post("/api/students/ai-inspection/review/", review).status_code, 409)
        self.assertEqual(self.client.post("/api/students/ai-inspection/review/", review).status_code, 409)
        self.assertEqual(ViolationEmail.objects.count(), 0)
        self.assertEqual(ViolationReport.objects.count(), 0)
        self.assertEqual(mail.outbox, [])

    def test_pass_and_rejected_api_results_never_queue(self):
        attempt = AccessAttempt.objects.create(student=self.student, entered=True, gate_opened=True)
        response = self.client.post("/api/students/ai-result/", {
            "student_number": self.student.student_number, "attempt_id": attempt.pk, "status": "PASS",
        }, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        inspection = self.inspection(state="PENDING")
        response = self.client.post("/api/students/ai-inspection/review/", {
            "inspection_id": inspection.pk, "decision": "NO",
        })
        self.assertEqual(response.status_code, 409)
        self.assertFalse(ViolationEmail.objects.exists())
        self.assertFalse(ViolationReport.objects.exists())
