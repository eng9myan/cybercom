from rest_framework import serializers
from .models import PayrollBatch, Payslip, PayslipLine


class PayslipLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayslipLine
        fields = '__all__'
        read_only_fields = ['id']


class PayslipSerializer(serializers.ModelSerializer):
    lines = PayslipLineSerializer(many=True, read_only=True)

    class Meta:
        model = Payslip
        fields = '__all__'
        read_only_fields = ['id', 'net_salary', 'created_at']


class PayrollBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollBatch
        fields = '__all__'
        read_only_fields = ['id', 'total_gross', 'total_net', 'created_at', 'updated_at']
        extra_kwargs = {'tenant': {'read_only': True}}

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)
