from django.contrib import admin

from .models import Dispute, PaymentIntent


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ["id", "order_id", "status", "amount", "captured_amount", "refunded_amount"]
    list_filter = ["status", "provider"]


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ["id", "order_id", "status", "created_at"]
    list_filter = ["status"]
