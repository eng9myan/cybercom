from rest_framework import serializers
from products.cymed.core.organizations.models import (
    Organization, OrganizationAddress, OrganizationContact, OrganizationRelationship
)

class OrganizationAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationAddress
        fields = ["id", "line1", "line2", "city", "state", "postal_code", "country"]

class OrganizationContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationContact
        fields = ["id", "telecom_system", "telecom_value"]

class OrganizationRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationRelationship
        fields = ["id", "source_organization", "target_organization", "relationship_type"]

class OrganizationSerializer(serializers.ModelSerializer):
    addresses = OrganizationAddressSerializer(many=True, required=False)
    contacts = OrganizationContactSerializer(many=True, required=False)

    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "organization_type", "is_active", "addresses", "contacts", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        addresses_data = validated_data.pop("addresses", [])
        contacts_data = validated_data.pop("contacts", [])

        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        org = Organization.objects.create(**validated_data)

        for addr in addresses_data:
            OrganizationAddress.objects.create(organization=org, tenant_id=org.tenant_id, **addr)
        for contact in contacts_data:
            OrganizationContact.objects.create(organization=org, tenant_id=org.tenant_id, **contact)

        return org
