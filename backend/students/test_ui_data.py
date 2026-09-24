from django.test import TestCase
from unittest.mock import patch
from .models import Student, AccessAttempt, AIInspection, GateCycle, ViolationReport, ViolationEmail


class ReadOnlyUIDataTests(TestCase):
    def setUp(self):
        self.student = Student.objects.create(student_number="UI-1", full_name="UI Student", email="ui@example.test", college="SOC")
        self.attempt = AccessAttempt.objects.create(student=self.student)
        self.inspection = AIInspection.objects.create(student=self.student, attempt=self.attempt, confirmation_status="CONFIRMED_DENY")
        GateCycle.objects.create(attempt=self.attempt, phase="CLOSED", outcome="DENIED")

    def test_audit_preserves_denial_without_official_offense(self):
        response = self.client.get("/api/students/audit/?outcome=DENIED&student_number=UI-1").json()
        self.assertEqual(response["total"], 1)
        self.assertEqual(response["results"][0]["osa_decision"], "CONFIRMED_DENY")
        self.assertFalse(response["results"][0]["entered"])
        self.assertFalse(ViolationReport.objects.exists())

    def test_read_only_endpoints_reject_post_and_expose_no_credentials(self):
        for endpoint in ("audit", "notifications", "system-status"):
            self.assertEqual(self.client.post(f"/api/students/{endpoint}/").status_code, 405)
        with patch("students.ui_data.bridge_running", return_value=False):
            data = self.client.get("/api/students/system-status/").json()
        self.assertFalse(data["arduino_connected"])
        self.assertEqual(data["denied_today"], 1)
        self.assertNotIn("EMAIL_HOST_PASSWORD", data)
        self.assertNotIn("EMAIL_HOST_USER", data)

    def test_notifications_show_persisted_status_and_derived_counts(self):
        report = ViolationReport.objects.create(student=self.student, violation_type="Knees", confirmed_entry=True)
        notice = ViolationEmail.objects.create(report=report, inspection=self.inspection, status="FAILED", error="TimeoutError")
        row = self.client.get("/api/students/notifications/?status=FAILED").json()["results"][0]
        self.assertEqual(row["id"], notice.pk)
        self.assertEqual(row["status"], "FAILED")
        self.assertEqual(row["total_minor_offenses"], 1)
        notice.refresh_from_db()
        self.assertEqual(notice.status, "FAILED")

    def test_pagination_and_search(self):
        AccessAttempt.objects.bulk_create([AccessAttempt(student=self.student) for _ in range(30)])
        data = self.client.get("/api/students/audit/?page=2").json()
        self.assertEqual(data["total"], 31)
        self.assertEqual(len(data["results"]), 6)
        self.assertEqual(self.client.get("/api/students/audit/?q=missing").json()["total"], 0)
