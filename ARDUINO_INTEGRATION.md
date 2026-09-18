# Connecting SHESEETVAI to an Arduino Gate

Project: `D:\CODING\SHESEETVAI-clean`
Date: 2026-09-12

## Scope

Use USB serial communication between the Windows PC and Arduino. A dedicated Python bridge owns the COM port; Django authorizes entry and stores events; Arduino controls the mechanism and reads sensors.

This document is a setup and implementation guide. It does not install software, change application behavior, or provide finished gate firmware. Board, actuator, sensor, and power-supply models must be confirmed before final wiring and firmware are produced.

## 1. Connection flow

```text
Student ID scan -> Django access attempt -> AI inspection
                                               |
                            PASS or completed OSA review
                                               |
                                  Django queues OPEN
                                               |
                                  Python serial bridge
                                               | USB
                                      Arduino controller
                                               |
                                   Gate actuator + sensors
                                               |
                           ENTERED event with access-attempt ID
                                               | USB
                                  Python bridge -> Django
                                               |
                               Entry log and violation record
```

The React page displays backend status. It should not directly control the COM port or decide that someone has physically entered.

## 2. Existing project integration points

| File | Existing responsibility | Integration work |
| --- | --- | --- |
| `backend/students/views.py` | AI results, OSA review, entry confirmation | Queue authorized gate commands and validate hardware events |
| `backend/students/models.py` | AccessAttempt, EntryLog, AIInspection | Track authorization, command delivery, and hardware status separately |
| `backend/students/urls.py` | Student API routes | Add authenticated bridge endpoints |
| `frontend/src/pages/StudentPage.jsx` | Student scan and inspection interface | Display waiting, opening, passage, and hardware fault states |
| `ai/camera_server.py` | Camera and AI service | Keep camera handling separate from the serial-port owner |

Existing entry endpoint:

```text
POST http://127.0.0.1:8000/api/students/confirm-entry/
```

Its current request uses `student_number` and selects the latest unentered attempt. Its code explicitly anticipates Arduino/HC-SR04 passage confirmation.

Before connecting live sensor events, change this to validate an explicit `attempt_id`. Selecting the latest attempt can associate a delayed event with the wrong scan.

Current code also sets `gate_opened = True` in multiple software paths. This is not evidence of physical gate movement. Do not use this flag alone to trigger hardware.

## 3. Entry policy

The current OSA review code explicitly allows entry even when a violation is confirmed.

Recommended hardware authorization points:

| System outcome | Proposed gate action |
| --- | --- |
| Unknown or invalid student ID | Do not authorize opening |
| Inspection running | Wait |
| AI PASS | Queue one opening command |
| Suspected violation pending OSA | Wait for review |
| OSA YES: violation confirmed | Queue opening; preserve confirmed violation |
| OSA NO: false detection | Queue opening without confirmed violation |
| Camera failure or unavailable hardware | Show fault; do not invent successful inspection or entry |

Waiting for OSA is the proposed integration policy, not a claim that the existing software already enforces it on physical hardware.

Opening and entry are separate events. Create the entry log only after validated passage. Preserve the existing logic that records a confirmed violation when the associated entry is confirmed.

## 4. Hardware setup

Required items depend on the mechanism:

- Arduino board with a USB data connection.
- USB data cable connected to the system PC.
- Gate actuator and an appropriate power supply/controller.
- Passage sensor; gate position feedback where available.
- Wiring and a shared reference ground where required by the circuit.

### Example only: Uno R3 and a small hobby-servo model

This pin allocation is a proposed bench setup, not verified wiring for your hardware.

| Component connection | Example connection |
| --- | --- |
| Arduino USB | Windows PC |
| Servo signal | D9 |
| Servo positive supply | External regulated supply matched to servo specifications |
| Servo ground | External supply ground |
| Arduino GND | Same external supply ground |
| Optional HC-SR04 VCC | Uno 5V |
| Optional HC-SR04 GND | Common ground |
| Optional HC-SR04 TRIG | D6 |
| Optional HC-SR04 ECHO | D7 |

