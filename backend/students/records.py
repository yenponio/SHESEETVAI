from django.http import JsonResponse

from .models import Student, ViolationReport



def school_records(request, school):

    students = Student.objects.filter(
        college__iexact=school
    )


    records = []


    for student in students:

        violations = ViolationReport.objects.filter(
            student=student
        ).count()


        if violations > 0:

            records.append({

                "studentNumber": student.student_number,

                "name": student.full_name,

                "college": student.college,

                "violations": violations,

                "status": "Violation"

            })


    return JsonResponse({

        "school": school.upper(),

        "records": records

    })