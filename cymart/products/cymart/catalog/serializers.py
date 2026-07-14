from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    full_path = serializers.CharField(read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "parent",
            "slug",
            "name_en",
            "name_ar",
            "description_en",
            "description_ar",
            "image_url",
            "meta_title",
            "meta_description",
            "attributes",
            "filters",
            "is_restricted",
            "restriction_reason",
            "allowed_country_codes",
            "min_age",
            "requires_prescription",
            "is_controlled_substance",
            "is_active",
            "display_order",
            "full_path",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
