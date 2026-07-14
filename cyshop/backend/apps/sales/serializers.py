from rest_framework import serializers
from decimal import Decimal
from .models import (
    Lead, Opportunity, Activity, Task, Meeting, Quotation, QuotationLine,
    SalesOrder, OrderLine, SalesCommunication
)

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)

class OpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)

class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)

class QuotationLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationLine
        fields = ['id', 'item_name', 'qty', 'unit_price', 'discount', 'line_total']

class QuotationSerializer(serializers.ModelSerializer):
    lines = QuotationLineSerializer(many=True)

    class Meta:
        model = Quotation
        fields = [
            'id', 'quotation_number', 'company', 'branch', 'customer_name',
            'customer_type', 'status', 'discount_type', 'discount_value',
            'tax_rate', 'total_amount', 'expiration_date', 'terms_conditions', 'lines'
        ]
        read_only_fields = ['id', 'total_amount']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        lines_data = validated_data.pop('lines')
        
        # Pull base pricing parameters
        customer_type = validated_data.get('customer_type', 'RETAIL')
        overall_discount_val = Decimal(str(validated_data.get('discount_value', 0.0)))
        discount_type = validated_data.get('discount_type', 'PERCENTAGE')
        tax_rate = Decimal(str(validated_data.get('tax_rate', 0.16)))

        lines_subtotal = Decimal('0.00')
        lines_to_create = []

        for line_data in lines_data:
            qty = Decimal(str(line_data.get('qty', 1.0)))
            unit_price = Decimal(str(line_data.get('unit_price', 0.0)))
            
            # --- Pricing & Volume Engine (Program 21.2) ---
            # 1. Wholesale Customer Discount (15%)
            if customer_type == 'WHOLESALE':
                unit_price = unit_price * Decimal('0.85')

            # 2. Volume Pricing Discount
            volume_discount = Decimal('0.00')
            if qty >= Decimal('50.0'):
                volume_discount = Decimal('0.20') # 20% discount
            elif qty >= Decimal('10.0'):
                volume_discount = Decimal('0.10') # 10% discount

            line_sub = qty * unit_price
            line_disc = line_sub * volume_discount
            line_tot = line_sub - line_disc
            
            lines_subtotal += line_tot

            lines_to_create.append({
                "item_name": line_data.get('item_name'),
                "qty": qty,
                "unit_price": unit_price,
                "discount": line_disc,
                "line_total": line_tot
            })

        # Calculate global order discounts
        if discount_type == 'PERCENTAGE':
            total_discount = lines_subtotal * (overall_discount_val / Decimal('100.0'))
        else:
            total_discount = overall_discount_val

        subtotal_after_discount = lines_subtotal - total_discount
        tax_amount = subtotal_after_discount * tax_rate
        final_total = subtotal_after_discount + tax_amount

        # --- Manager Approval Rule ---
        # If total discount percentage exceeds 25%, route status to DRAFT/SUBMITTED for review
        discount_percent = Decimal('0.0')
        if lines_subtotal > 0:
            discount_percent = (total_discount / lines_subtotal) * Decimal('100.0')

        status = validated_data.get('status', 'DRAFT')
        if discount_percent > Decimal('25.0') and status not in ['APPROVED', 'REJECTED']:
            status = 'SUBMITTED' # Requires manager approval override

        quotation = Quotation.objects.create(
            tenant_id=tenant_id,
            total_amount=final_total,
            status=status,
            **validated_data
        )

        for l in lines_to_create:
            QuotationLine.objects.create(
                tenant_id=tenant_id,
                quotation=quotation,
                **l
            )

        return quotation

class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine
        fields = ['id', 'item_name', 'qty', 'unit_price', 'line_total']

class SalesOrderSerializer(serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True)

    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'quotation', 'company', 'branch',
            'customer_name', 'status', 'fulfillment_status',
            'invoice_status', 'delivery_status', 'total_amount', 'lines'
        ]
        read_only_fields = ['id', 'total_amount']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        lines_data = validated_data.pop('lines')

        total = Decimal('0.00')
        lines_to_create = []

        for l_data in lines_data:
            qty = Decimal(str(l_data.get('qty', 1.0)))
            unit_price = Decimal(str(l_data.get('unit_price', 0.0)))
            line_tot = qty * unit_price
            total += line_tot

            lines_to_create.append({
                "item_name": l_data.get('item_name'),
                "qty": qty,
                "unit_price": unit_price,
                "line_total": line_tot
            })

        order = SalesOrder.objects.create(
            tenant_id=tenant_id,
            total_amount=total,
            **validated_data
        )

        for l in lines_to_create:
            OrderLine.objects.create(
                tenant_id=tenant_id,
                order=order,
                **l
            )

        return order

class SalesCommunicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesCommunication
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)
