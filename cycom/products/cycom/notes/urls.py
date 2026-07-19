from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.notes.views import NoteViewSet

router = DefaultRouter()
router.register("notes", NoteViewSet)

urlpatterns = [path("", include(router.urls))]
