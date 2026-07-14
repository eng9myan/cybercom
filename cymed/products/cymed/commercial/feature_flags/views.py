from rest_framework.decorators import action
from rest_framework.response import Response

from products.cymed.commercial.feature_flags.models import (
    CustomerFeature,
    FeatureDependency,
    FeatureFlag,
    TenantFeature,
)
from products.cymed.commercial.feature_flags.serializers import (
    CustomerFeatureSerializer,
    FeatureCheckSerializer,
    FeatureDependencySerializer,
    FeatureFlagSerializer,
    TenantFeatureSerializer,
)
from products.cymed.commercial.views import CommercialModelViewSet


class FeatureFlagViewSet(CommercialModelViewSet):
    queryset = FeatureFlag.objects.all()
    serializer_class = FeatureFlagSerializer

    @action(detail=False, methods=["post"])
    def check(self, request):
        """Check if a feature is enabled for the current tenant."""
        ser = FeatureCheckSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        feature_code = ser.validated_data["feature_code"]
        tenant_id = getattr(request, "tenant_id", None)

        try:
            flag = FeatureFlag.objects.get(code=feature_code)
        except FeatureFlag.DoesNotExist:
            return Response({"enabled": False, "reason": "Feature not found."}, status=404)

        # Check tenant override
        if tenant_id:
            override = TenantFeature.objects.filter(tenant_id=tenant_id, feature=flag).first()
            if override:
                return Response({"enabled": override.is_enabled, "source": "tenant_override"})

        return Response({"enabled": flag.default_enabled, "source": "default"})


class FeatureDependencyViewSet(CommercialModelViewSet):
    queryset = FeatureDependency.objects.all()
    serializer_class = FeatureDependencySerializer


class TenantFeatureViewSet(CommercialModelViewSet):
    queryset = TenantFeature.objects.all()
    serializer_class = TenantFeatureSerializer

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return TenantFeature.objects.filter(tenant_id=tenant_id)
        return TenantFeature.objects.none()


class CustomerFeatureViewSet(CommercialModelViewSet):
    queryset = CustomerFeature.objects.all()
    serializer_class = CustomerFeatureSerializer
