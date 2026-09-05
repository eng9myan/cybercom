from rest_framework import serializers

from platform.canonical.models import LayoutTemplate, VerticalFlavor


class LayoutTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayoutTemplate
        fields = ["id", "flavor_key", "name", "route", "slots", "roles", "device"]


class VerticalFlavorSerializer(serializers.ModelSerializer):
    """Read-only — the catalog is edited via flavor-registry.yaml / a
    *.flavor.yaml pack and re-synced, never PATCHed directly (N.6)."""

    layout_templates = serializers.SerializerMethodField()

    class Meta:
        model = VerticalFlavor
        fields = [
            "id",
            "key",
            "name",
            "version",
            "status",
            "feature_flag",
            "owner",
            "certified_at",
            "definition",
            "layout_templates",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_layout_templates(self, obj: VerticalFlavor):
        qs = LayoutTemplate.objects.filter(flavor_key=obj.key)
        return LayoutTemplateSerializer(qs, many=True).data
