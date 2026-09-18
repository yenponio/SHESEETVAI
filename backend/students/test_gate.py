import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, SimpleTestCase
from students.models import (
    Student, AccessAttempt, AIInspection, EntryLog, Violation, ViolationReport,
    GateController, GateCycle, GateEvent,
)
from students.gate import (
    GateError, apply_event, begin_session, claim_open, end_session, queue_attempt,
)
from students.gate_protocol import EventJournal, LineFramer, parse_event


class GateIntegrationTests(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            student_number="TEST-1", barcode="123456", full_name="Gate Test",
            email="gate@example.test", college="Test",
        )
        GateController.objects.filter(pk=1).update(
            enabled=True, connected=True, ready=True, bridge_id="session", process_id=123,
        )
        self.running = patch("students.gate.bridge_running", return_value=True)
        self.running.start()
        self.addCleanup(self.running.stop)
        self.sequence = 0

    def scan(self):
        return self.client.post("/api/students/scan/", {"barcode": "123456"})

    def cycle(self):
        response = self.scan()
        self.assertEqual(response.status_code, 200, response.content)
        self.attempt = AccessAttempt.objects.get(pk=response.json()["attempt_id"])
        return self.attempt

    def event(self, name, session="session", key=None):
        self.sequence += 1
        apply_event(session, self.attempt.pk, name, key or f"event-{self.sequence}")

    def opened(self):
        self.cycle()
        self.assertEqual(claim_open("session"), self.attempt.pk)
        self.event("OPENING")
        self.event("OPEN_ESTIMATED")

    def inspection(self):
        response = self.client.post("/api/students/ai-result/", {
            "student_number": self.student.student_number,
            "attempt_id": self.attempt.pk,
            "status": "VIOLATION",
            "violations": ["Test dress code"],
        }, content_type="application/json")
        self.assertEqual(response.status_code, 201, response.content)
        return AIInspection.objects.get(pk=response.json()["inspection_id"])

    def review(self, inspection):
        return self.client.post("/api/students/ai-inspection/review/", {
            "inspection_id": inspection.pk, "decision": "YES",
        })

    def close(self):
        self.event("CLOSING")
        self.event("CLOSED_ESTIMATED")

    def test_valid_scan_queues_without_fabricating_open_or_entry(self):
        self.cycle()
        self.assertFalse(self.attempt.gate_opened)
        self.assertFalse(self.attempt.entered)
        self.assertEqual(self.attempt.gate_cycle.phase, "QUEUED")
        self.assertEqual(EntryLog.objects.count(), 0)

    def test_invalid_id_does_not_queue(self):
        response = self.client.post("/api/students/scan/", {"barcode": "000"})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(GateCycle.objects.exists())

    def test_second_scan_cannot_replace_active_student(self):
        self.cycle()
        self.assertEqual(self.scan().status_code, 409)
        self.assertEqual(AccessAttempt.objects.count(), 1)

    def test_offline_gate_rejects_scan(self):
        with patch("students.gate.bridge_running", return_value=False):
            self.assertEqual(self.scan().status_code, 409)
        self.assertFalse(AccessAttempt.objects.exists())

    def test_open_command_is_claimed_only_once(self):
        self.cycle()
        self.assertEqual(claim_open("session"), self.attempt.pk)
        self.assertIsNone(claim_open("session"))
        self.assertIsNone(claim_open("different"))

    def test_open_without_passage_has_no_record(self):
        self.opened()
        self.assertFalse(EntryLog.objects.exists())
        self.assertFalse(Violation.objects.exists())

    def test_entry_creates_one_log_and_releases_only_after_close(self):
        self.opened()
        self.event("ENTERED")
        self.assertEqual(EntryLog.objects.count(), 1)
        self.assertEqual(self.scan().status_code, 409)
        self.close()
        self.assertIsNone(GateController.objects.get(pk=1).active_cycle_id)

    def test_confirmed_violation_waits_for_entry(self):
        self.opened()
        inspection = self.inspection()
        self.assertEqual(self.review(inspection).status_code, 200)
        self.assertFalse(Violation.objects.exists())
        self.event("ENTERED")
        self.assertEqual(Violation.objects.count(), 1)
        self.assertEqual(ViolationReport.objects.count(), 1)

    def test_review_after_entry_saves_once(self):
        self.opened()
        inspection = self.inspection()
        self.event("ENTERED")
        self.assertFalse(Violation.objects.exists())
        self.assertEqual(self.review(inspection).status_code, 200)
        self.assertEqual(self.review(inspection).status_code, 400)
        self.assertEqual(Violation.objects.count(), 1)

    def test_unconfirmed_violation_flag_does_not_create_report(self):
        self.opened()
        self.attempt.has_violation = True
        self.attempt.violation_type = "Unreviewed"
        self.attempt.save(update_fields=["has_violation", "violation_type"])
        self.event("ENTERED")
        self.assertFalse(ViolationReport.objects.exists())
        self.assertFalse(Violation.objects.exists())

    def test_walkaway_never_records_confirmed_violation(self):
        self.opened()
        inspection = self.inspection()
        self.review(inspection)
        self.event("WALKED_AWAY")
        self.close()
        self.assertFalse(EntryLog.objects.exists())
        self.assertFalse(Violation.objects.exists())
        with self.assertRaises(GateError):
            self.event("ENTERED")

    def test_late_ai_is_ignored_for_cancelled_attempt(self):
        self.opened()
        self.event("WALKED_AWAY")
        response = self.client.post("/api/students/ai-result/", {
            "student_number": self.student.student_number,
            "attempt_id": self.attempt.pk, "status": "VIOLATION",
            "violations": ["Test"],
        }, content_type="application/json")
        self.assertTrue(response.json()["ignored"])
        self.assertFalse(AIInspection.objects.exists())

    def test_cancelled_inspection_disappears_from_review_queue(self):
        self.opened()
        inspection = self.inspection()
        self.event("WALKED_AWAY")
        self.assertEqual(self.review(inspection).status_code, 409)
        response = self.client.get("/api/students/ai-inspection/pending/")
        self.assertFalse(response.json()["success"])

    def test_ai_never_falls_back_to_latest_scan(self):
        self.cycle()
        for attempt_id in (None, "bad", self.attempt.pk + 999, True):
            response = self.client.post("/api/students/ai-result/", {
                "student_number": self.student.student_number,
                "attempt_id": attempt_id, "status": "PASS",
            }, content_type="application/json")
            self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(AccessAttempt.objects.count(), 1)

    def test_browser_cannot_confirm_entry(self):
        self.opened()
        response = self.client.post("/api/students/confirm-entry/", {
            "student_number": self.student.student_number,
            "attempt_id": self.attempt.pk,
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(EntryLog.objects.exists())

    def test_duplicate_entry_delivery_does_not_duplicate_records(self):
        self.opened()
        self.review(self.inspection())
        self.event("ENTERED", key="stable-delivery")
        self.event("ENTERED", key="stable-delivery")
        self.event("ENTERED")
        self.assertEqual(EntryLog.objects.count(), 1)
        self.assertEqual(Violation.objects.count(), 1)
        self.assertEqual(ViolationReport.objects.count(), 1)

    def test_event_id_cannot_be_reused_for_different_event(self):
        self.opened()
        self.event("ENTERED", key="same")
        with self.assertRaises(GateError):
            self.event("WALKED_AWAY", key="same")

    def test_wrong_session_is_rejected(self):
        self.opened()
        with self.assertRaises(GateError):
            self.event("ENTERED", session="other")
        self.assertFalse(EntryLog.objects.exists())

    def test_entry_before_opening_is_rejected(self):
        self.cycle()
        claim_open("session")
        with self.assertRaises(GateError):
            self.event("ENTERED")
        self.assertFalse(EntryLog.objects.exists())

    def test_uncertain_passage_requires_cancel_and_never_enters(self):
        self.opened()
        self.event("PASSAGE_UNCERTAIN")
        with self.assertRaises(GateError):
            self.event("ENTERED")
        self.event("CANCELLED")
        self.close()
        self.assertFalse(EntryLog.objects.exists())

    def test_rejected_open_releases_without_entry(self):
        self.cycle()
        claim_open("session")
        self.event("OPEN_REJECTED")
        self.assertEqual(self.attempt.gate_cycle.outcome, "CANCELLED")
        self.assertIsNone(GateController.objects.get(pk=1).active_cycle_id)

    def test_close_pause_does_not_release_next_student(self):
        self.opened()
        self.event("ENTERED")
        self.event("CLOSING")
        self.event("CLOSE_PAUSED")
        self.assertEqual(self.scan().status_code, 409)
        self.event("CLOSING")
        self.event("CLOSED_ESTIMATED")
        self.assertIsNone(GateController.objects.get(pk=1).active_cycle_id)

    def test_restart_cancels_uncertain_old_open_without_replay(self):
        self.cycle()
        claim_open("session")
        with patch("students.gate.bridge_running", return_value=False):
            begin_session("new", 456)
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.gate_cycle.outcome, "CANCELLED")
        self.assertIsNone(claim_open("new"))
        self.assertFalse(EntryLog.objects.exists())

    def test_journaled_events_can_replay_after_disconnect(self):
        self.opened()
        end_session("session", "Disconnected")
        self.event("ENTERED")
        self.close()
        self.assertEqual(EntryLog.objects.count(), 1)

    def test_existing_software_mode_is_preserved_before_bridge_start(self):
        GateController.objects.filter(pk=1).update(enabled=False)
        response = self.scan()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["hardware_gate"])
        self.assertFalse(GateCycle.objects.exists())

    def test_status_matches_exact_attempt(self):
        self.opened()
        response = self.client.get(f"/api/students/gate/attempts/{self.attempt.pk}/")
        self.assertEqual(response.json()["attempt_id"], self.attempt.pk)
        self.assertEqual(response.json()["phase"], "OPEN")
        self.assertNotIn("timestamp", response.json())


