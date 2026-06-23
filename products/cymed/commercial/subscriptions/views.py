from products.cymed.commercial.views import CommercialModelViewSet
from products.cymed.commercial.subscriptions.models import (
    SubscriptionPlan, Subscription, SubscriptionUsage,
    SubscriptionInvoice, SubscriptionContract
)
from products.cymed.commercial.subscriptions.serializers import (
    SubscriptionPlanSerializer, SubscriptionSerializer, SubscriptionUsageSerializer,
    SubscriptionInvoiceSerializer, SubscriptionContractSerializer
)


class SubscriptionPlanViewSet(CommercialModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer


class SubscriptionViewSet(CommercialModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer


class SubscriptionUsageViewSet(CommercialModelViewSet):
    queryset = SubscriptionUsage.objects.all()
    serializer_class = SubscriptionUsageSerializer


class SubscriptionInvoiceViewSet(CommercialModelViewSet):
    queryset = SubscriptionInvoice.objects.all()
    serializer_class = SubscriptionInvoiceSerializer


class SubscriptionContractViewSet(CommercialModelViewSet):
    queryset = SubscriptionContract.objects.all()
    serializer_class = SubscriptionContractSerializer
