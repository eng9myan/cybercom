from core.viewsets import TenantScopedModelViewSet
from products.cycom.knowledge.models import Article
from products.cycom.knowledge.serializers import ArticleSerializer


class ArticleViewSet(TenantScopedModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        parent_id = self.request.query_params.get("parent_id")
        if parent_id == "root":
            qs = qs.filter(parent__isnull=True)
        elif parent_id:
            qs = qs.filter(parent_id=parent_id)
        return qs
