from rest_framework import viewsets

from .models import NphiesInteraction
from .serializers import NphiesInteractionSerializer


class NphiesInteractionViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin-only audit view of every NPHIES exchange."""
    queryset = NphiesInteraction.objects.all()
    serializer_class = NphiesInteractionSerializer
