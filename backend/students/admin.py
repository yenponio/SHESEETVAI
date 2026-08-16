from django.contrib import admin
from .models import (
    Student,
    Violation,
    OSAAccount,
    AccessAttempt,
    EntryLog,
    ViolationReport
)


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


@admin.register(OSAAccount)
class OSAAccountAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "password",
    )

    search_fields = (
        "email",
    )

@admin.register(AccessAttempt)
class AccessAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "scan_time",
        "has_violation",
        "gate_opened",
        "entered",
    )

    list_filter = (
        "has_violation",
        "gate_opened",
        "entered",
        "scan_time",
    )

    search_fields = (
        "student__full_name",
        "student__student_number",
    )


@admin.register(EntryLog)
class EntryLogAdmin(admin.ModelAdmin):
    list_display = (
        "attempt",
        "entry_time",
        "status",
    )

    list_filter = (
        "status",
        "entry_time",
    )

@admin.register(ViolationReport)
class ViolationReportAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "violation_type",
        "confirmed_entry",
        "sent_to_osa",
        "report_time",
    )

    list_filter = (
        "confirmed_entry",
        "sent_to_osa",
        "report_time",
    )

    search_fields = (
        "student__full_name",
        "student__student_number",
        "violation_type",
    )