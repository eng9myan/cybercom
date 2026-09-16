from rest_framework import serializers

from products.cyed.governance.models import AuditEvent, ConsentRecord


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = "__all__"
        read_only_fields = [f.name for f in AuditEvent._meta.fields]


class ConsentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentRecord
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None) if request else None
        student = attrs.get("student", getattr(self.instance, "student", None))
        ctype = attrs.get("consent_type", getattr(self.instance, "consent_type", None))
        if tenant_id and student and ctype:
            qs = ConsentRecord.objects.filter(tenant_id=tenant_id, student=student, consent_type=ctype)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"consent_type": "A consent of this type already exists for this student — update it instead."}
                )
        return attrs
