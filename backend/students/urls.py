from django.urls import path
from .views import StudentList, LoginView
from .dashboard import dashboard_data

urlpatterns = [
    path("", StudentList.as_view(), name="student-list"),
    path("login/", LoginView.as_view(), name="login"),
    path("dashboard/", dashboard_data, name="dashboard"),
]