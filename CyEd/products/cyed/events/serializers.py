from rest_framework import serializers

from products.cyed.events.models import Event, EventParticipation


class EventSerializer(serializers.ModelSerializer):
    is_excursion = serializers.SerializerMethodField()
    invited_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "hardship_waivers"]

    def get_is_excursion(self, obj) -> bool:
        return obj.is_excursion()

    def get_invited_count(self, obj) -> int:
        return obj.participations.exclude(status="declined").count()

    def validate(self, attrs):
        charging = attrs.get("charge_students", getattr(self.instance, "charge_students", False))
        cost = attrs.get("cost", getattr(self.instance, "cost", 0))
        if charging and not cost:
            raise serializers.ValidationError({
                "cost": (
                    "Set a cost, or turn off charging — otherwise every child gets a "
                    "nil invoice that has to be chased and cancelled."
                )
            })
        departs = attrs.get("departs_at", getattr(self.instance, "departs_at", None))
        returns = attrs.get("returns_at", getattr(self.instance, "returns_at", None))
        if departs and returns and returns <= departs:
            raise serializers.ValidationError(
                {"returns_at": "The excursion cannot return before it departs."}
            )
        return attrs


class EventParticipationSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    cleared = serializers.SerializerMethodField()
    consented = serializers.SerializerMethodField()
    paid = serializers.SerializerMethodField()

    class Meta:
        model = EventParticipation
        fields = "__all__"
        # Consent, payment and the waiver all move through actions or the
        # documents behind them — a PATCHable `consent_given` would let a child
        # be cleared onto a bus without a signed permission.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "consent_document", "consent_given_at", "invoice",
            "fee_waived", "waiver_reason",
        ]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip() if obj.student_id else ""

    def get_cleared(self, obj) -> bool:
        return obj.is_cleared()

    def get_consented(self, obj) -> bool:
        return obj.is_consented()

    def get_paid(self, obj) -> bool:
        return obj.is_paid()
