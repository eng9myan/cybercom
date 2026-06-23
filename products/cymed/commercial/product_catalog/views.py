from products.cymed.commercial.views import CommercialModelViewSet
from products.cymed.commercial.product_catalog.models import (
    ProductVersion, ProductLicenseMapping, ProductFeatureMatrix
)
from products.cymed.commercial.product_catalog.serializers import (
    ProductVersionSerializer, ProductLicenseMappingSerializer, ProductFeatureMatrixSerializer
)


class ProductVersionViewSet(CommercialModelViewSet):
    queryset = ProductVersion.objects.all()
    serializer_class = ProductVersionSerializer


class ProductLicenseMappingViewSet(CommercialModelViewSet):
    queryset = ProductLicenseMapping.objects.all()
    serializer_class = ProductLicenseMappingSerializer


class ProductFeatureMatrixViewSet(CommercialModelViewSet):
    queryset = ProductFeatureMatrix.objects.all()
    serializer_class = ProductFeatureMatrixSerializer
