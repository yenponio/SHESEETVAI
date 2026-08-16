from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    AccessAttempt,
    EntryLog,
    ViolationReport
)


@receiver(post_save, sender=AccessAttempt)
def create_logs(sender, instance, created, **kwargs):

    if instance.entered:

        # Create Entry Log
        EntryLog.objects.get_or_create(
            attempt=instance,
            defaults={
                "status": "Access Granted"
            }
        )


        # Create Violation Report if student has violation
        if instance.has_violation:

            ViolationReport.objects.get_or_create(
                student=instance.student,
                violation_type=instance.violation_type,
                defaults={
                    "confirmed_entry": True,
                    "sent_to_osa": True
                }
            )