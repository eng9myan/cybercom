from rest_framework import serializers
from .models import PayerContract, ContractRate, ContractRule, ReimbursementRule


class PayerContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayerContract
        fields = "__all__"


class ContractRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractRate
        fields = "__all__"


class ContractRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractRule
        fields = "__all__"


class ReimbursementRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReimbursementRule
        fields = "__all__"
