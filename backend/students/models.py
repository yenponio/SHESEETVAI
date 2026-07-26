from django.db import models


class Student(models.Model):
    student_number = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    college = models.CharField(max_length=150)

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
        return f"{self.student_number} - {self.full_name}"


class Violation(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="violations"
    )

    violation_type = models.CharField(max_length=200)

    status = models.CharField(
        max_length=20,
        default="Unread"
    )

    detected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.violation_type}"


class OSAAccount(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.email

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


    def __str__(self):
        return f"{self.student} - {self.scan_time}"

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
        return f"{self.attempt.student.full_name} - {self.status}"


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
        return f"{self.student} - {self.violation_type}"