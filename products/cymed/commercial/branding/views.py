from products.cymed.commercial.branding.models import (
    Brand,
    BrandAsset,
    BrandDomain,
    BrandLocalization,
    BrandTheme,
)
from products.cymed.commercial.branding.serializers import (
    BrandAssetSerializer,
    BrandDomainSerializer,
    BrandLocalizationSerializer,
    BrandSerializer,
    BrandThemeSerializer,
)
from products.cymed.commercial.views import CommercialModelViewSet


class BrandViewSet(CommercialModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class BrandThemeViewSet(CommercialModelViewSet):
    queryset = BrandTheme.objects.all()
    serializer_class = BrandThemeSerializer


class BrandAssetViewSet(CommercialModelViewSet):
    queryset = BrandAsset.objects.all()
    serializer_class = BrandAssetSerializer


class BrandDomainViewSet(CommercialModelViewSet):
    queryset = BrandDomain.objects.all()
    serializer_class = BrandDomainSerializer


class BrandLocalizationViewSet(CommercialModelViewSet):
    queryset = BrandLocalization.objects.all()
    serializer_class = BrandLocalizationSerializer
