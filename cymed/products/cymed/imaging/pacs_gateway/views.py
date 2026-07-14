from products.cymed.imaging.views import ImagingModelViewSet

from .models import PACSEvent, PACSNode, PACSQuery, StudyRoute
from .serializers import (
    PACSEventSerializer,
    PACSNodeSerializer,
    PACSQuerySerializer,
    StudyRouteSerializer,
)


class PACSNodeViewSet(ImagingModelViewSet):
    queryset = PACSNode.objects.all()
    serializer_class = PACSNodeSerializer
    required_feature = "imaging.pacs"


class PACSQueryViewSet(ImagingModelViewSet):
    queryset = PACSQuery.objects.select_related("pacs_node")
    serializer_class = PACSQuerySerializer
    required_feature = "imaging.pacs"


class StudyRouteViewSet(ImagingModelViewSet):
    queryset = StudyRoute.objects.select_related("source_pacs", "destination_pacs")
    serializer_class = StudyRouteSerializer
    required_feature = "imaging.pacs"


class PACSEventViewSet(ImagingModelViewSet):
    queryset = PACSEvent.objects.select_related("pacs_node")
    serializer_class = PACSEventSerializer
    required_feature = "imaging.pacs"
    http_method_names = ["get", "head", "options"]
