from rest_framework import serializers

from products.cyed.visitors.models import Visitor


class VisitorSerializer(serializers.ModelSerializer):
    on_site = serializers.ReadOnlyField()

    class Meta:
        model = Visitor
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "signed_out_at", "created_at", "updated_at"]
