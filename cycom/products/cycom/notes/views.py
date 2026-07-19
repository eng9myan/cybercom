from core.viewsets import TenantScopedModelViewSet
from products.cycom.notes.models import Note
from products.cycom.notes.serializers import NoteSerializer


class NoteViewSet(TenantScopedModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
