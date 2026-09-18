import json

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction

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
from .gate import (GateError, queue_attempt, save_violation, lock_database,
                   cancelled_attempt, CANCELLED_OUTCOMES)


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
        ).order_by("-scan_time").first()

        if not attempt:
            return Response({"success": False})

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
            student = Student.objects.get(
                barcode=barcode
            )

            print(
                "STUDENT FOUND:",
                student.student_number,
                student.full_name
            )

            # Valid ID queues one exact-attempt command when the USB bridge is enabled.
            try:
                attempt, hardware_gate = queue_attempt(student)
            except GateError as error:
                return Response({"success": False, "message": str(error),
                                 "code": error.code}, status=409)

            photo = None

            if student.id_front:
                photo = request.build_absolute_uri(
                    student.id_front.url
                )

                print("ID PHOTO:", photo)

            else:
                print(
                    "NO ID PHOTO FOR:",
                    student.student_number
                )

            return Response(
                {
                    "success": True,
                    "student": {
                        "id": student.student_number,
                        "name": student.full_name,
                        "college": student.college,
                        "photo": photo
                    },
                    "attempt_id": attempt.id,
                    "hardware_gate": hardware_gate
                },
                status=status.HTTP_200_OK
            )

        except Student.DoesNotExist:
            print("BARCODE NOT FOUND:", barcode)

            return Response(
                {
                    "success": False,
                    "message": "Barcode not registered",
                    "barcode": barcode
                },
                status=status.HTTP_404_NOT_FOUND
            )


# =========================================================
# RECEIVE AI RESULT
# =========================================================

