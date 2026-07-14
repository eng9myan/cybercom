from rest_framework import serializers
from .models import Warehouse, StockLocation, StockLevel, StockMovement, StockTransfer


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class StockLocationSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = StockLocation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class StockLevelSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.internal_ref', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True, allow_null=True)
    location_code = serializers.CharField(source='location.code', read_only=True)
    warehouse_name = serializers.CharField(source='location.warehouse.name', read_only=True)
    available_quantity = serializers.DecimalField(
        max_digits=15, decimal_places=4, read_only=True
    )

    class Meta:
        model = StockLevel
        fields = '__all__'
        read_only_fields = ['id', 'quantity', 'reserved_quantity', 'created_at', 'updated_at']


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    from_location_code = serializers.CharField(source='from_location.code', read_only=True, allow_null=True)
    to_location_code = serializers.CharField(source='to_location.code', read_only=True, allow_null=True)

    class Meta:
        model = StockMovement
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        if data.get('quantity', 0) <= 0:
            raise serializers.ValidationError({'quantity': 'Quantity must be positive.'})
        if not data.get('from_location') and not data.get('to_location'):
            raise serializers.ValidationError(
                'At least one of from_location or to_location must be provided.'
            )
        return data

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class StockTransferSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    from_branch_name = serializers.CharField(source='from_branch.name', read_only=True)
    to_branch_name = serializers.CharField(source='to_branch.name', read_only=True)
    from_location_code = serializers.CharField(source='from_location.code', read_only=True)
    to_location_code = serializers.CharField(source='to_location.code', read_only=True)

    class Meta:
        model = StockTransfer
        fields = '__all__'
        read_only_fields = [
            'id', 'transfer_number', 'status', 'dispatch_movement', 'receive_movement',
            'dispatched_at', 'received_at', 'created_at', 'updated_at',
        ]

    def validate(self, data):
        if data.get('quantity', 0) <= 0:
            raise serializers.ValidationError({'quantity': 'Quantity must be positive.'})
        if data.get('from_location') and data.get('to_location') and data['from_location'] == data['to_location']:
            raise serializers.ValidationError('Source and destination locations must differ.')
        return data

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        validated_data['status'] = 'DRAFT'
        return super().create(validated_data)
