from django.db import models


# ==========================================================
# STUDENT
# ==========================================================

class Student(models.Model):
    student_number = models.CharField(
        max_length=20,
        unique=True
    )

    barcode = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )

    full_name = models.CharField(
        max_length=150
    )

    email = models.EmailField()

    college = models.CharField(
        max_length=150
    )

    id_front = models.ImageField(
        upload_to="students/id_front/",
        blank=True,
        null=True
    )

    id_back = models.ImageField(
        upload_to="students/id_back/",
        blank=True,
        null=True
    )

    def __str__(self):
        return (
            f"{self.student_number} - "
            f"{self.full_name}"
        )


# ==========================================================
# CONFIRMED VIOLATION
# ==========================================================

class Violation(models.Model):
    inspection = models.ForeignKey(
        "AIInspection", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="confirmed_violations",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="violations"
    )

    violation_type = models.CharField(
        max_length=200
    )

    status = models.CharField(
        max_length=20,
        default="Unread"
    )

    detected_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.student.full_name} - "
            f"{self.violation_type}"
        )


# ==========================================================
# OSA ACCOUNT
# ==========================================================

class OSAAccount(models.Model):
    email = models.EmailField(
        unique=True
    )

    password = models.CharField(
        max_length=100
    )

    def __str__(self):
        return self.email


# ==========================================================
# ACCESS ATTEMPT
# ==========================================================

class AccessAttempt(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    scan_time = models.DateTimeField(
        auto_now_add=True
    )

    has_violation = models.BooleanField(
        default=False
    )

    violation_type = models.CharField(
        max_length=100,
        blank=True
    )

    gate_opened = models.BooleanField(
        default=False
    )

    entered = models.BooleanField(
        default=False
    )

    processed = models.BooleanField(
        default=False
    )

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.scan_time}"
        )


# ==========================================================
# ENTRY LOG
# ==========================================================

class EntryLog(models.Model):
    attempt = models.OneToOneField(
        AccessAttempt,
        on_delete=models.CASCADE
    )

    entry_time = models.DateTimeField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=50,
        default="Access Granted"
    )

    def __str__(self):
        return (
            f"{self.attempt.student.full_name} - "
            f"{self.status}"
        )


# ==========================================================
# OLD / GENERAL VIOLATION REPORT
# ==========================================================

class ViolationReport(models.Model):
    inspection = models.ForeignKey(
        "AIInspection", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="violation_reports",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    violation_type = models.CharField(
        max_length=100
    )

    report_time = models.DateTimeField(
        auto_now_add=True
    )

    confirmed_entry = models.BooleanField(
        default=False
    )

    sent_to_osa = models.BooleanField(
        default=False
    )

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.violation_type}"
        )


# ==========================================================
# AI INSPECTION
# ==========================================================
#
# This stores a suspected violation detected by the AI.
#
# It is NOT considered a confirmed violation yet.
#
# Flow:
#
# AI detects violation
#       â†“
# screenshot + violations saved here
#       â†“
# OSA sees it
#       â†“
# OSA presses YES or NO
#
# ==========================================================

class AIInspection(models.Model):

    STATUS_CHOICES = [
        ("CONFIRMED_ALLOW", "Confirmed Violation - Allow Entry"),
        ("CONFIRMED_DENY", "Confirmed Violation - Deny Entry"),
        (
            "PENDING",
            "Pending Confirmation"
        ),
        (
            "CONFIRMED",
            "Confirmed Violation (Historical)"
        ),
        (
            "REJECTED",
            "False Detection"
        ),
    ]


    # ======================================================
    # STUDENT
    # ======================================================

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="ai_inspections"
    )


    # ======================================================
    # ACCESS ATTEMPT
    # ======================================================

    attempt = models.ForeignKey(
        AccessAttempt,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="ai_inspections"
    )


    # ======================================================
    # AI RESULT
    # ======================================================

    ai_result = models.CharField(
        max_length=20,
        default="VIOLATION"
    )


    # ======================================================
    # VIOLATIONS
    # ======================================================
    #
    # Example:
    #
    # [
    #   "Shoulders exposed",
    #   "Knees exposed"
    # ]
    #
    # ======================================================

    violations = models.JSONField(
        default=list,
        blank=True
    )


    # ======================================================
    # SCREENSHOT
    # ======================================================

    screenshot = models.ImageField(
        upload_to="ai_inspections/",
        blank=True,
        null=True
    )


    # ======================================================
    # CONFIRMATION STATUS
    # ======================================================

    confirmation_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )


    # ======================================================
    # DATE AI DETECTED IT
    # ======================================================

    detected_at = models.DateTimeField(
        auto_now_add=True
    )


    # ======================================================
    # DATE OSA CONFIRMED / REJECTED
    # ======================================================

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    # ======================================================
    # FINAL VIOLATION ALREADY SAVED
    # ======================================================

    recorded = models.BooleanField(
        default=False
    )

    def __str__(self):

        return (
            f"{self.student.student_number} - "
            f"{self.confirmation_status}"
        )


# USB gate integration: no new calendar timestamp fields.
class GateCycle(models.Model):
    attempt = models.OneToOneField(
        AccessAttempt, on_delete=models.CASCADE, primary_key=True,
        related_name="gate_cycle",
    )
    phase = models.CharField(max_length=20, default="WAITING_OSA")
    outcome = models.CharField(max_length=20, default="PENDING")
    bridge_id = models.CharField(max_length=64, blank=True)
    message = models.CharField(max_length=160, blank=True)


class GateController(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    enabled = models.BooleanField(default=False)
    connected = models.BooleanField(default=False)
    ready = models.BooleanField(default=False)
    active_cycle = models.OneToOneField(
        GateCycle, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
    )
    bridge_id = models.CharField(max_length=64, blank=True)
    process_id = models.PositiveIntegerField(default=0)
    revision = models.PositiveBigIntegerField(default=0)


class GateEvent(models.Model):
    key = models.CharField(max_length=100, primary_key=True)
    cycle = models.ForeignKey(GateCycle, on_delete=models.CASCADE)
    event = models.CharField(max_length=32)


class ViolationEmail(models.Model):
    """Durable delivery queue; existing violation and inspection models stay intact."""
    report = models.OneToOneField(ViolationReport, on_delete=models.CASCADE,
                                  related_name="email_notification")
    inspection = models.ForeignKey(AIInspection, on_delete=models.SET_NULL,
                                   null=True, related_name="email_notifications")
    status = models.CharField(max_length=12, default="PENDING", db_index=True,
                              choices=[(value, value.title()) for value in
                                       ("PENDING", "SENDING", "SENT", "SKIPPED", "FAILED")])
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=200, blank=True)
