from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"templates", views.DocumentationTemplateViewSet, basename="doc-template")
router.register(r"smart-phrases", views.SmartPhraseViewSet, basename="smart-phrase")
router.register(r"notes", views.ProviderClinicalNoteViewSet, basename="clinical-note")
router.register(r"cosignatures", views.NoteCoSignatureViewSet, basename="note-cosignature")
router.register(r"voice-dictations", views.VoiceDictationViewSet, basename="voice-dictation")

urlpatterns = [path("", include(router.urls))]
