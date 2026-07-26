from django.http import JsonResponse
from django.utils.timezone import now

from .models import (
    EntryLog,
    ViolationReport
)


def dashboard_data(request):

    today = now().date()


    # ==============================
    # Students who actually entered today
    # ==============================

    students_today = EntryLog.objects.filter(
        entry_time__date=today
    ).count()



    # ==============================
    # Violation reports
    # ==============================

    total_violations = ViolationReport.objects.count()


    violations_today = ViolationReport.objects.filter(
        report_time__date=today
    ).count()



    # ==============================
    # College violation statistics
    # ==============================

    college_list = [
        "CCJEF",
        "SAS",
        "SBA",
        "SEA",
        "SED",
        "SHTM",
        "SNAMS",
        "SOC",
    ]


    college_stats = {}


    # Create default colleges with zero values
    for college in college_list:
        college_stats[college] = {
            "college": college,
            "students": 0,
            "violations": 0
        }



    entries_today = EntryLog.objects.filter(
        entry_time__date=today
    ).select_related(
        "attempt__student"
    )



    for entry in entries_today:

        student = entry.attempt.student

        college = student.college



        # If new college exists
        if college not in college_stats:

            college_stats[college] = {
                "college": college,
                "students": 0,
                "violations": 0
            }



        # Count entered students
        college_stats[college]["students"] += 1



        # Check violation
        has_violation = ViolationReport.objects.filter(
            student=student,
            confirmed_entry=True
        ).exists()



        if has_violation:
            college_stats[college]["violations"] += 1



    college_chart = list(college_stats.values())



    # ==============================
    # Recent scan logs
    # ==============================

    recent_logs = (
        EntryLog.objects
        .select_related(
            "attempt__student"
        )
        .order_by("-entry_time")[:10]
    )



    logs = []


    for entry in recent_logs:

        student = entry.attempt.student


        has_violation = ViolationReport.objects.filter(
            student=student,
            confirmed_entry=True
        ).exists()



        logs.append({

            "studentNumber": student.student_number,

            "name": student.full_name,

            "college": student.college,

            "status": (
                "Dress Code Violation"
                if has_violation
                else "Access Granted"
            ),

            "time": entry.entry_time.strftime(
                "%Y-%m-%d %H:%M"
            ),

        })



    # Temporary until scanner timer is connected
    average_scan_time = "2.4 sec"



    return JsonResponse({

        "students_today": students_today,

        "total_violations": total_violations,

        "violations_today": violations_today,

        "average_scan_time": average_scan_time,


        "college_chart": college_chart,


        "recent_logs": logs

    })