"""Run separately from Django/USB so SMTP cannot delay gate events."""
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, close_old_connections

from students.models import ViolationEmail
from students.notifications import deliver_notification


class Command(BaseCommand):
    help = "Deliver pending confirmed-violation emails; use --watch for continuous delivery."

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true")

    def handle(self, *args, **options):
        if (settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"
                and not (settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD
                         and settings.DEFAULT_FROM_EMAIL)):
            raise CommandError("Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in backend/.env first.")
        try:
            while True:
                close_old_connections()
                try:
                    ids = list(ViolationEmail.objects.filter(status="PENDING")
                               .order_by("pk").values_list("pk", flat=True)[:100])
                    for notice_id in ids:
                        deliver_notification(notice_id)
                        state = ViolationEmail.objects.filter(pk=notice_id).values_list("status", flat=True).first()
                        self.stdout.write(f"Violation email {notice_id}: {state}")
                except OperationalError:
                    if not options["watch"]:
                        raise
                    self.stderr.write("Database temporarily unavailable; pending notices will be checked again.")
                if not options["watch"]:
                    break
                time.sleep(2)
        except KeyboardInterrupt:
            self.stdout.write("Email worker stopped.")
