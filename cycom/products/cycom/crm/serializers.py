from rest_framework import serializers

from products.cycom.crm.models import Lead


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
