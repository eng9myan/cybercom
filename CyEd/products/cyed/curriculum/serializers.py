from rest_framework import serializers

from core.serializers import ReadOnlyModelSerializer
from products.cyed.curriculum.models import (
    AchievementStandard,
    CrossCurriculumPriority,
    CurriculumOutcome,
    GeneralCapability,
    MracImportRun,
)


class GeneralCapabilitySerializer(ReadOnlyModelSerializer):
    """Read-only: capabilities come from the ACARA MRAC export, not the UI."""

    class Meta:
        model = GeneralCapability
        fields = "__all__"


class CrossCurriculumPrioritySerializer(ReadOnlyModelSerializer):
    class Meta:
        model = CrossCurriculumPriority
        fields = "__all__"


class AchievementStandardSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = AchievementStandard
        fields = "__all__"


class MracImportRunSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = MracImportRun
        fields = "__all__"


class CurriculumOutcomeSerializer(serializers.ModelSerializer):
    general_capability_codes = serializers.SerializerMethodField()
    cross_curriculum_priority_codes = serializers.SerializerMethodField()
    elaboration_count = serializers.SerializerMethodField()

    class Meta:
        model = CurriculumOutcome
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_general_capability_codes(self, obj) -> list:
        return sorted(c.code for c in obj.general_capabilities.all())

    def get_cross_curriculum_priority_codes(self, obj) -> list:
        return sorted(c.code for c in obj.cross_curriculum_priorities.all())

    def get_elaboration_count(self, obj) -> int:
        return obj.elaborations.count()

    def _tenant_id(self):
        request = self.context.get("request")
        return getattr(request, "tenant_id", None) if request else None

    def validate(self, attrs):
        # (tenant_id, code, framework) is unique but tenant_id is injected on
        # save, so DRF's own unique-together validator cannot see it. Check
        # here to return a clean 400 instead of a 500 IntegrityError.
        tenant_id = self._tenant_id()
        code = attrs.get("code", getattr(self.instance, "code", None))
        framework = attrs.get("framework", getattr(self.instance, "framework", "ACARA v9"))
        if tenant_id and code:
            qs = CurriculumOutcome.objects.filter(tenant_id=tenant_id, code=code, framework=framework)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"code": "This outcome code already exists for this framework."})

        # Related records must belong to the caller's tenant — the router's
        # PrimaryKeyRelatedField querysets are not tenant-scoped.
        if tenant_id:
            self._check_tenant(attrs, "parent_outcome", tenant_id)
            self._check_tenant(attrs, "achievement_standard_ref", tenant_id)
            for field in ("general_capabilities", "cross_curriculum_priorities"):
                for obj in attrs.get(field) or []:
                    if str(obj.tenant_id) != str(tenant_id):
                        raise serializers.ValidationError({field: "Belongs to a different tenant."})

        parent = attrs.get("parent_outcome", getattr(self.instance, "parent_outcome", None))
        if parent is not None and self.instance is not None and parent.pk == self.instance.pk:
            raise serializers.ValidationError({"parent_outcome": "An outcome cannot elaborate itself."})
        return attrs

    @staticmethod
    def _check_tenant(attrs, field, tenant_id):
        obj = attrs.get(field)
        if obj is not None and str(obj.tenant_id) != str(tenant_id):
            raise serializers.ValidationError({field: "Belongs to a different tenant."})
