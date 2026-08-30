from django.urls import path

from .views import (
    StudentList,
    LoginView,
    BarcodeScanView,
    LatestScanView,
    receive_ai_result,
    records_data,
    confirm_entry,
    latest_pending_inspection,
    review_ai_inspection,
)

from .dashboard import dashboard_data
from .records import school_records


urlpatterns = [

    # =====================================================
    # STUDENTS
    # =====================================================

    path(
        "",
        StudentList.as_view(),
        name="student-list"
    ),


    # =====================================================
    # OSA LOGIN
    # =====================================================

    path(
        "login/",
        LoginView.as_view(),
        name="login"
    ),


    # =====================================================
    # DASHBOARD
    # =====================================================

    path(
        "dashboard/",
        dashboard_data,
        name="dashboard"
    ),


    # =====================================================
    # RECORDS
    # =====================================================

    path(
        "records/",
        records_data,
        name="records"
    ),

    path(
        "records/<str:school>/",
        school_records,
        name="school-records"
    ),


    # =====================================================
    # BARCODE SCANNER
    # =====================================================

    path(
        "scan/",
        BarcodeScanView.as_view(),
        name="barcode-scan"
    ),

    path(
        "scan/latest/",
        LatestScanView.as_view(),
        name="latest-scan"
    ),


    # =====================================================
    # AI RESULT
    # =====================================================
    #
    # camera_server.py sends the AI result + screenshot here
    #
    # =====================================================

    path(
        "ai-result/",
        receive_ai_result,
        name="ai-result"
    ),


    # =====================================================
    # OSA - GET PENDING AI VIOLATION
    # =====================================================
    #
    # ConfirmationPage.jsx will read this endpoint.
    #
    # =====================================================

    path(
        "ai-inspection/pending/",
        latest_pending_inspection,
        name="latest-pending-inspection"
    ),


    # =====================================================
    # OSA - YES / NO DECISION
    # =====================================================
    #
    # YES = real violation
    # NO  = false AI detection
    #
    # =====================================================

    path(
        "ai-inspection/review/",
        review_ai_inspection,
        name="review-ai-inspection"
    ),


    # =====================================================
    # ENTRY CONFIRMATION
    # =====================================================

    path(
        "confirm-entry/",
        confirm_entry,
        name="confirm-entry"
    ),

]