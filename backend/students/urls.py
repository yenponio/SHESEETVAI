from django.urls import path
from .views import StudentList, LoginView
from .dashboard import dashboard_data
from .views import records_data
from .records import school_records
urlpatterns = [
    path("", StudentList.as_view(), name="student-list"),
    path("login/", LoginView.as_view(), name="login"),
    path("dashboard/", dashboard_data, name="dashboard"),
    path("records/",records_data,name="records"),
    path("records/<str:school>/",school_records,name="school-records"),
]