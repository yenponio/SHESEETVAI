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
#       ↓
# screenshot + violations saved here
#       ↓
# OSA sees it
#       ↓
# OSA presses YES or NO
#
# ==========================================================

class AIInspection(models.Model):

    STATUS_CHOICES = [
        (
            "PENDING",
            "Pending Confirmation"
        ),
        (
            "CONFIRMED",
            "Confirmed Violation"
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


    def __str__(self):

        return (
            f"{self.student.student_number} - "
            f"{self.confirmation_status}"
        )