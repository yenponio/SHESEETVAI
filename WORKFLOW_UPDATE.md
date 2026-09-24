# SHESEETVAI adviser workflow implementation report

Implemented 23 September 2026 in the existing project. Starting checkpoint:
`6b782dd`. Changes have not been committed or pushed. No Arduino sketch or pin
assignment was changed. No physical OPEN command or live email was sent during verification.

## 1. Existing architecture inspected before editing

| Concern | Actual implementation |
|---|---|
| Student scan | `StudentPage.jsx` keyboard barcode handler -> POST `/api/students/scan/` -> `BarcodeScanView` -> `gate.queue_attempt` |
| AI activation | StudentPage `displayStudent` / `startCamera` automatically POST `/start-camera` with student number and exact attempt ID; the MJPEG stream drives `DressCodeInspection.process_frame` |
| AI result | `ai/camera_server.py` sends result and screenshot to POST `/api/students/ai-result/`; `receive_ai_result` binds the exact student/attempt |
| Evidence capture/storage | `ai/camera_integration.py` saves the evidence frame; camera server uploads it; `AIInspection.screenshot` uses Django storage under `ai_inspections/` in MEDIA_ROOT |
| OSA queue/review | GET `/api/students/ai-inspection/pending/`, POST `/api/students/ai-inspection/review/`, existing `ConfirmationPage.jsx` |
| Gate opening | `gate_bridge` claims a gate cycle and sends `OPEN <attempt_id>` through pyserial at 9600 baud |
| Uno firmware | `D:/CODING/SHESEETVAI_GATE_TEST/SHESEETVAI_GATE_TEST.ino` plus `PassageLogic.h`, protocol `BENCH_GATE_V1` |
| Entry sensor | Two HC-SR04 sensors; outside A -> overlap -> inside B -> clear -> ENTERED event |
| entered flag | Local bridge `gate.apply_event`; browser POST `/confirm-entry/` remains forbidden with HTTP 403 |
| Final offense | `gate.save_violation` creates Violation, ViolationReport and ViolationEmail transactionally |
| Daily rule | Official report lookup within aware midnight-to-midnight bounds in Django's configured timezone |
| SMTP | `students/notifications.py`, `send_violation_emails` worker, existing environment settings and START_EMAIL.cmd |
| Records/evidence | `records.violation_records`, `ViolationTable`, `ViolationEvidenceModal`; evidence comes from report.inspection.screenshot |
| Dashboard | `dashboard_data` consumes the shared Records source |
| Existing counts | No stored minor/major counters. Reports already represented one offense; old Violation rows represented individual clothing types |

## 2. Changed files

- `SMTP_SETUP.md`: current workflow, official totals and email behavior.
- `backend/students/models.py`: allow/deny status choices and waiting-for-OSA default.
- `backend/students/gate.py`: scan reservation, OSA-authorized claim, strict finalization guards, one Violation per offense, official daily lookup and status payload.
- `backend/students/views.py`: PASS and VIOLATION both await OSA; three atomic decisions; no review-time offense or fabricated gate opening.
- `backend/students/management/commands/gate_bridge.py`: updated operator messages, acknowledgement timeout and failure details.
- `backend/students/notifications.py`: minor and major equivalents in email.
- `backend/students/records.py`: confirmed-entry history only, derived totals and existing evidence links.
- `backend/students/serializers.py`: derived offense_counts in Student API.
- `backend/students/test_gate.py`: existing protocol/bridge tests follow OSA-first ordering.
- `backend/students/test_notifications.py`: new state and one-row offense fixtures; existing failure/concurrency/mail coverage retained.
- `backend/students/test_evidence.py`: acknowledged sensor-entry fixtures and existing evidence coverage.
- `backend/students/test_records.py`: official-only records and new review ordering.
- `frontend/src/pages/ConfirmationPage.jsx`: student details, AI result, three buttons, processing lock and asynchronous gate status.
- `frontend/src/pages/StudentPage.jsx`: PASS waits for OSA, denial handling, backend decision polling across browsers.
- `frontend/src/hooks/useGateCycle.js`: pending/denied/offline messages and denied-cycle completion.
- `frontend/src/hooks/useGateCycle.test.js`: pending/denied/offline UI behavior.
- `frontend/src/components/ViolationEvidenceModal.jsx`: current minor and equivalent-major totals alongside evidence.
- `frontend/src/styles/ConfirmationPage.css`: three readable buttons and danger styling for deny.

