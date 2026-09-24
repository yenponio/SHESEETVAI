"""Adviser workflow: real HTTP review + bridge events, isolated mail/storage."""
import io
import tempfile
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase, override_settings
from PIL import Image

from .gate import apply_event, claim_open, GateError, save_violation, end_session
from .models import (Student, AccessAttempt, AIInspection, GateCycle, GateController,
                     Violation, ViolationReport, ViolationEmail, EntryLog)
from .notifications import deliver_notification
from .offenses import offense_counts


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
                   DEFAULT_FROM_EMAIL="system@example.test")
class OfficialWorkflowTests(TransactionTestCase):
    def setUp(self):
        GateController.objects.update_or_create(pk=1, defaults=dict(
            enabled=True, connected=True, ready=True, bridge_id="workflow", process_id=123))
        self.running = patch("students.gate.bridge_running", side_effect=lambda c: c.connected)
        self.running.start()
        self.addCleanup(self.running.stop)
        self.review_running = patch("students.views.bridge_running", side_effect=lambda c: c.connected)
        self.review_running.start()
        self.addCleanup(self.review_running.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.media = override_settings(MEDIA_ROOT=self.temp.name)
        self.media.enable()
        self.addCleanup(self.media.disable)
        self.student = Student.objects.create(student_number="FINAL-1", barcode="12345",
            full_name="Workflow Student", email="student@example.test", college="SOC")
        mail.outbox = []
        self.sequence = 0

    def scan_ai(self, result="VIOLATION", color="red"):
        response = self.client.post("/api/students/scan/", {"barcode": self.student.barcode})
        self.assertEqual(response.status_code, 200, response.content)
        self.attempt = AccessAttempt.objects.get(pk=response.json()["attempt_id"])
        self.assertFalse(self.attempt.gate_opened)
        self.assertFalse(self.attempt.entered)
        self.assertIsNone(claim_open("workflow"))
        data = io.BytesIO()
        Image.new("RGB", (4, 4), color).save(data, format="PNG")
        self.image = data.getvalue()
        response = self.client.post("/api/students/ai-result/", {
            "student_number": self.student.student_number, "attempt_id": self.attempt.pk,
            "status": result, "violations": '["Shoulders", "Knees"]',
            "screenshot": SimpleUploadedFile("evidence.png", self.image, "image/png"),
        })
        self.assertEqual(response.status_code, 201, response.content)
        self.inspection = AIInspection.objects.get(pk=response.json()["inspection_id"])
        self.assertIsNone(claim_open("workflow"))
        pending = self.client.get("/api/students/ai-inspection/pending/").json()["inspection"]
        self.assertEqual(pending["id"], self.inspection.pk)
        self.assertEqual(pending["screenshot"], "http://testserver" + self.inspection.screenshot.url)

    def review(self, decision):
        return self.client.post("/api/students/ai-inspection/review/", {
            "inspection_id": self.inspection.pk, "decision": decision})

    def event(self, event):
        self.sequence += 1
        apply_event("workflow", self.attempt.pk, event, f"workflow:{self.sequence}")

    def open(self):
        self.assertEqual(claim_open("workflow"), self.attempt.pk)
        self.assertIsNone(claim_open("workflow"))
        self.attempt.refresh_from_db()
        self.assertFalse(self.attempt.gate_opened)
        self.event("OPENING")
        self.attempt.refresh_from_db()
        self.assertFalse(self.attempt.gate_opened)
        self.event("OPEN_ESTIMATED")
        self.attempt.refresh_from_db()
        self.assertTrue(self.attempt.gate_opened)
        self.assertFalse(self.attempt.entered)

    def finish(self, outcome="ENTERED"):
        self.event(outcome)
        self.event("CLOSING")
        self.event("CLOSED_ESTIMATED")

    def official(self):
        self.scan_ai()
        self.assertEqual(self.review("YES").status_code, 200)
        self.open()
        self.finish()

    def assert_no_offense(self):
        self.assertFalse(Violation.objects.exists())
        self.assertFalse(ViolationReport.objects.exists())
        self.assertFalse(ViolationEmail.objects.exists())
        self.assertEqual(offense_counts(self.student.pk)["total_minor_offenses"], 0)
        self.assertEqual(mail.outbox, [])

    def test_yes_entry_creates_one_minor_with_exact_evidence_and_email(self):
        self.scan_ai()
        self.assertEqual(self.review("YES").status_code, 200)
        self.assert_no_offense()
        self.open()
        self.assert_no_offense()
        self.finish()
        self.assertEqual(Violation.objects.count(), 1)  # Two types, one minor.
        report = ViolationReport.objects.get()
        self.assertEqual(report.inspection_id, self.inspection.pk)
        self.assertEqual(Violation.objects.get().inspection_id, self.inspection.pk)
        self.assertEqual(offense_counts(self.student.pk), {"total_minor_offenses": 1, "equivalent_major_offenses": 0})
        self.assertEqual(mail.outbox, [])  # Worker only sees committed queue.
        self.assertTrue(deliver_notification(ViolationEmail.objects.get().pk))
        self.assertEqual(mail.outbox[0].attachments[0].content, self.image)
        self.assertIn("Current Minor Offenses: 1", mail.outbox[0].body)
        self.assertIn("Equivalent Major Offenses: 0", mail.outbox[0].body)
        row = self.client.get("/api/students/records/").json()["records"][0]
        self.assertEqual(row["evidence_image"], "http://testserver" + self.inspection.screenshot.url)
        self.assertEqual(row["total_minor_offenses"], 1)

    def test_yes_walkaway_never_records(self):
        self.scan_ai()
        self.review("YES")
        self.open()
        self.finish("WALKED_AWAY")
        self.assert_no_offense()
        self.assertFalse(EntryLog.objects.exists())

    def test_no_opens_and_logs_normal_entry(self):
        self.scan_ai()
        self.assertEqual(self.review("NO").status_code, 200)
        self.open()
        self.finish()
        self.attempt.refresh_from_db()
        self.assertTrue(self.attempt.entered)
        self.assertFalse(self.attempt.has_violation)
        self.assertEqual(EntryLog.objects.count(), 1)
        self.assert_no_offense()

    def test_deny_never_opens_or_counts_and_next_scan_is_allowed(self):
        self.scan_ai()
        self.assertEqual(self.review("DENY").status_code, 200)
        self.assertIsNone(claim_open("workflow"))
        self.attempt.refresh_from_db()
        self.inspection.refresh_from_db()
        self.assertEqual(self.inspection.confirmation_status, "CONFIRMED_DENY")
        self.assertFalse(self.attempt.gate_opened)
        self.assertFalse(self.attempt.entered)
        self.assertFalse(save_violation(self.inspection.pk))
        with self.assertRaises(GateError):
            self.event("ENTERED")
        self.assert_no_offense()
        self.assertFalse(EntryLog.objects.exists())
        self.assertEqual(self.client.get("/api/students/dashboard/").json()["total_violations"], 0)
        self.scan_ai()

    def test_same_day_duplicate_preserves_first_evidence_and_normal_entry(self):
        self.official()
        first = ViolationReport.objects.get()
        image = self.image
        deliver_notification(ViolationEmail.objects.get().pk)
        self.scan_ai(color="blue")
        self.review("YES")
        self.open()
        self.finish()
        self.assertEqual(EntryLog.objects.count(), 2)
        self.assertEqual(Violation.objects.count(), 1)
        self.assertEqual(ViolationReport.objects.count(), 1)
        self.assertEqual(ViolationEmail.objects.count(), 1)
        self.assertFalse(deliver_notification(ViolationEmail.objects.get().pk))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments[0].content, image)
        self.assertEqual(ViolationReport.objects.get().inspection_id, first.inspection_id)

    def test_local_midnight_allows_new_offense_and_email(self):
        for moment in (datetime(2026, 9, 23, 15, 59, tzinfo=dt_timezone.utc),
                       datetime(2026, 9, 23, 16, 1, tzinfo=dt_timezone.utc)):
            with patch("django.utils.timezone.now", return_value=moment):
                self.official()
                deliver_notification(ViolationEmail.objects.order_by("pk").last().pk)
        self.assertEqual(Violation.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_total_minors_and_major_equivalents_keep_all_history(self):
        for total in range(1, 10):
            moment = datetime(2026, 9, 1, tzinfo=dt_timezone.utc) + timedelta(days=total)
            with patch("django.utils.timezone.now", return_value=moment):
                self.official()
            self.assertEqual(offense_counts(self.student.pk), {
                "total_minor_offenses": total, "equivalent_major_offenses": total // 3})
        self.assertEqual(Violation.objects.count(), 9)

    def test_repeated_osa_submission_never_requeues_open_or_offense(self):
        self.scan_ai()
        self.review("YES")
        self.assertEqual(self.review("YES").status_code, 400)
        self.assertEqual(self.review("DENY").status_code, 400)
        self.open()
        self.assertEqual(self.review("NO").status_code, 400)
        self.finish()
        self.assertEqual(self.review("YES").status_code, 400)
        self.event("ENTERED")  # Durable duplicate remains harmless after closing.
        self.assertEqual(Violation.objects.count(), 1)
        self.assertEqual(ViolationEmail.objects.count(), 1)

    def test_pass_still_requires_osa_before_opening(self):
        self.scan_ai(result="PASS")
        self.assertEqual(self.inspection.ai_result, "PASS")
        self.assertEqual(self.review("NO").status_code, 200)
        self.open()
        self.finish()
        self.assert_no_offense()

    def test_open_rejection_does_not_fabricate_success_or_offense(self):
        self.scan_ai()
        self.review("YES")
        self.assertEqual(claim_open("workflow"), self.attempt.pk)
        self.event("OPEN_REJECTED")
        self.attempt.refresh_from_db()
        self.assertFalse(self.attempt.gate_opened)
        self.assertFalse(self.attempt.entered)
        self.assert_no_offense()

    def test_disconnect_after_claim_never_replays_open(self):
        self.scan_ai()
        self.review("YES")
        claim_open("workflow")
        end_session("workflow", "USB write failed; operator assistance required.")
        self.assertIsNone(claim_open("workflow"))
        self.attempt.refresh_from_db()
        self.assertFalse(self.attempt.gate_opened)
        status = self.client.get(f"/api/students/gate/attempts/{self.attempt.pk}/").json()
        self.assertFalse(status["connected"])
        self.assertIn("USB write failed", status["message"])
        self.assert_no_offense()

    def test_offline_review_does_not_save_allow_decision(self):
        self.scan_ai()
        GateController.objects.filter(pk=1).update(connected=False)
        self.assertEqual(self.review("YES").status_code, 409)
        self.inspection.refresh_from_db()
        self.assertEqual(self.inspection.confirmation_status, "PENDING")
        self.assert_no_offense()

    def test_entered_flag_without_acknowledged_opening_is_not_official(self):
        self.scan_ai()
        self.review("YES")
        AccessAttempt.objects.filter(pk=self.attempt.pk).update(entered=True)
        GateCycle.objects.filter(pk=self.attempt.pk).update(outcome="ENTERED")
        self.assertFalse(save_violation(self.inspection.pk))
        self.assert_no_offense()

    def test_denial_after_previous_offense_does_not_change_totals(self):
        self.official()
        self.scan_ai()
        self.review("DENY")
        self.assertEqual(offense_counts(self.student.pk)["total_minor_offenses"], 1)
        self.assertEqual(ViolationEmail.objects.count(), 1)
        self.assertEqual(Violation.objects.count(), 1)

    def test_unconfirmed_historical_report_is_preserved_but_not_counted(self):
        old = ViolationReport.objects.create(student=self.student, violation_type="Unconfirmed")
        self.assertEqual(offense_counts(self.student.pk)["total_minor_offenses"], 0)
        self.assertEqual(self.client.get("/api/students/records/").json()["total"], 0)
        self.official()
        self.assertTrue(ViolationReport.objects.filter(pk=old.pk).exists())
        self.assertEqual(offense_counts(self.student.pk)["total_minor_offenses"], 1)

    def test_incomplete_serial_write_does_not_mark_gate_open(self):
        from unittest.mock import Mock
        from django.core.management.base import CommandError
        from .management.commands.gate_bridge import write_command
        self.scan_ai()
        self.review("YES")
        claim_open("workflow")
        port = Mock()
        port.write.return_value = 1
        with self.assertRaises(CommandError):
            write_command(port, f"OPEN {self.attempt.pk}")
        self.attempt.refresh_from_db()
        self.assertFalse(self.attempt.gate_opened)
        self.assertIsNone(claim_open("workflow"))
        self.assert_no_offense()

    def test_manual_confirm_after_ai_pass_has_explicit_offense_description(self):
        self.scan_ai(result="PASS")
        self.review("YES")
        self.open()
        self.finish()
        self.assertEqual(ViolationReport.objects.get().violation_type, "OSA-confirmed dress-code violation")

    def test_upgrade_cancels_only_unsent_legacy_scan_without_deleting_history(self):
        from importlib import import_module
        from django.apps import apps
        migration = import_module("students.migrations.0013_osa_entry_decisions")
        self.official()
        first = ViolationReport.objects.get().pk
        attempt = AccessAttempt.objects.create(student=self.student)
        cycle = GateCycle.objects.create(attempt=attempt, phase="QUEUED")
        GateController.objects.filter(pk=1).update(active_cycle=cycle)
        migration.cancel_unsent_legacy_cycles(apps, None)
        cycle.refresh_from_db()
        self.assertEqual((cycle.phase, cycle.outcome), ("CLOSED", "CANCELLED"))
        self.assertTrue(AccessAttempt.objects.filter(pk=attempt.pk).exists())
        self.assertTrue(ViolationReport.objects.filter(pk=first).exists())
        self.assertIsNone(GateController.objects.get(pk=1).active_cycle_id)
