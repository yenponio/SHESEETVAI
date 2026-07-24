from django.contrib import admin
from .models import Student, Violation


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "student_number",
        "full_name",
        "email",
        "college",
    )

    search_fields = (
        "student_number",
        "full_name",
        "email",
    )


@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "violation_type",
        "status",
        "detected_at",
    )

    list_filter = (
        "status",
        "detected_at",
    )

    search_fields = (
        "student__full_name",
        "student__student_number",
        "violation_type",
    )