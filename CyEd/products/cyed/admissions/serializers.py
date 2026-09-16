from rest_framework import serializers

from products.cyed.admissions.models import (
    Application,
    ApplicationDocument,
    CatchmentZone,
    Offer,
)


class CatchmentZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatchmentZone
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def _string_list(self, value, field):
        if value in (None, ""):
            return []
        if not isinstance(value, list) or not all(isinstance(v, (str, int)) for v in value):
            raise serializers.ValidationError(f"{field} must be a list of strings.")
        return [str(v).strip() for v in value if str(v).strip()]

    def validate_postcodes(self, value):
        return self._string_list(value, "postcodes")

    def validate_suburbs(self, value):
        return self._string_list(value, "suburbs")

    def validate(self, attrs):
        postcodes = attrs.get("postcodes", getattr(self.instance, "postcodes", []) or [])
        suburbs = attrs.get("suburbs", getattr(self.instance, "suburbs", []) or [])
        if not postcodes and not suburbs:
            raise serializers.ValidationError(
                "A zone with no suburbs and no postcodes matches nothing, so every "
                "address would read as out of catchment. Give it at least one."
            )
        return attrs


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = ApplicationDocument
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "received_by"]


class OfferSerializer(serializers.ModelSerializer):
    has_expired = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = "__all__"
        # The response is set through accept/decline so expiry and the
        # application's own status cannot be bypassed by a direct PATCH.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "response", "responded_on", "responded_by", "decline_reason",
        ]

    def get_has_expired(self, obj) -> bool:
        return obj.has_expired()


class ApplicationSerializer(serializers.ModelSerializer):
    offers = OfferSerializer(many=True, read_only=True)
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    outstanding_documents = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "enrolled_student_id", "created_at", "updated_at"]

    def get_outstanding_documents(self, obj) -> list:
        return [d.kind for d in obj.documents.all() if not d.is_received]
