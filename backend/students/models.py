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