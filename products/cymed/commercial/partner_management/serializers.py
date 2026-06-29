from rest_framework import serializers

from products.cymed.commercial.partner_management.models import (
    DistributorAgreement,
    Partner,
    PartnerType,
    ResellerAgreement,
)


class PartnerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerType
        fields = "__all__"


class ResellerAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResellerAgreement
        fields = "__all__"


class DistributorAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistributorAgreement
        fields = "__all__"


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = "__all__"
