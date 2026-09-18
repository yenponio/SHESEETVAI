# SHESEETVAI USB gate prototype

## What is connected
The existing tested SHESEETVAI_GATE_TEST sketch is used unchanged:
Uno, USB at 9600 baud, TB6600 STEP/DIR on D6/D7 and D8/D9,
HC-SR04 A on D10/D11 and B on D12/D13.
The screenshot supplied during testing shows COM4. Edit START_GATE.cmd if the port changes.

The local Django management command owns USB and uses Django's ORM directly.
React cannot confirm entry or open the serial port. The old confirm-entry HTTP route returns 403.

## Starting the integrated demo
1. Ensure the sensor backgrounds, overlap sequence and motor closed reference are correct.
2. Close Arduino Serial Monitor. Only one application can own COM4.
3. Start/restart Django, the AI camera service and the React frontend using your usual commands.
4. Double-click START_GATE.cmd in the project root. Read the closed-reference instruction and continue.
5. Wait for GATE READY in that window.
6. Tap a valid ID. OPEN is sent automatically with that scan's attempt ID.

Equivalent bridge command from backend:
    venv\Scripts\python.exe manage.py gate_bridge --port COM4 --closed-reference

The schema is installed using:
    venv\Scripts\python.exe manage.py migrate

The added USB dependency is:
    venv\Scripts\python.exe -m pip install pyserial==3.5

Starting the bridge enables hardware mode in the database. After that, scans are rejected while
the bridge is stopped/offline; they are not silently treated as successful hardware entries.
Before the bridge is first started, the existing software-only scan flow remains available.

## Behavior
- Valid ID queues one opening. It does not wait for OSA to permit entry.
- AI and OSA keep their existing review workflow.
- ENTERED for the exact active attempt creates its entry log once.
- Final violations require BOTH actual entry AND OSA confirmation, in either order.
- WALKED_AWAY or CANCELLED never creates an entry log or final violation.
- Pending scan/inspection audit data may remain; cancelled inspections are excluded from the
  pending OSA queue, and late AI/review requests cannot turn them into final violations.
- A second scan cannot replace an active gate cycle.
- The kiosk waits for gate closure and the relevant inspection result instead of resetting
  after its old 2.5-second result timer in hardware mode.
- Gate closing still follows the tested firmware's sensor logic; there is no automatic
  closing timeout. Existing application date fields were preserved; no new calendar
  timestamp fields were added.

## Uncertain passage / restart
If PASSAGE_UNCERTAIN is displayed:
1. Clear both sensor zones while retaining valid backgrounds.
2. Type CLOSE in the bridge terminal and press Enter.
3. If blocked, fix sensor clearance and try again; do not reset the position blindly.

Do not open Arduino Serial Monitor while the bridge is running.
Do not type OPEN in the bridge terminal: a valid ID scan authorizes the command.
CLOSE and STATUS are the only operator commands accepted.

A USB reset/disconnect stops the bridge; it never automatically replays an opening.
Restore the known closed reference before restarting. On restart, durable events are processed
first and unresolved old attempts are cancelled. An entry already recorded is not erased.
The local backend/gate_events.sqlite3 journal must remain with this database for event recovery.
Communication deadlines only detect a lost connection; they do not close the gate.

## Verification
Automated tests use Django's separate test database and cover exact-attempt association,
entry/OSA ordering, walk-away cancellation, duplicate events, restart handling, serial framing,
and event-journal persistence. Frontend tests verify when the kiosk may release a student.
These checks do not substitute for the integrated physical ID/AI/sensor demonstration.

After setup, test:
- Invalid ID: no motor movement.
- Valid ID, remain at either sensor: gate stays open.
- A only -> both -> B only -> clear: one entry log, then close.
- A only -> retreat -> clear: close without an entry/final violation.
- OSA-confirmed violation + entry: one final violation.
- OSA-confirmed violation + retreat: no final violation.
- Another tap during an active cycle: rejected.
- Unplug USB: no invented entry; restore closed reference before restart.

Motor positions are estimated, and this is a bench demonstration. A full-size gate still needs
verified passage coverage and separate position/obstruction protection.

## Implementation references
- SQLite transaction limitations: https://docs.djangoproject.com/en/6.0/ref/databases/#sqlite-notes
- pySerial port and timeout behavior: https://pyserial.readthedocs.io/en/latest/pyserial_api.html
