from rest_framework import serializers

from products.cyed.school.models import Notice, SchoolProfile


class SchoolProfileSerializer(serializers.ModelSerializer):
    has_logo = serializers.ReadOnlyField()

    class Meta:
        model = SchoolProfile
        exclude = ["logo_bytes"]
        read_only_fields = ["id", "tenant_id", "logo_content_type", "created_at", "updated_at"]


class NoticeSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = "__all__"
        # `posted_by` is stamped from the token: a notice attributed to someone
        # who did not write it is worse than an unattributed one.
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "posted_by"]

    def get_is_active(self, obj) -> bool:
        return obj.is_active()

    def validate(self, attrs):
        starts = attrs.get("starts_on", getattr(self.instance, "starts_on", None))
        ends = attrs.get("ends_on", getattr(self.instance, "ends_on", None))
        if starts and ends and ends < starts:
            raise serializers.ValidationError(
                {"ends_on": "A notice cannot come down before it goes up."}
            )
        years = attrs.get("year_levels", getattr(self.instance, "year_levels", "") or "")
        for part in [y.strip() for y in years.split(",") if y.strip()]:
            if not part.isdigit():
                raise serializers.ValidationError({
                    "year_levels": (
                        f"'{part}' is not a year level. Use digits separated by commas, "
                        f"e.g. '9,10'. Foundation is 0."
                    )
                })
        return attrs