Verify component ratings first. This HC-SR04 example assumes a 5 V Uno R3; do not copy its ECHO wiring onto a 3.3 V board without suitable level conversion.

Arduino recommends an appropriate external supply for servos and connecting its ground to Arduino ground. See [Arduino servo troubleshooting](https://support.arduino.cc/hc/en-us/articles/360017053760-Troubleshoot-servo-motors).

A single ultrasonic sensor detects proximity; it does not reliably establish passage direction. For stronger entry confirmation, use two suitably positioned sensors and validate their activation sequence. Keep passage sensing separate from obstruction protection.

For a full-size gate, use the gate controller's documented control interface and independent obstruction protection, limits, and emergency release. Do not connect a gate motor directly to an Arduino pin. Closing must remain inhibited while the passage is obstructed.

## 5. Prepare Windows and Arduino

1. Install Arduino IDE and select the actual board model.
2. Connect the board using a USB data cable.
3. Find its COM port in Arduino IDE or Windows Device Manager.
4. Upload firmware implementing the protocol in section 6.
5. Set both firmware and Python to 115200 baud.
6. Close Arduino Serial Monitor before starting the Python bridge.

In the Python environment intended for the bridge:

```powershell
python -m pip install pyserial requests
python -m serial.tools.list_ports
```

Example bridge configuration:

```text
ARDUINO_PORT=COM3
ARDUINO_BAUD=115200
DJANGO_BASE_URL=http://127.0.0.1:8000
```

Replace COM3 with the detected port. These are proposed configuration names, not settings currently consumed by the project.

Use finite read/write timeouts. pySerial documents COM-port access and timeout behavior in its [short introduction](https://pyserial.readthedocs.io/en/stable/shortintro.html). Configure the matching board rate with [Serial.begin](https://github.com/arduino/reference-en/blob/master/Language/Functions/Communication/Serial/begin.adoc).

## 6. Define a serial protocol

Use newline-terminated messages. The following is a proposed protocol; it must be implemented on both sides.

| Direction | Example | Meaning |
| --- | --- | --- |
| Arduino -> bridge | `READY 1` | Firmware ready, protocol version 1 |
| Bridge -> Arduino | `OPEN 123 456` | Command 123 authorizes attempt 456 |
| Arduino -> bridge | `ACK 123 456` | Command accepted, not proof of movement |
| Arduino -> bridge | `OPENED 123 456` | Open position confirmed by feedback |
| Arduino -> bridge | `ENTERED 123 456` | Valid passage sequence completed |
| Arduino -> bridge | `CLOSED 123 456` | Closed position confirmed by feedback |
| Arduino -> bridge | `ERROR 123 456 OBSTRUCTED` | Fault requiring handling |

If the prototype lacks position feedback, report an explicitly named estimated state such as `OPEN_ESTIMATED`; a servo command does not prove the arm moved.

Firmware requirements:

- Bound message length and reject malformed commands.
- Allow only one active passage attempt at a time.
- Acknowledge duplicate command IDs without repeating movement.
- Use a nonblocking state machine so sensors remain monitored during movement.
- Debounce sensor events and emit one ENTERED event per active attempt.
- Ignore unrelated proximity detections when no attempt is active.
- Do not infer passage from a timer.
- Use an appropriate obstruction-aware close sequence.
- On reset, announce READY and require reconciliation before accepting queued work.

Do not blindly replay OPEN after reconnecting. An Arduino reset may clear its command memory. Mark uncertain commands for reconciliation, using persistent identifiers/state where needed.

## 7. Implement the Python bridge

Suggested new file:

```text
backend/gate_bridge.py
```

Run it as a separate, single process. Do not start serial connections in Django imports, request handlers, or development autoreload hooks.

The bridge should:

1. Open the configured serial port with finite timeouts.
2. Wait for READY and check protocol compatibility.
3. Obtain an authorized command from Django.
4. Write its command ID and attempt ID to Arduino.
5. Read and validate complete event messages.
6. Forward hardware events to Django.
7. Retry event delivery using the same event identifier.
8. Persist undelivered events across bridge restarts.
9. Report connection loss and reconnect with backoff.

Maintain partial input until a newline arrives: a timed-out read can return an incomplete message. Keep serial reading responsive while HTTP requests are in progress.

Only this bridge should own the COM port. Camera service restarts should not restart the gate controller connection.

## 8. Implement backend command and event handling

Suggested new routes, not currently available:

```text
POST /api/gate/commands/claim/
POST /api/gate/events/
```

Use authenticated bridge requests. Validate device identity and permissions server-side; do not place a device credential in frontend code.

Recommended command fields:

- Unique command ID and associated AccessAttempt ID.
- Gate/device ID.
- Authorization reason and timestamp.
- Expiration time.
- Delivery and acknowledgement state.

Queue a command once per authorized attempt. Save it transactionally with authorization, then let the bridge claim it after commit. A durable command record prevents a temporary USB failure from silently losing the operation.

Example proposed hardware-event request:

```json
{
  "event_id": "gate-1-session-8-event-42",
  "device_id": "gate-1",
  "command_id": 123,
  "attempt_id": 456,
  "event": "ENTERED"
}
```

For ENTERED:

1. Authenticate the bridge.
2. Validate the command, device, attempt, authorization, and active session.
3. Reject mismatched or stale events.
4. Lock the relevant database record inside a transaction.
5. Deduplicate by event ID and attempt.
6. Mark the exact attempt as entered and create its EntryLog once.
7. Apply the existing confirmed-violation recording logic.
8. Return success for already-processed identical events.

Refactor the existing `confirm_entry()` logic into a shared service or adapt that endpoint to the same validation rules. Do not leave an unvalidated alternate route that can bypass hardware-event checks.

Track authorization, command acceptance, physical gate feedback, and actual entry separately. A missing acknowledgement must produce an uncertain/fault state rather than an entry log.

## 9. Startup sequence after implementation

1. Connect and power the verified Arduino circuit.
2. Start Django from the backend environment.
3. Start the existing AI camera service in its appropriate environment.
4. Start the new gate bridge.
5. Confirm READY and a healthy device state.
6. Start the frontend and perform a controlled scan.

Proposed bridge command, usable only after that file is implemented:

```powershell
Set-Location 'D:\CODING\SHESEETVAI-clean\backend'
python gate_bridge.py
```

## 10. Verification checklist

Start with an LED or unloaded model mechanism before testing movement.

- Valid scan and AI PASS produce one authorized OPEN command.
- Pending OSA review does not open under the proposed policy.
- OSA YES permits entry and records the confirmed violation after passage.
- OSA NO permits entry without a confirmed violation.
- Opening without passage creates no entry log.
- Duplicate commands do not repeat movement.
- Duplicate ENTERED events create only one entry log.
- Events for a different attempt/device are rejected.
- A second scan cannot replace the active student's passage association.
- USB disconnect shows a hardware fault without marking entry.
- Reset/reconnect does not replay an uncertain opening.
- Network failure preserves events for safe retry.
- Obstruction inhibits closing.
- Position failures are reported accurately.
- Invalid IDs and unauthorized API requests do not actuate the gate.

## 11. Troubleshooting

| Symptom | Check |
| --- | --- |
| COM port missing | USB data cable, board driver, Device Manager |
| Port access denied | Close Serial Monitor and other bridge instances |
| Unreadable messages | Matching baud rate and newline framing |
| Board resets or servo jitters | Supply capacity, grounding, wiring, mechanical load |
| UI indicates open but mechanism does not move | Distinguish software authorization from hardware feedback |
| Entry recorded for wrong scan | Exact attempt ID validation and one active passage |
| Multiple entry records | Durable event deduplication and transactional updates |
| Sensor fires without entry | Placement, debounce, passage sequence, active-attempt checks |

## 12. Information needed for final implementation

Record these before writing hardware-specific firmware:

- Exact Arduino model.
- Servo/motor and gate-controller model.
- Prototype or full-size mechanism.
- Sensor models and quantity.
- Power-supply voltage/current rating.
- Windows COM port.
- Opening/closing feedback and obstruction detection.
- Intended behavior while OSA review is pending.
