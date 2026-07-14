from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Category
from .serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        parent_id = self.request.query_params.get("parent_id")
        if parent_id == "root":
            qs = qs.filter(parent__isnull=True)
        elif parent_id:
            qs = qs.filter(parent_id=parent_id)
        # Country eligibility (Category.is_eligible_for_country) isn't
        # filterable as a queryset expression — allowed_country_codes=[]
        # means "everywhere", which JSONField can't express portably as a
        # single query. Left as a model-level check for callers to apply,
        # not wired into list filtering here to avoid returning a plain
        # list where callers (pagination) expect a queryset.
        return qs
