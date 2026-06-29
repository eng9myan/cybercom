from rest_framework import serializers

from products.cymed.commercial.customer_management.models import (
    Customer,
    CustomerContract,
    CustomerDeployment,
    CustomerOrganization,
    CustomerSuccessPlan,
)


class CustomerOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerOrganization
        fields = "__all__"


class CustomerContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerContract
        fields = "__all__"


class CustomerDeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDeployment
        fields = "__all__"


class CustomerSuccessPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerSuccessPlan
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"
