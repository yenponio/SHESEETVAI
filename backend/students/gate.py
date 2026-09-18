"""Gate operations shared by HTTP scan handling and the local USB bridge.

The bridge is a Django management command on the same PC and uses the ORM.
There is no public API which can assert that a student physically entered.
"""
from contextlib import contextmanager
import psutil

from django.db import transaction
from django.db.models import F
from .models import (
    AccessAttempt, AIInspection, EntryLog, GateController, GateCycle,
    GateEvent, Violation, ViolationReport,
)

CANCELLED_OUTCOMES = ("WALKED_AWAY", "CANCELLED", "UNCERTAIN")
DEVICE_EVENTS = {
    "OPENING", "OPEN_ESTIMATED", "AT_A", "BOTH_DETECTED", "AT_B",
    "ENTERED", "WALKED_AWAY", "PASSAGE_UNCERTAIN", "CANCELLED",
    "CLOSING", "CLOSE_PAUSED", "CLOSED_ESTIMATED", "OPEN_REJECTED",
}


class GateError(Exception):
    def __init__(self, message, code="GATE_BUSY"):
        super().__init__(message)
        self.code = code


def lock_database():
    # SQLite ignores select_for_update. Acquire its write lock before reading
    # mutable gate/violation state; this also locks the singleton on PostgreSQL.
    GateController.objects.filter(pk=1).update(revision=F("revision") + 1)


@contextmanager
def locked_controller():
    with transaction.atomic():
        lock_database()
        yield GateController.objects.get(pk=1)


def bridge_running(controller):
    if not controller.connected or not controller.process_id:
        return False
    try:
        process = psutil.Process(controller.process_id)
        arguments = process.cmdline()
        return process.is_running() and "gate_bridge" in arguments
    except (psutil.Error, OSError):
        return False


def queue_attempt(student):
    with locked_controller() as controller:
        if not controller.enabled:
            return AccessAttempt.objects.create(student=student, gate_opened=True), False
        if not controller.ready or not bridge_running(controller):
            raise GateError("Gate is offline. Please ask the operator for assistance.",
                            "GATE_OFFLINE")
        if controller.active_cycle_id:
            raise GateError("Please wait until the current student's gate cycle is finished.")
        attempt = AccessAttempt.objects.create(student=student, gate_opened=False)
        if attempt.pk > 2147483647:
            raise GateError("Gate attempt number is out of range.", "GATE_FAULT")
        cycle = GateCycle.objects.create(attempt=attempt)
        controller.active_cycle = cycle
        controller.save(update_fields=["active_cycle"])
        return attempt, True


def begin_session(bridge_id, process_id):
    with locked_controller() as controller:
        if bridge_running(controller):
            raise GateError("Another gate bridge is already running.")
        # Restart never replays an uncertain OPEN. The operator has restored
        # the closed reference, and durable old events were replayed first.
        if controller.active_cycle_id:
            previous = GateCycle.objects.get(pk=controller.active_cycle_id)
            if previous.outcome != "ENTERED":
                previous.outcome = "CANCELLED"
            previous.phase = "CLOSED"
            previous.message = "Previous session ended; closed reference restored."
            previous.save()
        controller.enabled = controller.connected = controller.ready = True
        controller.active_cycle = None
        controller.bridge_id = bridge_id
        controller.process_id = process_id
        controller.save()


def end_session(bridge_id, message):
    with locked_controller() as controller:
        if controller.bridge_id != bridge_id:
            return
        controller.connected = controller.ready = False
        controller.save(update_fields=["connected", "ready"])
        if controller.active_cycle_id:
            cycle = GateCycle.objects.get(pk=controller.active_cycle_id)
            # Keep protocol phase/outcome: journaled events may still need replay.
            cycle.message = message[:160]
            cycle.save()


def claim_open(bridge_id):
    with locked_controller() as controller:
        if (controller.bridge_id != bridge_id or not controller.ready or
                not controller.connected or not controller.active_cycle_id):
            return None
        cycle = GateCycle.objects.get(pk=controller.active_cycle_id)
        if cycle.phase != "QUEUED":
            return None
        cycle.phase = "SENT"
        cycle.bridge_id = bridge_id
        cycle.save(update_fields=["phase", "bridge_id"])
        return cycle.pk


def save_violation(inspection_id):
    with locked_controller():
        inspection = AIInspection.objects.select_related("attempt", "student").get(pk=inspection_id)
        if (inspection.confirmation_status != "CONFIRMED" or inspection.recorded or
                not inspection.attempt_id or not inspection.attempt.entered):
            return False
        if GateCycle.objects.filter(
            attempt_id=inspection.attempt_id, outcome__in=CANCELLED_OUTCOMES,
        ).exists():
            return False
        text = ", ".join(inspection.violations)
        for name in inspection.violations:
            Violation.objects.create(student=inspection.student, violation_type=name, status="Unread")
        ViolationReport.objects.create(
            student=inspection.student, violation_type=text,
            confirmed_entry=True, sent_to_osa=True,
        )
        inspection.recorded = True
        inspection.save(update_fields=["recorded"])
        return True


def cancelled_attempt(attempt_id):
    return GateCycle.objects.filter(
        attempt_id=attempt_id, outcome__in=CANCELLED_OUTCOMES,
    ).exists()


def apply_event(bridge_id, attempt_id, event, event_key):
    if event not in DEVICE_EVENTS:
        raise GateError("Unknown hardware event.", "GATE_EVENT_INVALID")
    with locked_controller() as controller:
        previous_event = GateEvent.objects.filter(pk=event_key).first()
        if previous_event:
            if previous_event.cycle_id != attempt_id or previous_event.event != event:
                raise GateError("Event identifier reused with different contents.", "GATE_EVENT_INVALID")
            return
        cycle = GateCycle.objects.select_related("attempt").get(pk=attempt_id)
        if not bridge_id or cycle.bridge_id != bridge_id:
            raise GateError("Event belongs to a different bridge session.", "GATE_EVENT_INVALID")
        # Closed attempts accept only harmless duplicates, never a late entry.
        if cycle.phase == "CLOSED":
            harmless = event == "CLOSED_ESTIMATED" or event == cycle.outcome
            if not harmless:
                raise GateError("Event received after the cycle closed.", "GATE_EVENT_INVALID")
        elif event == "OPEN_REJECTED":
            if cycle.phase != "SENT":
                raise GateError("Opening rejection arrived after movement.", "GATE_EVENT_INVALID")
            cycle.phase, cycle.outcome = "CLOSED", "CANCELLED"
        elif event == "OPENING":
            if cycle.phase not in ("SENT", "OPENING"):
                raise GateError("Unexpected opening event.", "GATE_EVENT_INVALID")
            cycle.phase = "OPENING"
        elif event == "OPEN_ESTIMATED":
            if cycle.phase not in ("OPENING", "OPEN"):
                raise GateError("Opening was not acknowledged.", "GATE_EVENT_INVALID")
            cycle.phase = "OPEN"
            cycle.attempt.gate_opened = True
            cycle.attempt.save(update_fields=["gate_opened"])
        elif event in ("AT_A", "BOTH_DETECTED", "AT_B"):
            if cycle.phase not in ("OPENING", "OPEN"):
                raise GateError("Passage without an active opening.", "GATE_EVENT_INVALID")
        elif event == "PASSAGE_UNCERTAIN":
            if cycle.phase not in ("OPENING", "OPEN") or cycle.outcome != "PENDING":
                raise GateError("Unexpected uncertainty event.", "GATE_EVENT_INVALID")
            cycle.outcome = "UNCERTAIN"
        elif event in ("ENTERED", "WALKED_AWAY", "CANCELLED"):
            if cycle.outcome == event:
                pass  # Duplicate outcome with a new delivery identifier.
            else:
                allowed = cycle.outcome == "PENDING" or (
                    event == "CANCELLED" and cycle.outcome == "UNCERTAIN")
                # FAULT permits replay of an event durably captured before disconnect.
                if cycle.phase not in ("OPEN", "FAULT") or not allowed:
                    raise GateError("Passage outcome conflicts with this attempt.", "GATE_EVENT_INVALID")
                if event == "ENTERED" and not cycle.attempt.gate_opened:
                    raise GateError("Entry without an acknowledged opening.", "GATE_EVENT_INVALID")
                cycle.outcome = event
                if event == "ENTERED":
                    cycle.attempt.entered = True
                    cycle.attempt.save(update_fields=["entered"])
                    EntryLog.objects.get_or_create(attempt=cycle.attempt)
        elif event in ("CLOSING", "CLOSE_PAUSED"):
            if cycle.outcome not in ("ENTERED", "WALKED_AWAY", "CANCELLED"):
                raise GateError("Closing before the attempt was resolved.", "GATE_EVENT_INVALID")
            cycle.phase = "CLOSING"
        elif event == "CLOSED_ESTIMATED":
            if cycle.phase != "CLOSING":
                raise GateError("Closed event without a closing cycle.", "GATE_EVENT_INVALID")
            cycle.phase = "CLOSED"
        cycle.message = event
        cycle.save()
        GateEvent.objects.create(key=event_key, cycle=cycle, event=event)
        if event == "ENTERED":
            for inspection in AIInspection.objects.filter(
                attempt_id=attempt_id, confirmation_status="CONFIRMED", recorded=False,
            ):
                save_violation(inspection.pk)
        if cycle.phase == "CLOSED" and controller.active_cycle_id == attempt_id:
            controller.active_cycle = None
            controller.save(update_fields=["active_cycle"])


def cycle_status(attempt_id):
    cycle = GateCycle.objects.get(pk=attempt_id)
    controller = GateController.objects.get(pk=1)
    return {
        "success": True, "attempt_id": cycle.pk, "phase": cycle.phase,
        "outcome": cycle.outcome, "message": cycle.message,
        "connected": bridge_running(controller),
    }
