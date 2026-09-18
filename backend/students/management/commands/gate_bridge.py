"""Local, single-owner USB bridge for the already-tested BENCH_GATE_V1 sketch."""
import os
import queue
import sys
import threading
import time
import uuid
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from students.gate import (
    GateError, apply_event, begin_session, bridge_running, claim_open, end_session,
)
from students.models import GateController
from students.gate_protocol import EventJournal, LineFramer, parse_event


def replay(journal):
    for seq, session, attempt, event in journal.pending():
        apply_event(session, attempt, event, f"{session}:{seq}")
        journal.acknowledge(seq)


def await_line(port, framer, expected, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        for line in framer.feed(port.read(64)):
            if line == expected:
                return
    raise CommandError(f"No '{expected}' received. Check firmware, baud rate and USB.")


def write_command(port, text):
    payload = (text + "\n").encode("ascii")
    if port.write(payload) != len(payload):
        raise CommandError("Incomplete USB write; command delivery is uncertain.")


class Command(BaseCommand):
    help = "Connect Django to the tested Uno gate over USB; owns the serial port."

    def add_arguments(self, parser):
        parser.add_argument("--port", required=True, help="Arduino port, for example COM4")
        parser.add_argument("--closed-reference", action="store_true",
                            help="Confirm the bench motors currently represent the CLOSED position.")
        parser.add_argument("--journal", default=str(Path(settings.BASE_DIR) / "gate_events.sqlite3"))

    def handle(self, *args, **options):
        if not options["closed_reference"]:
            raise CommandError(
                "Restore the bench motors to their CLOSED reference, then add --closed-reference. "
                "Opening the serial port may reset the Uno."
            )
        try:
            import serial
        except ImportError as error:
            raise CommandError("Install pyserial in backend/venv first: python -m pip install pyserial==3.5") from error
        try:
            controller = GateController.objects.get(pk=1)
        except DatabaseError as error:
            raise CommandError("Run python manage.py migrate before starting the gate bridge.") from error
        if bridge_running(controller):
            raise CommandError("Another bridge is already running. Do not open the port twice.")

        session = uuid.uuid4().hex
        journal = EventJournal(options["journal"])
        stop = threading.Event()
        failures = queue.Queue()
        operator_commands = queue.Queue()
        shared = {"active_attempt": None, "status_seen": time.monotonic()}
        reader = None
        registered = False

        def operator_input():
            for line in sys.stdin:
                command = line.strip().upper()
                if command in ("CLOSE", "STATUS"):
                    operator_commands.put(command)
                elif command:
                    self.stdout.write("Only CLOSE or STATUS is accepted here. Scan an ID to open.")
                if stop.is_set():
                    return

        try:
            with serial.Serial(options["port"], 9600, timeout=0.1, write_timeout=1) as port:
                framer = LineFramer()
                self.stdout.write("Waiting for the Uno. Keep Serial Monitor closed.")
                await_line(port, framer, "READY BENCH_GATE_V1", 8)
                write_command(port, "ARM")
                await_line(port, framer, "ARMED_CLOSED_REFERENCE", 5)

                # Finish durable events from the previous session before reconciling it.
                while journal.pending():
                    replay(journal)
                begin_session(session, os.getpid())
                registered = True
                self.stdout.write(self.style.SUCCESS(
                    "GATE READY. A valid ID scan will open it. "
                    "For an uncertain passage, clear both sensors and type CLOSE here."
                ))

                def read_serial():
                    try:
                        while not stop.is_set():
                            for line in framer.feed(port.read(64)):
                                if not line:
                                    continue
                                if line.startswith("READY"):
                                    raise RuntimeError("Uno reset during operation. Restore closed reference and restart.")
                                if line.startswith("STATUS "):
                                    shared["status_seen"] = time.monotonic()
                                    values = dict(part.split("=", 1) for part in line.split()[1:] if "=" in part)
                                    if values.get("fault") != "0" or values.get("mode") == "0":
                                        raise RuntimeError("Uno reported a fault or lost its closed reference.")
                                    continue
                                event = parse_event(line, shared["active_attempt"])
                                if event:
                                    attempt, name = event
                                    journal.append(session, attempt, name)
                                self.stdout.write(line)
                                if line in ("ERROR UNARMED_OR_BUSY", "ERROR INVALID_ID"):
                                    raise RuntimeError("Gate rejected its active command; inspect and restart.")
                    except Exception as error:
                        failures.put(error)
                        stop.set()

                reader = threading.Thread(target=read_serial, name="gate-usb-reader", daemon=True)
                reader.start()
                threading.Thread(target=operator_input, name="gate-operator", daemon=True).start()
                next_status = time.monotonic()
                shared["status_seen"] = next_status
                while not stop.is_set():
                    # Database contention retries the same durable events, never OPEN.
                    try:
                        replay(journal)
                        if not journal.pending():
                            attempt = claim_open(session)
                            if attempt is not None:
                                shared["active_attempt"] = attempt
                                write_command(port, f"OPEN {attempt}")
                    except DatabaseError:
                        # Keep draining USB in the reader while database writes retry.
                        pass
                    while not operator_commands.empty():
                        write_command(port, operator_commands.get_nowait())
                    now = time.monotonic()
                    if now >= next_status:
                        write_command(port, "STATUS")
                        next_status = now + 1
                    if now - shared["status_seen"] > 6:
                        raise CommandError("USB status stopped responding. No gate closing command was sent.")
                    stop.wait(0.05)
                if not failures.empty():
                    raise CommandError(str(failures.get()))
        except KeyboardInterrupt:
            self.stdout.write("Bridge stopped. The gate was not forced closed.")
        except (serial.SerialException, OSError, ValueError, GateError) as error:
            raise CommandError(str(error)) from error
        finally:
            stop.set()
            if reader:
                reader.join(timeout=0.5)
            if registered:
                try:
                    # Anything not applied remains in the durable journal for restart.
                    replay(journal)
                except Exception as error:
                    self.stderr.write(f"Events remain pending for recovery: {error}")
                try:
                    end_session(session, "USB bridge stopped; operator assistance required.")
                except DatabaseError:
                    self.stderr.write("Could not mark bridge offline; stopped process will be detected.")
