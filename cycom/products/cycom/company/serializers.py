from rest_framework import serializers

from products.cycom.company.models import Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
