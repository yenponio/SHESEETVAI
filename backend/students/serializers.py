from rest_framework import serializers
from .models import Student
from .offenses import offense_counts

class StudentSerializer(serializers.ModelSerializer):
    offense_counts = serializers.SerializerMethodField()

    def get_offense_counts(self, student):
        return offense_counts(student.pk)

    class Meta:
        model = Student
        fields = "__all__"