## 3. New files

- `backend/students/offenses.py`: shared official offense-count calculation.
- `backend/students/migrations/0013_osa_entry_decisions.py`: additive workflow migration.
- `backend/students/test_workflow.py`: HTTP/bridge-event end-to-end regression suite.
- `WORKFLOW_UPDATE.md`: this report, upgrade procedure and manual acceptance tests.

## 4. Models and migration

`AIInspection.confirmation_status` adds CONFIRMED_ALLOW and CONFIRMED_DENY.
PENDING and REJECTED remain. Historical CONFIRMED values are preserved and are
not silently treated as a fresh authorization to open. The field remains length 20.

`GateCycle.phase` now defaults to WAITING_OSA instead of QUEUED. DENIED is a
terminal outcome in the existing outcome field. No new model, counter field,
removed field, database reset, or history deletion was introduced.

Migration 0013 also cancels old unsent QUEUED scans and releases their controller
reservation. Those attempts remain stored. It does not change active movement
or historical offenses. Apply upgrades with the bridge stopped and no active
passage; restart using the existing closed-reference procedure.

## 5. Exact migration and startup commands

The migration has already been applied successfully to this local database.
For another checkout, in PowerShell:

```powershell
Set-Location 'D:\CODING\SHESEETVAI-clean\backend'
.\venv\Scripts\python.exe -B manage.py migrate --noinput
.\venv\Scripts\python.exe -B manage.py check
```

No further makemigrations command is required. Restart Django and the email
worker to load the code. Start the camera/frontend as usual. Start the Uno bridge
with the existing START_GATE.cmd, or from backend after restoring CLOSED:

```powershell
.\venv\Scripts\python.exe manage.py gate_bridge --port COM4 --closed-reference
.\venv\Scripts\python.exe manage.py send_violation_emails --watch
```

Run those two long-running commands in separate terminals. COM4 is the existing
launcher value, not an auto-detected new port. Keep Arduino Serial Monitor closed.
No sketch upload is needed.

## 6. Old versus new workflow

Previously a valid scan queued OPEN immediately; OSA had two decisions and a
late YES could finalize an already-entered student. AI PASS bypassed OSA review.
Disabled hardware could fabricate gate_opened=True.

Now: scan -> exact AccessAttempt and WAITING_OSA cycle -> automatic AI capture
-> PENDING AIInspection (including PASS) -> OSA decision -> either denied/closed,
or queued OPEN -> Uno acknowledgement -> HC-SR04 ENTERED -> official offense
only for confirmed-allow and only once per local day -> committed email queue.
There is no software-mode gate-success shortcut.

## 7. Exact button behavior

| Button | Inspection status | Gate | Official offense/email |
|---|---|---|---|
| YES - Confirm Violation and Allow Entry | CONFIRMED_ALLOW | Queue OPEN once; wait for acknowledgement | Only after actual ENTERED and no offense that day |
| NO - No Violation | REJECTED | Queue OPEN once; wait for acknowledgement | Never; normal entry log after sensor passage |
| Confirm Violation and Deny Entry | CONFIRMED_DENY | Keep closed; terminal DENIED cycle | Never |

YES sets has_violation=True. NO sets it False. DENY retains the OSA finding in
attempt/inspection audit state but leaves gate_opened=False and entered=False.
All buttons are disabled during submission, with a synchronous ref guard against
rapid duplicate clicks. A manual YES after AI PASS uses the explicit description
OSA-confirmed dress-code violation, without claiming an AI-detected clothing type.

## 8. Uno OPEN location and preserved hardware

`backend/students/management/commands/gate_bridge.py` sends
`write_command(port, f"OPEN {attempt}")` only after `gate.claim_open` atomically
claims a QUEUED cycle with an allowed OSA status. The attempt ID is required by
the working protocol; it was not replaced with an uncorrelated plain OPEN.

Preserved: Uno, 9600 baud, ARM handshake, CLOSE/STATUS commands, durable event
journal, existing restart handling and no automatic-close timeout. Pins remain
STEP/DIR 6/7 and 8/9; sensor TRIG 10/12, ECHO 11/13. Motor travel remains 1600 steps.

## 9. Opening failure