class GateProtocolTests(SimpleTestCase):
    def test_partial_and_multiple_lines_are_preserved(self):
        framer = LineFramer()
        self.assertEqual(framer.feed(b"ENTER"), [])
        self.assertEqual(framer.feed(b"ED 42\r\nCLOSING 42\nPART"),
                         ["ENTERED 42", "CLOSING 42"])
        self.assertEqual(framer.feed(b"IAL\n"), ["PARTIAL"])

    def test_oversized_serial_line_is_rejected(self):
        with self.assertRaises(ValueError):
            LineFramer(limit=4).feed(b"12345")

    def test_event_parser_rejects_bad_ids(self):
        for line in ("ENTERED", "ENTERED 0", "ENTERED -1", "ENTERED 2147483648", "ENTERED 1 extra"):
            with self.assertRaises(ValueError):
                parse_event(line)
        self.assertEqual(parse_event("ENTERED 42"), (42, "ENTERED"))
        self.assertIsNone(parse_event("STATUS mode=1 fault=0"))

    def test_open_rejection_is_bound_to_active_command(self):
        self.assertEqual(parse_event("ERROR SENSOR_UNKNOWN", 42), (42, "OPEN_REJECTED"))
        with self.assertRaises(ValueError):
            parse_event("ERROR SENSOR_UNKNOWN")

    def test_event_journal_survives_reopening_and_acknowledges_exact_row(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.sqlite3"
            first = EventJournal(path)
            seq = first.append("bridge", 42, "ENTERED")
            reopened = EventJournal(path)
            self.assertEqual(reopened.pending(), [(seq, "bridge", 42, "ENTERED")])
            reopened.acknowledge(seq)
            self.assertEqual(first.pending(), [])


class GateBridgeCommandTests(TestCase):
    def run_bridge_scenario(self, outcome):
        import io
        import os
        import queue
        from django.core.management import call_command

        student = Student.objects.create(
            student_number="BRIDGE-1", barcode="999888", full_name="Bridge Test",
            email="bridge@example.test", college="Test",
        )
        test_case = self

        class FakeSerial:
            def __init__(self):
                self.chunks = queue.Queue()
                self.chunks.put(b"READY BENCH_GATE_V1\n")
                self.commands = []
                self.attempt_id = None
                self.status_count = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, amount):
                try:
                    return self.chunks.get(timeout=0.02)
                except queue.Empty:
                    return b""

            def write(self, payload):
                command = payload.decode("ascii").strip()
                self.commands.append(command)
                if command == "ARM":
                    self.chunks.put(b"ARMED_CLOSED_REFERENCE\n")
                elif command == "STATUS":
                    self.status_count += 1
                    if self.status_count > 4:
                        raise AssertionError("Bridge failed to finish the simulated passage")
                    if self.attempt_id is None:
                        response = test_case.client.post("/api/students/scan/", {"barcode": student.barcode})
                        test_case.assertEqual(response.status_code, 200, response.content)
                        self.attempt_id = response.json()["attempt_id"]
                        response = test_case.client.post("/api/students/ai-result/", {
                            "student_number": student.student_number, "attempt_id": self.attempt_id,
                            "status": "VIOLATION", "violations": ["Test violation"],
                        }, content_type="application/json")
                        test_case.assertEqual(response.status_code, 201, response.content)
                        review = test_case.client.post("/api/students/ai-inspection/review/", {
                            "inspection_id": response.json()["inspection_id"], "decision": "YES",
                        })
                        test_case.assertEqual(review.status_code, 200)
                    elif GateCycle.objects.get(pk=self.attempt_id).phase == "CLOSED":
                        raise KeyboardInterrupt
                    self.chunks.put(b"STATUS mode=1 path=0 A=1 B=1 position=0 fault=0\n")
                elif command.startswith("OPEN "):
                    attempt = int(command.split()[1])
                    test_case.assertEqual(attempt, self.attempt_id)
                    events = ["OPENING", "OPEN_ESTIMATED", outcome, "CLOSING", "CLOSED_ESTIMATED"]
                    self.chunks.put("".join(f"{event} {attempt}\n" for event in events).encode("ascii"))
                return len(payload)

        serial_port = FakeSerial()
        with tempfile.TemporaryDirectory() as directory:
            with patch("serial.Serial", return_value=serial_port), \
                 patch("students.gate.bridge_running", side_effect=lambda c: c.connected and c.process_id == os.getpid()), \
                 patch("students.management.commands.gate_bridge.bridge_running", return_value=False), \
                 patch("sys.stdin", io.StringIO("")):
                call_command(
                    "gate_bridge", port="SIMULATED", closed_reference=True,
                    journal=str(Path(directory) / "events.sqlite3"),
                    stdout=io.StringIO(), stderr=io.StringIO(),
                )
        self.assertEqual(len([c for c in serial_port.commands if c.startswith("OPEN ")]), 1)
        self.assertFalse(GateController.objects.get(pk=1).connected)
        return GateCycle.objects.get(pk=serial_port.attempt_id)

    def test_valid_id_serial_entry_and_osa_create_one_final_record(self):
        cycle = self.run_bridge_scenario("ENTERED")
        self.assertEqual(cycle.outcome, "ENTERED")
        self.assertEqual(EntryLog.objects.count(), 1)
        self.assertEqual(Violation.objects.count(), 1)
        self.assertEqual(ViolationReport.objects.count(), 1)

    def test_valid_id_serial_retreat_creates_no_entry_or_violation(self):
        cycle = self.run_bridge_scenario("WALKED_AWAY")
        self.assertEqual(cycle.outcome, "WALKED_AWAY")
        self.assertFalse(EntryLog.objects.exists())
        self.assertFalse(Violation.objects.exists())
        self.assertFalse(ViolationReport.objects.exists())
