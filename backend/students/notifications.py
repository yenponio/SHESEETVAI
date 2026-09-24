"""Deliver committed violation notifications outside HTTP/USB processing."""
import logging
from pathlib import PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.db import connection
from django.utils import timezone

from .models import ViolationEmail
from .offenses import offense_counts

logger = logging.getLogger(__name__)


def deliver_notification(notification_id):
    # A worker must claim in autocommit before making external side effects.
    if connection.in_atomic_block:
        raise RuntimeError("Email delivery must run outside database transactions")
    if (settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"
            and not (settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD
                     and settings.DEFAULT_FROM_EMAIL)):
        return False  # Leave pending until configured, without losing the notice.
    claimed = ViolationEmail.objects.filter(pk=notification_id, status="PENDING").update(
        status="SENDING", error="",
    )
    if not claimed:
        return False
    try:
        notice = ViolationEmail.objects.select_related("report__student", "report__inspection", "inspection").get(
            pk=notification_id,
        )
        student = notice.report.student
        recipient = (student.email or "").strip()
        try:
            validate_email(recipient)
        except ValidationError:
            ViolationEmail.objects.filter(pk=notification_id).update(
                status="SKIPPED", error="Student email is missing or invalid",
            )
            return False
        attachment = None
        # New reports are the canonical evidence link; retain exact legacy queue links.
        inspection = notice.report.inspection if notice.report.inspection_id else notice.inspection
        screenshot = inspection.screenshot if inspection else None
        if screenshot:
            filename = PurePosixPath(screenshot.name.replace("\\", "/")).name
            mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(
                PurePosixPath(filename).suffix.lower(),
            )
            if mime:
                try:
                    # Use the ImageField's storage, never guess a media directory.
                    with screenshot.storage.open(screenshot.name, "rb") as evidence:
                        attachment = (filename, evidence.read(), mime)
                except Exception:
                    logger.warning("Evidence unavailable for violation email %s", notification_id)
        occurred = timezone.localtime(notice.report.report_time, timezone.get_default_timezone())
        evidence_text = ("Please see the attached image for the recorded evidence."
                         if attachment else "No evidence image was available for this notification.")
        counts = offense_counts(student.pk)
        body = (
            f"Dear {student.full_name or student.student_number},\n\n"
            "A dress-code violation was recorded during your campus entry.\n\n"
            f"Student Number: {student.student_number}\n"
            f"Violation: {notice.report.violation_type}\n"
            f"Date/Time: {occurred:%Y-%m-%d %H:%M:%S %Z}\n\n"
            f"Current Minor Offenses: {counts['total_minor_offenses']}\n"
            f"Equivalent Major Offenses: {counts['equivalent_major_offenses']}\n\n"
            f"{evidence_text}\n\n"
            "This is an automated notification from the SHESEETVAI system."
        )
        message = EmailMessage(
            subject="SHESEETVAI - Dress Code Violation Notice", body=body,
            from_email=settings.DEFAULT_FROM_EMAIL, to=[recipient],
        )
        if attachment:
            message.attach(*attachment)
        if message.send(fail_silently=False) != 1:
            raise RuntimeError("Email backend did not accept the message")
    except Exception as error:
        # Do not expose credentials, recipient addresses or SMTP response bodies.
        ViolationEmail.objects.filter(pk=notification_id).update(
            status="FAILED", error=type(error).__name__,
        )
        logger.warning("Violation email %s failed (%s)", notification_id, type(error).__name__)
        return False
    ViolationEmail.objects.filter(pk=notification_id).update(status="SENT", sent_at=timezone.now())
    return True