@api_view(["POST"])
@transaction.atomic
def receive_ai_result(request):
    lock_database()
    student_number = request.data.get("student_number")
    result_status = request.data.get("status")
    violations = request.data.get("violations", [])
    attempt_id = request.data.get("attempt_id")
    screenshot = request.FILES.get("screenshot")

    if not student_number:
        return Response(
            {
                "success": False,
                "message": "student_number is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Normalize status
    if result_status:
        result_status = str(
            result_status
        ).strip().upper()

    # Normalize violations
    if isinstance(violations, str):
        try:
            violations = json.loads(violations)

        except json.JSONDecodeError:
            violations = [
                item.strip()
                for item in violations.split(",")
                if item.strip()
            ]

    if not isinstance(violations, list):
        violations = []

    # Find student
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

    # Bind every result to the exact scan; never guess the latest student attempt.
    try:
        if isinstance(attempt_id, bool) or not str(attempt_id).isdigit():
            raise ValueError
        attempt = AccessAttempt.objects.get(id=int(attempt_id), student=student)
    except (ValueError, TypeError, AccessAttempt.DoesNotExist):
        return Response({"success": False, "message": "A valid attempt_id for this student is required"}, status=400)
    if cancelled_attempt(attempt.pk):
        return Response({"success": True, "ignored": True, "message": "Entry was cancelled"})
    if AIInspection.objects.filter(attempt=attempt).exists():
        return Response({"success": True, "ignored": True, "message": "Inspection already received"})

    # =====================================================
    # AI RESULT = VIOLATION
    # =====================================================

    if result_status == "VIOLATION":

        # AI result is only suspected.
        # OSA must confirm before it becomes a real violation.
        inspection = AIInspection.objects.create(
            student=student,
            attempt=attempt,
            ai_result="VIOLATION",
            violations=violations,
            screenshot=screenshot,
            confirmation_status="PENDING"
        )

        print("")
        print("========================================")
        print("AI VIOLATION RECEIVED BY DJANGO")
        print("Student:", student.student_number)
        print("Inspection ID:", inspection.id)
        print("Violations:", violations)
        print("Screenshot:", inspection.screenshot)
        print("OSA Status: PENDING")
        print("========================================")

        return Response(
            {
                "success": True,
                "message": (
                    "Violation sent to OSA "
                    "for confirmation"
                ),
                "inspection_id": inspection.id,
                "confirmation_status": (
                    inspection.confirmation_status
                )
            },
            status=status.HTTP_201_CREATED
        )

    # =====================================================
    # AI RESULT = PASS
    # =====================================================

    elif result_status == "PASS":
        attempt.has_violation = False
        attempt.violation_type = ""
        if not hasattr(attempt, "gate_cycle"):
            attempt.gate_opened = True
        attempt.save()

        print("")
        print("========================================")
        print("AI PASS RECEIVED BY DJANGO")
        print("Student:", student.student_number)
        print("========================================")

        return Response(
            {
                "success": True,
                "message": "Student passed dress code",
                "status": "PASS"
            },
            status=status.HTTP_200_OK
        )

    return Response(
        {
            "success": False,
            "message": "Status must be PASS or VIOLATION"
        },
        status=status.HTTP_400_BAD_REQUEST
    )


# =========================================================
# GET LATEST PENDING OSA INSPECTION
# =========================================================

@api_view(["GET"])
def latest_pending_inspection(request):
    inspection = AIInspection.objects.filter(
        confirmation_status="PENDING",
        attempt__isnull=False,
    ).exclude(attempt__gate_cycle__outcome__in=CANCELLED_OUTCOMES).select_related(
        "student",
        "attempt"
    ).order_by("-detected_at").first()

    if not inspection:
        return Response({
            "success": False,
            "message": "No pending AI inspections"
        })

    student = inspection.student

    student_photo = None

    if student.id_front:
        student_photo = request.build_absolute_uri(
            student.id_front.url
        )

    screenshot_url = None

    if inspection.screenshot:
        screenshot_url = request.build_absolute_uri(
            inspection.screenshot.url
        )

    return Response({
        "success": True,
        "inspection": {
            "id": inspection.id,
            "attempt_id": inspection.attempt_id,
            "student": {
                "student_number": student.student_number,
                "name": student.full_name,
                "college": student.college,
                "photo": student_photo
            },
            "ai_result": inspection.ai_result,
            "violations": inspection.violations,
            "screenshot": screenshot_url,
            "confirmation_status": (
                inspection.confirmation_status
            ),
            "detected_at": inspection.detected_at
        }
    })


# =========================================================
# SAVE CONFIRMED VIOLATION IF READY
# =========================================================
#
# A violation becomes permanent ONLY when:
#
# 1. OSA confirmed it.
# 2. Student actually entered campus.
#
# This function can safely be called from both:
# - OSA confirmation
# - ultrasonic entry confirmation
#
# =========================================================

def save_confirmed_violation_if_ready(inspection):
    return save_violation(inspection.pk)


# =========================================================
# OSA REVIEW AI INSPECTION
# =========================================================

@api_view(["POST"])
@transaction.atomic
def review_ai_inspection(request):
    lock_database()
    inspection_id = request.data.get("inspection_id")
    decision = request.data.get("decision")

    if decision:
        decision = str(
            decision
        ).strip().upper()

    if not inspection_id:
        return Response(
            {
                "success": False,
                "message": "inspection_id is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if decision not in ["YES", "NO"]:
        return Response(
            {
                "success": False,
                "message": "decision must be YES or NO"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Find inspection
    try:
        inspection = AIInspection.objects.select_related(
            "student",
            "attempt"
        ).get(id=inspection_id)

    except AIInspection.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "AI inspection not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    if cancelled_attempt(inspection.attempt_id):
        return Response({"success": False, "message": "This student did not complete entry"}, status=409)

    # Prevent double review
    if inspection.confirmation_status != "PENDING":
        return Response(
            {
                "success": False,
                "message": (
                    "Inspection has already been reviewed"
                ),
                "confirmation_status": (
                    inspection.confirmation_status
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    student = inspection.student
    attempt = inspection.attempt

    # =====================================================
    # OSA PRESSES YES
    # =====================================================

    if decision == "YES":
        inspection.confirmation_status = "CONFIRMED"
        inspection.reviewed_at = timezone.now()
        inspection.save()

        violation_text = ", ".join(
            inspection.violations
        )

        if attempt:
            attempt.has_violation = True
            attempt.violation_type = violation_text

            # A violation does NOT block campus entry.
            if not hasattr(attempt, "gate_cycle"):
                attempt.gate_opened = True
            attempt.save()

        # This only saves permanently if the student
        # has already entered campus.
        save_confirmed_violation_if_ready(
            inspection
        )

        print("")
        print("========================================")
        print("OSA CONFIRMED VIOLATION")
        print("Student:", student.student_number)
        print("Violations:", inspection.violations)
        print("========================================")

        return Response({
            "success": True,
            "decision": "YES",
            "confirmation_status": "CONFIRMED",
            "message": "Violation confirmed by OSA"
        })

    # =====================================================
    # OSA PRESSES NO
    # =====================================================

    inspection.confirmation_status = "REJECTED"
    inspection.reviewed_at = timezone.now()
    inspection.save()

    if attempt:
        attempt.has_violation = False
        attempt.violation_type = ""
        if not hasattr(attempt, "gate_cycle"):
            attempt.gate_opened = True
        attempt.save()

    print("")
    print("========================================")
    print("OSA REJECTED AI VIOLATION")
    print("Student:", student.student_number)
    print("False detection - student cleared.")
    print("========================================")

    return Response({
        "success": True,
        "decision": "NO",
        "confirmation_status": "REJECTED",
        "message": "AI detection rejected by OSA"
    })


# =========================================================
# CONFIRM ENTRY
# =========================================================
#
# Eventually this endpoint will be triggered when the
# Arduino/HC-SR04 confirms that the student actually
# passed through the gate.
#
# =========================================================

@api_view(["POST"])
def confirm_entry(request):
    return Response({
        "success": False,
        "message": "Entry confirmation is accepted only from the local USB gate bridge."
    }, status=403)
