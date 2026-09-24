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
    GateController,
    GateCycle,
)

from .serializers import StudentSerializer
from .gate import (GateError, queue_attempt, save_violation, lock_database,
                   cancelled_attempt, CANCELLED_OUTCOMES, bridge_running)


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

            # Valid ID reserves a closed gate cycle; only OSA can queue OPEN.
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

    if result_status in ("VIOLATION", "PASS"):

        # AI result is only suspected.
        # OSA must confirm before it becomes a real violation.
        inspection = AIInspection.objects.create(
            student=student,
            attempt=attempt,
            ai_result=result_status,
            violations=violations if result_status == "VIOLATION" else [],
            screenshot=screenshot,
            confirmation_status="PENDING"
        )

        print("")
        print("========================================")
        print("AI RESULT RECEIVED BY DJANGO:", result_status)
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
                    "AI result sent to OSA "
                    "for confirmation"
                ),
                "inspection_id": inspection.id,
                "confirmation_status": (
                    inspection.confirmation_status
                )
            },
            status=status.HTTP_201_CREATED
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
# Compatibility wrapper for internal callers; all finalization guards live in
# gate.save_violation. The OSA review endpoint never calls this function.
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

    if decision not in ("YES", "NO", "DENY"):
        return Response({"success": False, "message": "decision must be YES, NO or DENY"}, status=400)
    try:
        inspection = AIInspection.objects.select_related("attempt", "student").get(pk=inspection_id)
    except (AIInspection.DoesNotExist, ValueError, TypeError):
        return Response({"success": False, "message": "AI inspection not found"}, status=404)
    # Serialized by the controller write lock; retries cannot authorize another OPEN.
    if inspection.confirmation_status != "PENDING":
        return Response({"success": False, "message": "Inspection has already been reviewed",
                         "confirmation_status": inspection.confirmation_status}, status=400)
    attempt = inspection.attempt
    cycle = GateCycle.objects.filter(attempt=attempt).first() if attempt else None
    controller = GateController.objects.get(pk=1)
    if (not cycle or cycle.phase != "WAITING_OSA" or cycle.outcome != "PENDING" or
            controller.active_cycle_id != cycle.pk or attempt.entered or attempt.gate_opened):
        return Response({"success": False, "message": "Attempt is no longer awaiting OSA review"}, status=409)
    if decision != "DENY" and (not controller.enabled or not controller.ready or
                               not bridge_running(controller)):
        return Response({"success": False, "code": "GATE_OFFLINE",
                         "message": "Gate is offline. Decision not saved; ask the operator for assistance."}, status=409)
    inspection.confirmation_status = {
        "YES": "CONFIRMED_ALLOW", "NO": "REJECTED", "DENY": "CONFIRMED_DENY",
    }[decision]
    inspection.reviewed_at = timezone.now()
    inspection.save(update_fields=["confirmation_status", "reviewed_at"])
    attempt.has_violation = decision != "NO"
    attempt.violation_type = (", ".join(inspection.violations) or "OSA-confirmed dress-code violation") if decision != "NO" else ""
    attempt.save(update_fields=["has_violation", "violation_type"])
    if decision == "DENY":
        cycle.phase, cycle.outcome = "CLOSED", "DENIED"
        cycle.message = "OSA denied entry. No official offense recorded."
        controller.active_cycle = None
        controller.save(update_fields=["active_cycle"])
    else:
        cycle.phase = "QUEUED"
        cycle.message = "OSA authorized opening; waiting for Uno acknowledgement."
    cycle.save(update_fields=["phase", "outcome", "message"])
    # No offense finalization here: only sensor-confirmed ENTERED can do that.
    return Response({"success": True, "decision": decision,
                     "attempt_id": attempt.pk,
                     "confirmation_status": inspection.confirmation_status,
                     "gate_opened": False, "entered": False,
                     "message": cycle.message})


# =========================================================
# CONFIRM ENTRY
# =========================================================
#
# Browser entry assertions are forbidden. The local Uno bridge processes
# HC-SR04 events through gate.apply_event instead.
#
# =========================================================

@api_view(["POST"])
def confirm_entry(request):
    return Response({
        "success": False,
        "message": "Entry confirmation is accepted only from the local USB gate bridge."
    }, status=403)
