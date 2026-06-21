from rest_framework import serializers
from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id", "name", "slug", "domain", "tier", "status",
            "country_code", "timezone", "locale", "activated_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "activated_at", "created_at", "updated_at"]
