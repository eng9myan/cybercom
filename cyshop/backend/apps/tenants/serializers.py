from rest_framework import serializers
from .models import Tenant, TenantSettings, Company, Branch, Department, WarehousePlaceholder, CostCenterPlaceholder

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'subdomain', 'created_at']
        read_only_fields = ['id', 'created_at']

class TenantSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantSettings
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at']

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'legal_name', 'tax_number', 'country_code', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'company', 'name', 'address', 'timezone', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'company', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)

class WarehousePlaceholderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehousePlaceholder
        fields = ['id', 'company', 'branch', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)

class CostCenterPlaceholderSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenterPlaceholder
        fields = ['id', 'company', 'code', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)
