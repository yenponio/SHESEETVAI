"""Shared source for Records and Dashboard: one row per violation report."""
from django.http import JsonResponse
from django.db.models import Count
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .models import ViolationReport

SCHOOLS = {
    "SEA": "School of Engineering and Architecture",
    "SOC": "School of Computing",
    "SHTM": "School of Hospitality and Tourism Management",
    "SBA": "School of Business and Accountancy",
    "SED": "School of Education",
    "CCJEF": "College of Criminal Justice Education and Forensics",
    "SAS": "School of Arts and Sciences",
    "SNAMS": "School of Nursing and Allied Medical Sciences",
}


def college_code(value):
    value = value.strip()
    if value.upper() == "CCJF":
        return "CCJEF"
    for code, name in SCHOOLS.items():
        if value.casefold() in (code.casefold(), name.casefold()):
            return code
    return value or "Unknown"


def violation_records(school=None, request=None):
    # Do not merge the per-type Violation table or infer reports from scans.
    reports = ViolationReport.objects.filter(confirmed_entry=True).select_related("student", "inspection", "email_notification").order_by("-report_time", "-pk")
    totals = dict(ViolationReport.objects.filter(confirmed_entry=True).values("student_id").annotate(total=Count("pk")).values_list("student_id", "total"))
    records = []
    for report in reports:
        student = report.student
        college = college_code(student.college)
        if school is not None and college.casefold() != college_code(school).casefold():
            continue
        occurred = timezone.localtime(report.report_time)
        screenshot = report.inspection.screenshot if report.inspection else None
        evidence_url = screenshot.url if screenshot else None
        if evidence_url and request is not None:
            evidence_url = request.build_absolute_uri(evidence_url)
        records.append({
            "total_minor_offenses": totals[student.pk],
            "equivalent_major_offenses": totals[student.pk] // 3,
            "osa_decision": report.inspection.confirmation_status if report.inspection else None,
            "confirmed_entry": report.confirmed_entry,
            "email_status": getattr(report, "email_notification", None).status if getattr(report, "email_notification", None) else None,
            "evidence_image": evidence_url,
            "id": report.pk,
            "studentNumber": student.student_number,
            "name": student.full_name,
            "college": college,
            "collegeName": student.college,
            "violationType": report.violation_type,
            "reportedAt": occurred.isoformat(),
            "date": occurred.strftime("%Y-%m-%d"),
            "time": occurred.strftime("%H:%M:%S"),
        })
    return records


@never_cache
def records_data(request):
    records = violation_records(request=request)
    schools = sorted(set(SCHOOLS) | {record["college"] for record in records})
    return JsonResponse({"records": records, "total": len(records), "schools": schools})


@never_cache
def school_records(request, school):
    records = violation_records(school, request=request)
    return JsonResponse({"school": college_code(school), "records": records, "total": len(records)})
