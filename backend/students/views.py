from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
from .models import Student, ViolationReport, AccessAttempt

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

class LatestScanView(APIView):

    def get(self, request):

        attempt = AccessAttempt.objects.filter(
            processed=False
        ).order_by(
            "-scan_time"
        ).first()

        if not attempt:

            return Response({
                "success":False
            })


        student = attempt.student

        attempt.processed = True
        attempt.save()

        return Response({

            "success":True,

            "student":{

                "id":student.student_number,

                "name":student.full_name,

                "college":student.college,

                "photo":
                student.id_front.url
                if student.id_front
                else None
            }

        })
def dashboard_data(request):

    from django.http import JsonResponse
    from .models import AccessAttempt, Student, ViolationReport


    # TOTAL SCANS

    students_today = AccessAttempt.objects.count()



    # TOTAL VIOLATIONS

    total_violations = AccessAttempt.objects.filter(
        has_violation=True
    ).count()



    violations_today = total_violations



    compliant = (
        students_today - total_violations
    )


    if compliant < 0:
        compliant = 0




    # =========================
    # COLLEGE CHART
    # =========================


    college_chart = []


    colleges = Student.objects.values_list(
        "college",
        flat=True
    ).distinct()



    for college in colleges:


        students = AccessAttempt.objects.filter(
            student__college=college
        ).count()



        violations = AccessAttempt.objects.filter(
            student__college=college,
            has_violation=True
        ).count()



        college_chart.append({

            "college": college,

            "students": students,

            "violations": violations

        })




    # =========================
    # RECENT LOGS
    # =========================


    recent_logs = []


    attempts = AccessAttempt.objects.select_related(
        "student"
    ).order_by(
        "-scan_time"
    )[:10]



    for attempt in attempts:


        recent_logs.append({

            "studentNumber":
                attempt.student.student_number,


            "name":
                attempt.student.full_name,


            "college":
                attempt.student.college,


            "status":
                "Dress Code Violation"
                if attempt.has_violation
                else
                "Access Granted",


            "time":
                attempt.scan_time.strftime(
                    "%Y-%m-%d %H:%M"
                )

        })




    return JsonResponse({

        "students_today":
            students_today,


        "total_violations":
            total_violations,


        "violations_today":
            violations_today,


        "compliant":
            compliant,


        "violation_count":
            total_violations,


        "college_chart":
            college_chart,


        "recent_logs":
            recent_logs

    })
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


class BarcodeScanView(APIView):

    def post(self, request):

        student_number = request.data.get("student_number")


        if not student_number:
            return Response(
                {
                    "success": False,
                    "message": "No student number provided"
                },
                status=400
            )


        try:
            student = Student.objects.get(
                student_number=student_number
            )


            attempt = AccessAttempt.objects.create(
                student=student
            )


            return Response(
                {
                    "success": True,
                    "student": {
                        "id": student.student_number,
                        "name": student.full_name,
                        "college": student.college,
                        "photo": (
                            student.id_front.url
                            if student.id_front
                            else None
                        )
                    },
                    "attempt_id": attempt.id
                }
            )


        except Student.DoesNotExist:


            return Response(
                {
                    "success": False,
                    "message": "Student not found"
                },
                status=404
            )
@api_view(["POST"])
def receive_ai_result(request):

    student_number = request.data.get(
        "student_number"
    )

    status = request.data.get(
        "status"
    )

    violations = request.data.get(
        "violations",
        []
    )


    try:

        student = Student.objects.get(
            student_number=student_number
        )

    except Student.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Student not found"
            },
            status=404
        )



    attempt = AccessAttempt.objects.filter(
        student=student,
        entered=False
    ).order_by(
        "-scan_time"
    ).first()



    if not attempt:

        attempt = AccessAttempt.objects.create(
            student=student
        )



    attempt.has_violation = (
        status == "VIOLATION"
    )


    attempt.violation_type = ",".join(
        violations
    )


    attempt.gate_opened = True


    attempt.save()



    return Response({

        "success": True,

        "message":
        "AI result received"

    })

@api_view(["POST"])
def confirm_entry(request):

    student_number = request.data.get(
        "student_number"
    )


    try:

        student = Student.objects.get(
            student_number=student_number
        )


    except Student.DoesNotExist:

        return Response(
            {
                "success":False,
                "message":"Student not found"
            },
            status=404
        )



    attempt = AccessAttempt.objects.filter(
        student=student,
        entered=False
    ).order_by(
        "-scan_time"
    ).first()



    if not attempt:

        return Response(
            {
                "success":False,
                "message":"No pending entry"
            },
            status=404
        )



    # ultrasonic confirmation

    attempt.entered = True

    attempt.save()



    # Create entry log

    entry, created = EntryLog.objects.get_or_create(

        attempt=attempt,

        defaults={

            "status":"Access Granted"

        }

    )


    # Save violation after entry confirmation

    if attempt.has_violation:

        ViolationReport.objects.get_or_create(

            student=student,

            violation_type=attempt.violation_type,

            confirmed_entry=True

        )



    return Response({

        "success":True,

        "message":
        "Entry confirmed"

    })