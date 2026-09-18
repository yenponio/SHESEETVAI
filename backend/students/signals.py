from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AccessAttempt, EntryLog


@receiver(post_save, sender=AccessAttempt)
def create_logs(sender, instance, created, **kwargs):
    if instance.entered:
        EntryLog.objects.get_or_create(
            attempt=instance,
            defaults={"status": "Access Granted"},
        )
    # Final violations are saved only by gate.save_violation after both
    # OSA confirmation and entry; this signal must not duplicate reports.
