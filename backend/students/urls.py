from django.urls import path
from .views import StudentList
from .dashboard import dashboard_data

urlpatterns = [
    path("", StudentList.as_view(), name="student-list"),
    path("dashboard/", dashboard_data, name="dashboard"),
]