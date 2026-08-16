from django.urls import path
from .views import StudentList, LoginView, BarcodeScanView, LatestScanView, receive_ai_result
from .dashboard import dashboard_data
from .views import records_data
from .records import school_records
from .views import confirm_entry
urlpatterns = [
    path("", StudentList.as_view(), name="student-list"),
    path("login/", LoginView.as_view(), name="login"),
    path("dashboard/", dashboard_data, name="dashboard"),
    path("records/",records_data,name="records"),
    path("records/<str:school>/",school_records,name="school-records"),
    path("scan/",BarcodeScanView.as_view()),
    path("scan/latest/",LatestScanView.as_view()),
    path("ai-result/",receive_ai_result),
    path("confirm-entry/",confirm_entry),
]