Review returns HTTP 409 and keeps PENDING if the gate is unavailable before an
allow decision. Successful review means authorization queued, not gate opened.
A short/failed serial write stops the bridge; OPEN is never automatically replayed.
Only OPEN_ESTIMATED marks gate_opened=True. Missing acknowledgement after 15
seconds stops the bridge with a useful error, without issuing CLOSE or another
OPEN. Explicit OPEN_REJECTED closes/cancels the cycle and never marks opening.

The existing status endpoint exposes connection, phase, message, gate_opened,
entered and confirmation_status. Both OSA and student screens poll it. Physical
position is still firmware-estimated, as in the existing hardware (no limit switches).

## 10. Sensor-confirmed entry

The sketch emits ENTERED for the existing A -> both -> B -> clear sequence.
The journaled event is associated with the exact attempt and bridge session.
`apply_event` validates the state, requires acknowledged opening, sets entered,
creates one EntryLog and invokes finalization within the same transaction.
OPEN itself never asserts entry. Walkaway, cancellation and uncertainty never
create an offense. If no passage begins, the firmware has no automatic timeout;
the existing operator CLOSE procedure cancels safely once sensors are clear.

## 11. Exact official offense conditions

All must hold in the serialized transaction:

1. Inspection is CONFIRMED_ALLOW and not already finalized.
2. Inspection and AccessAttempt belong to the same student.
3. Attempt exists, gate_opened=True and entered=True.
4. Its matching GateCycle outcome is ENTERED.
5. No confirmed-entry official report exists for that student in today's configured local-day bounds.

Then create one Violation containing all types, one confirmed-entry ViolationReport,
and one ViolationEmail linked to the report/inspection. Set recorded=True. Any
failure rolls these database writes back together. OSA review never calls finalization.

## 12. Daily duplicate prevention

The existing singleton controller write lock serializes writers on SQLite and
PostgreSQL. The query uses Django's default timezone, localdate and aware local
midnight bounds. Violation type is irrelevant. A skipped duplicate marks its
inspection finalized, preventing a replay the next day. Original evidence is
never replaced. The later attempt still scans, reviews, opens and logs entry.
The next local calendar day can create one new official offense.

## 13. Minor totals and historical safety

`offense_counts(student_id)` counts `ViolationReport` rows with confirmed_entry=True.
Each such report is one minor. This is the existing one-report-per-offense history;
counting legacy per-type Violation rows would overcount multi-type detections.
New finalizations also create exactly one Violation row per offense.

Pre-upgrade database inspection found 20 report rows, 13 marked confirmed entry,
and 44 legacy Violation rows. All remain stored. The 7 unconfirmed reports are
excluded from official Records, Dashboard and offense totals rather than deleted
or promoted without evidence. Existing confirmed historical reports remain official.

## 14. Major equivalents

`equivalent_major_offenses = total_minor_offenses // 3`. No subtraction, reset,
or separate major record. Examples: 3 -> 1, 5 -> 1, 6 -> 2, 9 -> 3. Totals are
returned in Student API and Records API, displayed in Records evidence details,
and included in email. They are derived rather than manually incremented.

## 15. SMTP timing and failures

One queue row is created in the offense transaction. The separate existing worker
reads only committed rows, claims PENDING -> SENDING atomically, and sends the
existing subject, student, violation, local time, current totals and exact evidence.
Totals in email are the current official totals at delivery time. No live recipient
was contacted during tests. Environment variable configuration remains unchanged.

SMTP failure retains the offense and entry, logs a sanitized failure and marks
FAILED. Missing/invalid email skips delivery. Missing evidence permits an email
without attachment. Missing credentials leaves mail pending. Failed/uncertain
SMTP deliveries are not automatically retried, preserving existing duplicate
protection. No passwords were requested, printed or committed.

## 16. Why denial is not an offense

DENY never queues opening, never sets entered and never calls finalization.
The status guard also explicitly excludes it. Only AccessAttempt/AIInspection/
GateCycle audit state remains; no separate denied-entry official violation exists.
It contributes nothing to Records, counts or normal offense email.

## 17. Evidence relationship

The exact AccessAttempt is linked to AIInspection. Its screenshot is displayed
on OSA review. The final Violation and ViolationReport both reference that same
inspection. Records resolves report.inspection.screenshot; the email service
prefers the same canonical report link and reads its Django storage bytes.
No latest-photo guessing, ID-photo substitution or same-day evidence overwrite.

## 18. Duplicate-action protection

