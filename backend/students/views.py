from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse

from .models import (
    Student,
    OSAAccount,
    AccessAttempt,
    EntryLog,
    ViolationReport
)

from .serializers import StudentSerializer


# =========================================================
# STUDENT LIST
# =========================================================

class StudentList(generics.ListAPIView):

    queryset = Student.objects.all()
    serializer_class = StudentSerializer


# =========================================================
# LOGIN
# =========================================================

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


# =========================================================
# LATEST SCAN
# =========================================================

class LatestScanView(APIView):

    def get(self, request):

        attempt = AccessAttempt.objects.filter(
            processed=False
        ).order_by(
            "-scan_time"
        ).first()

        if not attempt:

            return Response({
                "success": False
            })

        student = attempt.student

        attempt.processed = True
        attempt.save()

        photo = None

        if student.id_front:
            photo = request.build_absolute_uri(
                student.id_front.url
            )

        return Response({

            "success": True,

            "student": {

                "id": student.student_number,

                "name": student.full_name,

                "college": student.college,

                "photo": photo
            }

        })


# =========================================================
# DASHBOARD DATA
# =========================================================

def dashboard_data(request):

    students_today = AccessAttempt.objects.count()

    total_violations = AccessAttempt.objects.filter(
        has_violation=True
    ).count()

    violations_today = total_violations

    compliant = students_today - total_violations

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
                else "Access Granted",

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


# =========================================================
# RECORDS
# =========================================================

def records_data(request):

    students = Student.objects.all()

    records = []

    for student in students:

        violations = ViolationReport.objects.filter(
            student=student
        )

        records.append({

            "studentNumber":
                student.student_number,

            "name":
                student.full_name,

            "college":
                student.college,

            "violations":
                violations.count(),

            "status":
                "Violation"
                if violations.exists()
                else "Clear"

        })

    return JsonResponse({
        "records": records
    })


# =========================================================
# BARCODE SCAN
# =========================================================

class BarcodeScanView(APIView):

    def post(self, request):

        # Get barcode sent by the physical scanner
        barcode = request.data.get("barcode")

        # Make sure it is treated as text
        if barcode is not None:
            barcode = str(barcode).strip()

        # No barcode
        if not barcode:

            return Response(
                {
                    "success": False,
                    "message": "No barcode provided"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        print("BARCODE RECEIVED:", barcode)

        try:

            # =================================================
            # FIND STUDENT USING BARCODE
            # =================================================

            student = Student.objects.get(
                barcode=barcode
            )

            print(
                "STUDENT FOUND:",
                student.student_number,
                student.full_name
            )

            # =================================================
            # CREATE ACCESS ATTEMPT
            # =================================================

            attempt = AccessAttempt.objects.create(
                student=student
            )

            # =================================================
            # GET ID FRONT PHOTO
            # =================================================

            photo = None

            if student.id_front:

                photo = request.build_absolute_uri(
                    student.id_front.url
                )

                print(
                    "ID PHOTO:",
                    photo
                )

            else:

                print(
                    "NO ID PHOTO FOR:",
                    student.student_number
                )

            # =================================================
            # RETURN STUDENT INFORMATION
            # =================================================

            return Response(

                {
                    "success": True,

                    "student": {

                        "id":
                            student.student_number,

                        "name":
                            student.full_name,

                        "college":
                            student.college,

                        "photo":
                            photo

                    },

                    "attempt_id":
                        attempt.id
                },

                status=status.HTTP_200_OK
            )

        except Student.DoesNotExist:

            print(
                "BARCODE NOT FOUND:",
                barcode
            )

            return Response(

                {
                    "success": False,

                    "message":
                        "Barcode not registered",

                    "barcode":
                        barcode
                },

                status=status.HTTP_404_NOT_FOUND
            )


# =========================================================
# RECEIVE AI RESULT
# =========================================================

@api_view(["POST"])
def receive_ai_result(request):

    student_number = request.data.get(
        "student_number"
    )

    result_status = request.data.get(
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
            status=status.HTTP_404_NOT_FOUND
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
        result_status == "VIOLATION"
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


# =========================================================
# CONFIRM ENTRY
# =========================================================

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
                "success": False,
                "message": "Student not found"
            },
            status=status.HTTP_404_NOT_FOUND
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
                "success": False,
                "message": "No pending entry"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # =================================================
    # ULTRASONIC CONFIRMATION
    # =================================================

    attempt.entered = True
    attempt.save()

    # =================================================
    # CREATE ENTRY LOG
    # =================================================

    entry, created = EntryLog.objects.get_or_create(

        attempt=attempt,

        defaults={
            "status": "Access Granted"
        }

    )

    # =================================================
    # SAVE VIOLATION
    # =================================================

    if attempt.has_violation:

        ViolationReport.objects.get_or_create(

            student=student,

            violation_type=
                attempt.violation_type,

            confirmed_entry=True

        )

    return Response({

        "success": True,

        "message":
            "Entry confirmed"

    })