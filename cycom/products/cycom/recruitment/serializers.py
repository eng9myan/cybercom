from rest_framework import serializers

from products.cycom.recruitment.models import Applicant


class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicant
        fields = [
            "id", "name", "email", "phone", "job_title", "stage",
            "priority", "source", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
