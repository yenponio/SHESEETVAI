"""One official report is one minor offense, regardless of clothing types.

Historical per-type Violation rows are retained; counting those rows would
inflate existing multi-type offenses. Records and Dashboard already use reports.
"""
from .models import ViolationReport


def offense_counts(student_id):
    total = ViolationReport.objects.filter(student_id=student_id, confirmed_entry=True).count()
    return {"total_minor_offenses": total, "equivalent_major_offenses": total // 3}
