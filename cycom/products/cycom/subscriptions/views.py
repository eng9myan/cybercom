from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.ar_ap.serializers import InvoiceSerializer
from products.cycom.subscriptions.models import Subscription, SubscriptionPlan
from products.cycom.subscriptions.serializers import SubscriptionPlanSerializer, SubscriptionSerializer
from products.cycom.subscriptions.services import (
    cancel_subscription,
    generate_invoice,
    pause_subscription,
    resume_subscription,
)


class SubscriptionPlanViewSet(TenantScopedModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer


class SubscriptionViewSet(TenantScopedModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    @action(detail=True, methods=["post"], url_path="generate-invoice")
    def generate_invoice_action(self, request, pk=None):
        invoice = generate_invoice(self.get_object())
        return Response(InvoiceSerializer(invoice).data, status=201)

    @action(detail=True, methods=["post"], url_path="pause")
    def pause(self, request, pk=None):
        sub = pause_subscription(self.get_object())
        return Response(SubscriptionSerializer(sub).data)

    @action(detail=True, methods=["post"], url_path="resume")
    def resume(self, request, pk=None):
        sub = resume_subscription(self.get_object())
        return Response(SubscriptionSerializer(sub).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        sub = cancel_subscription(self.get_object())
        return Response(SubscriptionSerializer(sub).data)
