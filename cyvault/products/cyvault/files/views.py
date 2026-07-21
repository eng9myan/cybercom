from core.viewsets import TenantScopedModelViewSet
from products.cyvault.files.models import FileObject
from products.cyvault.files.serializers import FileObjectSerializer


class FileObjectViewSet(TenantScopedModelViewSet):
    queryset = FileObject.objects.all()
    serializer_class = FileObjectSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        linked_model = self.request.query_params.get("linked_model")
        linked_id = self.request.query_params.get("linked_id")
        if category:
            qs = qs.filter(category=category)
        if linked_model:
            qs = qs.filter(linked_model=linked_model)
        if linked_id:
            qs = qs.filter(linked_id=linked_id)
        return qs
