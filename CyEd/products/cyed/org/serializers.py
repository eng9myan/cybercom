from rest_framework import serializers

from products.cyed.org.models import Campus


class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        # (tenant_id, code) is unique for non-blank codes; tenant is injected on
        # save, so enforce here for a clean 400 rather than a DB IntegrityError.
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None)
        code = attrs.get("code", getattr(self.instance, "code", ""))
        if code:
            qs = Campus.objects.filter(tenant_id=tenant_id, code=code)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"code": "A campus with this code already exists."})
        return attrs
