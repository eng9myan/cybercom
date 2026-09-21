from rest_framework import serializers

from products.cycom.appraisals.models import Appraisal


class AppraisalSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.__str__", read_only=True)

    class Meta:
        model = Appraisal
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
