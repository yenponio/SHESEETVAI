import json

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from django.http import JsonResponse
from django.utils import timezone

from .models import (
    Student,
    OSAAccount,
    AccessAttempt,
    EntryLog,
    ViolationReport,
    Violation,
    AIInspection,
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

        barcode = request.data.get("barcode")

        if barcode is not None:
            barcode = str(barcode).strip()

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
#
# AI sends:
#
# student_number
# status
# violations
# screenshot
# attempt_id (optional)
#
# VIOLATION:
# Creates AIInspection with PENDING status.
# It is NOT counted as confirmed until OSA presses YES.
#
# PASS:
# No OSA confirmation is needed.
#
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

    attempt_id = request.data.get(
        "attempt_id"
    )

    screenshot = request.FILES.get(
        "screenshot"
    )

    # =====================================================
    # VALIDATE STUDENT NUMBER
    # =====================================================

    if not student_number:

        return Response(
            {
                "success": False,
                "message":
                    "student_number is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # =====================================================
    # NORMALIZE STATUS
    # =====================================================

    if result_status:

        result_status = (
            str(result_status)
            .strip()
            .upper()
        )

    # =====================================================
    # NORMALIZE VIOLATIONS
    # =====================================================
    #
    # Multipart/form-data may send violations as JSON text:
    #
    # ["Shoulders exposed", "Knees exposed"]
    #
    # =====================================================

    if isinstance(violations, str):

        try:

            violations = json.loads(
                violations
            )

        except json.JSONDecodeError:

            violations = [
                item.strip()
                for item
                in violations.split(",")
                if item.strip()
            ]

    if not isinstance(
        violations,
        list
    ):

        violations = []

    # =====================================================
    # FIND STUDENT
    # =====================================================

    try:

        student = Student.objects.get(
            student_number=student_number
        )

    except Student.DoesNotExist:

        return Response(
            {
                "success": False,
                "message":
                    "Student not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # =====================================================
    # FIND ACCESS ATTEMPT
    # =====================================================

    attempt = None

    if attempt_id:

        try:

            attempt = AccessAttempt.objects.get(
                id=attempt_id,
                student=student
            )

        except AccessAttempt.DoesNotExist:

            attempt = None

    if not attempt:

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

    # =====================================================
    # AI RESULT = VIOLATION
    # =====================================================

    if result_status == "VIOLATION":

        # ---------------------------------------------
        # IMPORTANT:
        #
        # Do NOT mark AccessAttempt.has_violation=True
        # yet.
        #
        # The AI is only reporting a SUSPECTED
        # violation. OSA must confirm first.
        # ---------------------------------------------

        inspection = AIInspection.objects.create(

            student=student,

            attempt=attempt,

            ai_result="VIOLATION",

            violations=violations,

            screenshot=screenshot,

            confirmation_status="PENDING"
        )

        print("")
        print(
            "========================================"
        )

        print(
            "AI VIOLATION RECEIVED BY DJANGO"
        )

        print(
            "Student:",
            student.student_number
        )

        print(
            "Inspection ID:",
            inspection.id
        )

        print(
            "Violations:",
            violations
        )

        print(
            "Screenshot:",
            inspection.screenshot
        )

        print(
            "OSA Status: PENDING"
        )

        print(
            "========================================"
        )

        return Response(
            {
                "success": True,

                "message":
                    "Violation sent to OSA for confirmation",

                "inspection_id":
                    inspection.id,

                "confirmation_status":
                    inspection.confirmation_status
            },
            status=status.HTTP_201_CREATED
        )

    # =====================================================
    # AI RESULT = PASS
    # =====================================================

    elif result_status == "PASS":

        attempt.has_violation = False

        attempt.violation_type = ""

        # PASS does not require OSA confirmation.
        attempt.gate_opened = True

        attempt.save()

        print("")
        print(
            "========================================"
        )

        print(
            "AI PASS RECEIVED BY DJANGO"
        )

        print(
            "Student:",
            student.student_number
        )

        print(
            "========================================"
        )

        return Response(
            {
                "success": True,
                "message":
                    "Student passed dress code",
                "status":
                    "PASS"
            },
            status=status.HTTP_200_OK
        )

    # =====================================================
    # UNKNOWN RESULT
    # =====================================================

    return Response(
        {
            "success": False,
            "message":
                "Status must be PASS or VIOLATION"
        },
        status=status.HTTP_400_BAD_REQUEST
    )


# =========================================================
# GET LATEST PENDING OSA INSPECTION
# =========================================================
#
# ConfirmationPage will call this endpoint.
#
# It returns the newest AI violation waiting for
# OSA confirmation.
#
# =========================================================

@api_view(["GET"])
def latest_pending_inspection(request):

    inspection = AIInspection.objects.filter(
        confirmation_status="PENDING"
    ).select_related(
        "student",
        "attempt"
    ).order_by(
        "-detected_at"
    ).first()

    if not inspection:

        return Response({
            "success": False,
            "message":
                "No pending AI inspections"
        })

    student = inspection.student

    # =====================================================
    # STUDENT ID PHOTO
    # =====================================================

    student_photo = None

    if student.id_front:

        student_photo = (
            request.build_absolute_uri(
                student.id_front.url
            )
        )

    # =====================================================
    # AI SCREENSHOT
    # =====================================================

    screenshot_url = None

    if inspection.screenshot:

        screenshot_url = (
            request.build_absolute_uri(
                inspection.screenshot.url
            )
        )

    # =====================================================
    # RESPONSE
    # =====================================================

    return Response({

        "success": True,

        "inspection": {

            "id":
                inspection.id,

            "student": {

                "student_number":
                    student.student_number,

                "name":
                    student.full_name,

                "college":
                    student.college,

                "photo":
                    student_photo
            },

            "ai_result":
                inspection.ai_result,

            "violations":
                inspection.violations,

            "screenshot":
                screenshot_url,

            "confirmation_status":
                inspection.confirmation_status,

            "detected_at":
                inspection.detected_at
        }

    })


# =========================================================
# OSA REVIEW AI INSPECTION
# =========================================================
#
# Expected:
#
# {
#     "inspection_id": 1,
#     "decision": "YES"
# }
#
# YES:
# AI was correct -> confirmed violation
#
# NO:
# AI was wrong -> false detection
#
# =========================================================

@api_view(["POST"])
def review_ai_inspection(request):

    inspection_id = request.data.get(
        "inspection_id"
    )

    decision = request.data.get(
        "decision"
    )

    if decision:

        decision = (
            str(decision)
            .strip()
            .upper()
        )

    # =====================================================
    # VALIDATION
    # =====================================================

    if not inspection_id:

        return Response(
            {
                "success": False,
                "message":
                    "inspection_id is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if decision not in [
        "YES",
        "NO"
    ]:

        return Response(
            {
                "success": False,
                "message":
                    "decision must be YES or NO"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # =====================================================
    # FIND INSPECTION
    # =====================================================

    try:

        inspection = (
            AIInspection.objects
            .select_related(
                "student",
                "attempt"
            )
            .get(
                id=inspection_id
            )
        )

    except AIInspection.DoesNotExist:

        return Response(
            {
                "success": False,
                "message":
                    "AI inspection not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # =====================================================
    # ALREADY REVIEWED
    # =====================================================

    if (
        inspection.confirmation_status
        != "PENDING"
    ):

        return Response(
            {
                "success": False,
                "message":
                    "Inspection has already been reviewed",
                "confirmation_status":
                    inspection.confirmation_status
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    student = inspection.student
    attempt = inspection.attempt

    # =====================================================
    # OSA PRESSES YES
    # =====================================================
    #
    # YES means:
    # "Yes, this really is a violation."
    #
    # =====================================================

    if decision == "YES":

        inspection.confirmation_status = (
            "CONFIRMED"
        )

        inspection.reviewed_at = (
            timezone.now()
        )

        inspection.save()

        # ---------------------------------------------
        # UPDATE ACCESS ATTEMPT
        # ---------------------------------------------

        violation_text = ", ".join(
            inspection.violations
        )

        if attempt:

            attempt.has_violation = True

            attempt.violation_type = (
                violation_text
            )

            # Violation confirmed -> do not open gate.
            attempt.gate_opened = False

            attempt.save()

        # ---------------------------------------------
        # CREATE INDIVIDUAL VIOLATION RECORDS
        # ---------------------------------------------

        for violation_name in (
            inspection.violations
        ):

            Violation.objects.create(
                student=student,
                violation_type=
                    violation_name,
                status="Unread"
            )

        # ---------------------------------------------
        # GENERAL VIOLATION REPORT
        # ---------------------------------------------

        ViolationReport.objects.create(

            student=student,

            violation_type=
                violation_text,

            confirmed_entry=False,

            sent_to_osa=True
        )

        print("")
        print(
            "========================================"
        )

        print(
            "OSA CONFIRMED VIOLATION"
        )

        print(
            "Student:",
            student.student_number
        )

        print(
            "Violations:",
            inspection.violations
        )

        print(
            "========================================"
        )

        return Response({

            "success": True,

            "decision":
                "YES",

            "confirmation_status":
                "CONFIRMED",

            "message":
                "Violation confirmed by OSA"
        })

    # =====================================================
    # OSA PRESSES NO
    # =====================================================
    #
    # NO means:
    # "No, AI detected this incorrectly."
    #
    # =====================================================

    inspection.confirmation_status = (
        "REJECTED"
    )

    inspection.reviewed_at = (
        timezone.now()
    )

    inspection.save()

    if attempt:

        attempt.has_violation = False

        attempt.violation_type = ""

        # False positive -> student can proceed.
        attempt.gate_opened = True

        attempt.save()

    print("")
    print(
        "========================================"
    )

    print(
        "OSA REJECTED AI VIOLATION"
    )

    print(
        "Student:",
        student.student_number
    )

    print(
        "False detection - student cleared."
    )

    print(
        "========================================"
    )

    return Response({

        "success": True,

        "decision":
            "NO",

        "confirmation_status":
            "REJECTED",

        "message":
            "AI detection rejected by OSA"
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