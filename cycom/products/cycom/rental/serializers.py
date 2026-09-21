from rest_framework import serializers

from products.cycom.rental.models import RentalOrder, RentalOrderLine


class RentalOrderLineSerializer(serializers.ModelSerializer):
    rental_days = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    late_days = serializers.IntegerField(read_only=True)
    late_fee = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = RentalOrderLine
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "order", "returned_date", "created_at", "updated_at"]


class RentalOrderSerializer(serializers.ModelSerializer):
    lines = RentalOrderLineSerializer(many=True, read_only=True)

    class Meta:
        model = RentalOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "created_at", "updated_at"]
