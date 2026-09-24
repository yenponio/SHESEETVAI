"""Read-only UI projections. Never authorize movement, record offenses or send mail."""
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from .gate import bridge_running, cycle_status
from .models import AccessAttempt, AIInspection, EntryLog, GateController, GateCycle, ViolationEmail
from .offenses import offense_counts


def page_data(queryset, request, serialize):
    page = Paginator(queryset, 25).get_page(request.GET.get("page", 1))
    return {"results": [serialize(row) for row in page], "total": page.paginator.count,
            "page": page.number, "pages": page.paginator.num_pages}


def audit_row(attempt):
    inspections = list(attempt.ai_inspections.all())
    inspection = inspections[-1] if inspections else None
    cycle = getattr(attempt, "gate_cycle", None)
    return {"id": attempt.pk, "student_number": attempt.student.student_number,
            "name": attempt.student.full_name, "college": attempt.student.college,
            "scan_time": timezone.localtime(attempt.scan_time).isoformat(),
            "ai_result": inspection.ai_result if inspection else None,
            "osa_decision": inspection.confirmation_status if inspection else None,
            "gate_phase": cycle.phase if cycle else None,
            "gate_event": cycle.message if cycle else None,
            "outcome": cycle.outcome if cycle else None,
            "gate_opened": attempt.gate_opened, "entered": attempt.entered}


@require_GET
@never_cache
def audit_data(request):
    rows = AccessAttempt.objects.select_related("student", "gate_cycle").prefetch_related("ai_inspections").order_by("-scan_time", "-pk")
    if request.GET.get("student_number"):
        rows = rows.filter(student__student_number=request.GET["student_number"])
    if request.GET.get("q"):
        rows = rows.filter(Q(student__full_name__icontains=request.GET["q"]) | Q(student__student_number__icontains=request.GET["q"]))
    outcome = request.GET.get("outcome")
    if outcome:
        rows = rows.filter(gate_cycle__outcome=outcome)
    result = page_data(rows, request, audit_row)
    result["entered_total"] = rows.filter(entered=True).count()
    return JsonResponse(result)


@require_GET
@never_cache
def notification_data(request):
    rows = ViolationEmail.objects.select_related("report__student").order_by("-created_at", "-pk")
    if request.GET.get("q"):
        rows = rows.filter(Q(report__student__full_name__icontains=request.GET["q"]) | Q(report__student__student_number__icontains=request.GET["q"]))
    if request.GET.get("status"):
        rows = rows.filter(status=request.GET["status"])
    def serialize(notice):
        student = notice.report.student
        return {"id": notice.pk, "student_number": student.student_number,
                "name": student.full_name, "email": student.email,
                "violation": notice.report.violation_type, **offense_counts(student.pk),
                "created_at": timezone.localtime(notice.created_at).isoformat(),
                "sent_at": timezone.localtime(notice.sent_at).isoformat() if notice.sent_at else None,
                "status": notice.status, "error": notice.error}
    return JsonResponse(page_data(rows, request, serialize))


@require_GET
@never_cache
def system_status(request):
    controller = GateController.objects.filter(pk=1).first()
    today = timezone.localdate()
    connected = bridge_running(controller) if controller else False
    active = cycle_status(controller.active_cycle_id) if controller and controller.active_cycle_id else None
    return JsonResponse({
        "arduino_connected": connected, "gate_ready": bool(connected and controller.ready),
        "active_cycle": active,
        "scans_today": AccessAttempt.objects.filter(scan_time__date=today).count(),
        "entries_today": EntryLog.objects.filter(entry_time__date=today).count(),
        "denied_today": GateCycle.objects.filter(outcome="DENIED", attempt__scan_time__date=today).count(),
        "smtp_configured": bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD and settings.DEFAULT_FROM_EMAIL),
        "timezone": settings.TIME_ZONE,
        "recent_detections": [{"id": item.pk, "student_number": item.student.student_number,
            "name": item.student.full_name, "ai_result": item.ai_result,
            "decision": item.confirmation_status, "detected_at": timezone.localtime(item.detected_at).isoformat()}
            for item in AIInspection.objects.select_related("student").order_by("-detected_at", "-pk")[:5]],
    })
