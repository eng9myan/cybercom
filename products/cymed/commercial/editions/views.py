from rest_framework.decorators import action
from rest_framework.response import Response

from products.cymed.commercial.editions.models import (
    EditionFeature,
    EditionLimit,
    EditionModule,
    ProductCatalogEntry,
    ProductEdition,
)
from products.cymed.commercial.editions.serializers import (
    EditionFeatureSerializer,
    EditionLimitSerializer,
    EditionModuleSerializer,
    ProductCatalogEntrySerializer,
    ProductEditionSerializer,
)
from products.cymed.commercial.views import CommercialModelViewSet


class ProductCatalogEntryViewSet(CommercialModelViewSet):
    queryset = ProductCatalogEntry.objects.all()
    serializer_class = ProductCatalogEntrySerializer


class ProductEditionViewSet(CommercialModelViewSet):
    queryset = ProductEdition.objects.select_related("product").prefetch_related(
        "features", "limits", "modules"
    )
    serializer_class = ProductEditionSerializer

    @action(detail=True, methods=["get"])
    def feature_matrix(self, request, pk=None):
        """Return the full feature matrix for this edition."""
        edition = self.get_object()
        features = EditionFeature.objects.filter(edition=edition)
        return Response(
            {
                "edition": edition.code,
                "product": edition.product.code,
                "features": EditionFeatureSerializer(features, many=True).data,
            }
        )


class EditionFeatureViewSet(CommercialModelViewSet):
    queryset = EditionFeature.objects.all()
    serializer_class = EditionFeatureSerializer


class EditionLimitViewSet(CommercialModelViewSet):
    queryset = EditionLimit.objects.all()
    serializer_class = EditionLimitSerializer


class EditionModuleViewSet(CommercialModelViewSet):
    queryset = EditionModule.objects.all()
    serializer_class = EditionModuleSerializer
