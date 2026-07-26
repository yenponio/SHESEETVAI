from django.http import JsonResponse
from django.db.models import Count
from django.utils.timezone import now

from .models import Student, Violation

def dashboard_data(request):

    total_students = Student.objects.count()

    total_violations = Violation.objects.count()

    violations_today = Violation.objects.filter(
        detected_at__date=now().date()
    ).count()
    colleges = (
    Student.objects
    .values("college")
    .annotate(count=Count("id"))
    .order_by("college")
    )
    recent_logs = (
        Violation.objects
        .select_related("student")
        .order_by("-detected_at")[:10]
    )
    logs = []

    for violation in recent_logs:
        logs.append({
            "student": violation.student.full_name,
            "college": violation.student.college,
            "violation": violation.violation_type,
            "status": violation.status,
            "time": violation.detected_at.strftime("%Y-%m-%d %H:%M"),
        })
    return JsonResponse({
        "total_students": total_students,
        "total_violations": total_violations,
        "violations_today": violations_today,
        "college_chart": list(colleges),
        "recent_logs": logs,
    })