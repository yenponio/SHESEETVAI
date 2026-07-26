from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
from .models import Student, ViolationReport

from .models import (
    Student,
    OSAAccount,
    EntryLog,
    ViolationReport
)

from .serializers import StudentSerializer


class StudentList(generics.ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        account = OSAAccount.objects.filter(
            email=email,
            password=password
        ).first()

        if account:
            return Response(
                {
                    "success": True,
                    "message": "Login successful"
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "success": False,
                "message": "Invalid email or password"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )


def dashboard_data(request):

    today = timezone.now().date()

    # Students who entered today
    students_today = EntryLog.objects.filter(
        entry_time__date=today
    ).count()


    # Violations today
    violations_today = ViolationReport.objects.filter(
        report_time__date=today
    ).count()


    # Total violations
    total_violations = ViolationReport.objects.count()


    # Compliance calculation
    total_entries = EntryLog.objects.count()

    compliant = total_entries - total_violations

    if compliant < 0:
        compliant = 0


    # Students per college
    college_chart = (
        Student.objects
        .values("college")
        .annotate(count=Count("id"))
    )


    # Recent scans
    recent_logs = []

    logs = EntryLog.objects.select_related(
        "attempt__student"
    ).order_by(
        "-entry_time"
    )[:5]


    for log in logs:

        student = log.attempt.student

        violation = ViolationReport.objects.filter(
            student=student,
            confirmed_entry=True
        ).exists()


        recent_logs.append({
            "student_number": student.student_number,
            "name": student.full_name,
            "college": student.college,
            "status": (
                "Dress Code Violation"
                if violation
                else "Access Granted"
            )
        })


    return JsonResponse(
        {
            "students_today": students_today,
            "total_violations": total_violations,
            "violations_today": violations_today,
            "compliant": compliant,
            "violation_count": total_violations,
            "college_chart": list(college_chart),
            "recent_logs": recent_logs
        }
    )
def records_data(request):

    students = Student.objects.all()

    records = []

    for student in students:

        violations = ViolationReport.objects.filter(
            student=student
        )


        records.append({

            "studentNumber": student.student_number,

            "name": student.full_name,

            "college": student.college,

            "violations": violations.count(),

            "status":
                "Violation"
                if violations.exists()
                else "Clear"

        })


    return JsonResponse({
        "records": records
    })