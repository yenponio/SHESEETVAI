from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Student, OSAAccount
from .serializers import StudentSerializer


class StudentList(generics.ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        account = OSAAccount.objects.filter(
            email=email,
            password=password
        ).first()

        if account:
            return Response(
                {
                    "success": True,
                    "message": "Login successful"
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "success": False,
                "message": "Invalid email or password"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )