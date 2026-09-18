from collections import Counter

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .models import EntryLog, Student
from .records import violation_records


@never_cache
def dashboard_data(request):
    today = timezone.localdate()
    records = violation_records()
    colleges = Counter(record["college"] for record in records)
    students_with_violations = {record["studentNumber"] for record in records}
    total_students = Student.objects.count()
    violation_students = len(students_with_violations)
    recent_entries = EntryLog.objects.select_related("attempt__student").order_by("-entry_time", "-pk")[:10]
    logs = [{
        "studentNumber": entry.attempt.student.student_number,
        "name": entry.attempt.student.full_name,
        "college": entry.attempt.student.college,
        "status": ("With Violation" if entry.attempt.student.student_number in students_with_violations else "No Violation"),
        "time": timezone.localtime(entry.entry_time).isoformat(),
    } for entry in recent_entries]
    return JsonResponse({
        "students_today": EntryLog.objects.filter(entry_time__date=today).count(),
        "total_violations": len(records),
        "violations_today": sum(record["date"] == today.isoformat() for record in records),
        "average_scan_time": "Not available",
        "college_chart": [{"college": college, "violations": count} for college, count in sorted(colleges.items())],
        "compliance_chart": [
            {"name": "Compliant (No Violation)", "value": total_students - violation_students},
            {"name": "With Violation", "value": violation_students},
        ],
        "recent_logs": logs,
    })
