from rest_framework import serializers

from .models import VendorPerformance, VendorQualification


class VendorQualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorQualification
        fields = [
            "id",
            "tenant_id",
            "vendor_id",
            "qualification_type",
            "expiry_date",
            "document_ref",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VendorPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorPerformance
        fields = [
            "id",
            "tenant_id",
            "vendor_id",
            "evaluation_period",
            "delivery_score",
            "quality_score",
            "price_score",
            "overall_score",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