The OSA transaction takes the controller write lock, checks PENDING and the active
WAITING_OSA cycle, and transitions once. Repeated reviews return HTTP 400 without
state changes. `claim_open` moves QUEUED -> SENT once. Durable GateEvent keys,
one-to-one EntryLog/queue links, recorded flag and the daily guard prevent repeated
sensor delivery from duplicating logs, offenses or mail. Concurrent finalization
and mail-claim tests remain covered.

## 19. Exact physical end-to-end acceptance steps

Use a designated test student with a controlled email address and no official
report today for the first YES test. Use the existing test hardware setup; do not
change pins or reflash. Start backend, frontend, camera, gate bridge and mail worker.
Open StudentPage and OSA ConfirmationPage. The currently configured detection
zones must overlap. Stand outside at sensor A, as required by the working sketch.

**YES / allow**

1. Scan the registered barcode. Verify student details load and AI starts automatically; gate stays closed.
2. Complete an AI violation capture. Verify matching student, suspected types, result and evidence on OSA; gate still closed and no offense/email yet.
3. Click YES - Confirm Violation and Allow Entry once. Verify CONFIRMED_ALLOW and one OPEN with that attempt ID. Wait for OPEN_ESTIMATED before passing.
4. Verify opening alone has not created an offense. Walk A -> both -> B -> clear.
5. Verify ENTERED, one EntryLog, one official report/Violation, matching Records image, minor total +1 and one queued/delivered email with the same image.
6. Repeat with the same student that day. Review/OPEN/entry still work, EntryLog grows, official count/email count do not, and first evidence remains.
7. Repeat on the next local day to verify a new offense/email. Do not change the production system clock for this test; the automated suite simulates midnight.
8. For walkaway, run YES on a fresh attempt, then retreat from A back outside without crossing. Verify WALKED_AWAY and no added offense/email. If the passage never starts, clear both sensors and use the existing operator CLOSE command; no auto-close timeout was added.

**NO / no violation**

1. Scan and complete AI inspection; verify the gate stays closed through both steps.
2. Click NO - No Violation. Verify REJECTED and one OPEN for the attempt.
3. Wait for OPEN_ESTIMATED, then traverse A -> both -> B -> clear.
4. Verify entered=True, has_violation=False, one normal EntryLog and no new offense/email/count increase. Rejected inspection remains auditable.

**Confirm / deny**

1. Scan and complete AI inspection; verify the evidence belongs to the student and the gate stays closed.
2. Click Confirm Violation and Deny Entry. Verify CONFIRMED_DENY and a CLOSED/DENIED cycle.
3. Verify no OPEN was sent, gate_opened=False, entered=False, no EntryLog and no new official record/email/count increase.
4. Verify the kiosk can process the next scan. A repeated request must not issue a command or change the decision.

For all decisions, rapid duplicate clicks are disabled. For a deliberate test API
retry, re-submit the same inspection ID; expect HTTP 400 and no additional action.
Disconnect testing must use the established safe bench procedure; verify status
reports unavailable and no falsely successful opening. Restore the closed reference
before restarting the bridge. SMTP outage must not remove the saved offense.

## 20. Validation, assumptions and limits

Automated coverage includes all 14 requested cases: first YES entry, walkaway,
NO normal entry, DENY, daily duplicates and next day, totals at 3/5/6, denial totals,
SMTP failure, exact evidence and repeated review. Additional coverage includes
PASS review, failed writes, offline review, forged entered flag, legacy history,
upgrade cancellation, concurrent finalization, durable journal replay and mail claims.

Commands used:

```powershell
# From project root
.\backend\venv\Scripts\python.exe -B backend/manage.py check
.\backend\venv\Scripts\python.exe -B backend/manage.py makemigrations --check --dry-run
.\backend\venv\Scripts\python.exe -B backend/manage.py test students --noinput --buffer
.\backend\venv\Scripts\python.exe -B -m unittest ai.test_evidence_frame
# From frontend
npm.cmd run build
node --test src/hooks/useGateCycle.test.js
```

Assumptions: every student, including AI PASS, requires OSA authorization; the
existing BENCH_GATE_V1 Uno sketch is still the uploaded firmware; official legacy
history is identified by the existing confirmed_entry flag; the single physical
lane continues to accept one active attempt at a time. The configured timezone
is Asia/Manila. No physical motor/sensor operation or live Gmail delivery was
performed by the agent; use the acceptance steps above. The frontend build retains
the existing large-bundle warning. No code was pushed as part of this workflow update.
