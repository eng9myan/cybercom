from core.viewsets import TenantScopedModelViewSet
from products.cycom.documents.models import Document
from products.cycom.documents.serializers import DocumentSerializer


class DocumentViewSet(TenantScopedModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tag = self.request.query_params.get("tag")
        if tag:
            # __contains (Postgres @> containment) isn't supported on
            # SQLite (used in CI/tests) — icontains does a portable text
            # match against the serialized JSON on both backends.
            qs = qs.filter(tags__icontains=tag)
        linked_model = self.request.query_params.get("linked_model")
        linked_id = self.request.query_params.get("linked_id")
        if linked_model:
            qs = qs.filter(linked_model=linked_model)
        if linked_id:
            qs = qs.filter(linked_id=linked_id)
        return qs
