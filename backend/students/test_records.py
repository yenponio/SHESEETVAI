from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.test import TestCase

from .gate import save_violation
from .models import Student, ViolationReport, Violation, AccessAttempt, AIInspection


class RecordsDashboardTests(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            student_number="REPORT-TEST", full_name="Report Test",
            email="report@example.test", college="School of Computing",
        )

    def report(self, text="Dress code"):
        return ViolationReport.objects.create(student=self.student, violation_type=text)

    def assert_totals(self, expected):
        records = self.client.get("/api/students/records/").json()
        dashboard = self.client.get("/api/students/dashboard/").json()
        self.assertEqual(records["total"], expected)
        self.assertEqual(len(records["records"]), expected)
        self.assertEqual(dashboard["total_violations"], expected)
        self.assertEqual(sum(row["violations"] for row in dashboard["college_chart"]), expected)
        self.assertEqual(sum(row["value"] for row in dashboard["compliance_chart"]), Student.objects.count())
        return records, dashboard

    def test_same_source_add_delete_and_school_filter(self):
        first = self.report("Shoulders, Knees")
        self.report("Shoes")
        Violation.objects.create(student=self.student, violation_type="Not a report")
        AccessAttempt.objects.create(student=self.student, has_violation=True, entered=True)
        records, dashboard = self.assert_totals(2)
        self.assertEqual(dashboard["college_chart"], [{"college": "SOC", "violations": 2}])
        self.assertEqual(len({row["id"] for row in records["records"]}), 2)
        self.assertEqual(self.client.get("/api/students/records/soc/").json()["total"], 2)
        self.assertEqual(self.client.get("/api/students/records/sea/").json()["total"], 0)
        first.delete()
        self.assert_totals(1)
        self.report()
        self.assert_totals(2)

    def test_empty(self):
        records, dashboard = self.assert_totals(0)
        self.assertEqual(records["records"], [])
        self.assertEqual(dashboard["college_chart"], [])
        self.assertEqual([row["value"] for row in dashboard["compliance_chart"]], [1, 0])

    def test_manila_date_and_today_boundary(self):
        report = self.report()
        ViolationReport.objects.filter(pk=report.pk).update(
            report_time=datetime(2026, 9, 15, 16, 30, tzinfo=dt_timezone.utc)
        )
        with patch("django.utils.timezone.now", return_value=datetime(2026, 9, 15, 17, tzinfo=dt_timezone.utc)):
            records, dashboard = self.assert_totals(1)
        row = records["records"][0]
        self.assertEqual(row["date"], "2026-09-16")
        self.assertEqual(row["time"], "00:30:00")
        self.assertTrue(row["reportedAt"].endswith("+08:00"))
        self.assertEqual(dashboard["violations_today"], 1)
        self.assertEqual(row["studentNumber"], self.student.student_number)
        self.assertEqual(row["name"], self.student.full_name)
        self.assertEqual(row["violationType"], report.violation_type)

    def test_abbreviations_and_unknown_schools_are_not_lost(self):
        self.student.college = "CCJF"
        self.student.save()
        self.report()
        self.assertEqual(self.client.get("/api/students/records/ccjef/").json()["total"], 1)
        self.assertEqual(self.client.get("/api/students/records/ccjf/").json()["total"], 1)
        self.student.college = "New School"
        self.student.save()
        records, dashboard = self.assert_totals(1)
        self.assertIn("New School", records["schools"])
        self.assertEqual(dashboard["college_chart"][0]["college"], "New School")

    def test_repeat_save_does_not_duplicate_report(self):
        attempt = AccessAttempt.objects.create(student=self.student, entered=True)
        inspection = AIInspection.objects.create(
            student=self.student, attempt=attempt, confirmation_status="CONFIRMED",
            violations=["Shoulders", "Knees"],
        )
        self.assertTrue(save_violation(inspection.pk))
        self.assertFalse(save_violation(inspection.pk))
        self.assertEqual(Violation.objects.count(), 2)
        self.assert_totals(1)

    def test_compliance_counts_students_once_and_status_matches(self):
        other = Student.objects.create(student_number="CLEAR", full_name="Clear Student",
                                       email="clear@example.test", college="SOC")
        AccessAttempt.objects.create(student=self.student, entered=True)
        AccessAttempt.objects.create(student=other, entered=True)
        first = self.report("Shoulders")
        second = self.report("Knees")
        dashboard = self.client.get("/api/students/dashboard/").json()
        self.assertEqual([row["value"] for row in dashboard["compliance_chart"]], [1, 1])
        statuses = {row["studentNumber"]: row["status"] for row in dashboard["recent_logs"]}
        self.assertEqual(statuses[self.student.student_number], "With Violation")
        self.assertEqual(statuses[other.student_number], "No Violation")
        first.delete()
        second.delete()
        dashboard = self.client.get("/api/students/dashboard/").json()
        self.assertEqual([row["value"] for row in dashboard["compliance_chart"]], [2, 0])
        self.assertTrue(all(row["status"] == "No Violation" for row in dashboard["recent_logs"]))

    def test_no_registered_students(self):
        self.student.delete()
        dashboard = self.client.get("/api/students/dashboard/").json()
        self.assertEqual([row["value"] for row in dashboard["compliance_chart"]], [0, 0])

    def test_pending_queue_skips_orphans_and_review_advances(self):
        orphan = AIInspection.objects.create(student=self.student, violations=["Old capture"])
        attempt = AccessAttempt.objects.create(student=self.student)
        current = AIInspection.objects.create(student=self.student, attempt=attempt, violations=["Knees"])
        pending = self.client.get("/api/students/ai-inspection/pending/").json()
        self.assertEqual(pending["inspection"]["id"], current.pk)
        response = self.client.post("/api/students/ai-inspection/review/", {
            "inspection_id": current.pk, "decision": "YES",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.get("/api/students/ai-inspection/pending/").json()["success"])
        orphan.refresh_from_db()
        self.assertEqual(orphan.confirmation_status, "PENDING")
        self.assertFalse(ViolationReport.objects.exists())
