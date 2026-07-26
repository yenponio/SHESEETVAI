from django.urls import path
from .views import StudentList, LoginView

urlpatterns = [
    path("", StudentList.as_view(), name="student-list"),
    path("login/", LoginView.as_view(), name="login"),
]