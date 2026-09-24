# Gmail violation notices

## Local setup

1. Install backend requirements and run migrations from `backend`:
   `venv\Scripts\python.exe -m pip install -r requirements.txt`
   `venv\Scripts\python.exe manage.py migrate`
2. Edit `backend/.env` locally (an empty ignored file has been created):
   ```dotenv
   EMAIL_HOST_USER=your_system_email@gmail.com
   EMAIL_HOST_PASSWORD=your_google_app_password
   ```
   Use your Google App Password, not your normal account password. Paste the app
   password without display-grouping spaces. `DEFAULT_FROM_EMAIL` is optional and
   defaults to the sender account. Never commit this file or paste credentials
   into screenshots, logs, tickets, or source files. `backend/.env.example` has
   placeholders only. Existing process environment variables take precedence.
3. Restart Django and the USB bridge so they load the changed code/settings.
   Restart the bridge only after the existing closed-reference procedure.
4. Start `START_EMAIL.cmd` and leave it running alongside the system. Equivalent,
   from `backend`: `venv\Scripts\python.exe manage.py send_violation_emails --watch`.
   Without `--watch`, the command processes up to 100 pending messages once.
5. Ensure the student's existing `email` is correct (the existing Django admin
   can edit it). A normal confirmed violation plus actual entry will queue mail.

SMTP uses Django's SMTP backend, smtp.gmail.com, port 587, STARTTLS, and a
15-second socket timeout. No live Gmail delivery was tested without credentials.
Reference: https://docs.djangoproject.com/en/6.0/topics/email/

## Existing workflow and daily rule

`Student.email`, `Student.full_name`, and `Student.student_number` are reused.
No existing field or API was replaced. `AIInspection.screenshot` supplies the
actual attachment through its configured Django storage; no guessed path or
student ID photograph is used. JPG/JPEG/PNG evidence is attached when readable;
missing evidence sends a notice without an attachment. Missing/invalid student
email skips sending without blocking record creation or entry.

`students.gate.save_violation()` remains the only application finalization point.
See `WORKFLOW_UPDATE.md` for the adviser-approved three-decision workflow.
It requires OSA CONFIRMED_ALLOW, acknowledged `gate_opened`, `AccessAttempt.entered`,
and the matching sensor-confirmed ENTERED gate cycle, and excludes cancelled
passages. The first finalized report on each Asia/Manila calendar day creates
one official `ViolationReport`, one `Violation` containing all detected types, and one new
`ViolationEmail` queue row. Multiple types in that first inspection share one
notice. A later scan with any violation type that day creates no additional
report, violation row, or notice; its AI review, entry log and gate cycle continue.
The later inspection is marked `recorded=True` to mean finalization was handled,
so it cannot be replayed tomorrow to create a delayed duplicate.

The date is the report creation date, consistent with existing Records/Dashboard,
not the initial scan or AI capture date. A new confirmed entry after local
midnight can create the next day's report. Existing controller write locking
serializes concurrent HTTP/USB finalization, including on SQLite. Historical
confirmed-entry reports also suppress another report for that date. Historical duplicates are
not removed, and historical records are not emailed. Direct ORM/admin creation
is unchanged and does not send mail; callers must use the existing finalization
service to obtain its daily duplicate protection.

## Delivery and failure behavior

The additive `0011_violation_email_queue` migration creates only the delivery
queue. The report and queue insert commit or roll back together. The separate
worker never runs inside the USB event loop or web request and reads committed
rows only. Its atomic PENDING-to-SENDING claim prevents competing workers from
sending the same queued notice. Refreshes, repeated reviews, repeated model
saves and repeated worker runs do not resend it.

Worker output identifies each queue ID and status: PENDING, SENDING, SENT,
SKIPPED or FAILED. With Gmail credentials absent, the worker stops with setup
instructions and leaves notices PENDING. Exception logging stores only exception
class names, not SMTP response bodies or credentials.

SMTP cannot guarantee exactly-once delivery when a connection/process fails
after Gmail accepts a message. To avoid duplicate notices, FAILED and stranded
SENDING rows are not automatically retried. Inspect the sender's Sent folder
and queue row before any deliberate recovery. SENT means SMTP accepted the
message, not a guarantee that it reached the recipient's inbox. Keep the worker
running for automatic delivery; pending rows survive worker restarts.

## Verification

`venv\Scripts\python.exe -B manage.py test students --noinput`

Tests use Django's in-memory mail backend, temporary storage and generated test
images, never live student recipients. Coverage includes byte-for-byte JPG/PNG
attachments, repeat reviews, same-day/different-student rules, Manila midnight,
transaction rollback, absent email/images, SMTP failure, concurrent finalization,
concurrent delivery claims, and the existing gate/records tests.

## Offense totals and denied entry

Only `ViolationReport.confirmed_entry=True` contributes to official totals.
Historical per-type Violation rows remain stored and are not counted separately.
Current Minor Offenses is the total official report count; Equivalent Major
Offenses is that count divided by 3 using integer division. Both appear in mail
and Records evidence details. Totals never reset after a major equivalent.

DENY leaves the gate closed and creates no official report, Violation or email.
NO allows normal sensor-confirmed entry without an offense. AI PASS also waits
for OSA. YES queues opening and waits for actual entry before recording anything.
Mail is delivered by the worker only after the offense transaction has committed.
