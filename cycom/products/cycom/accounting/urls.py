from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.accounting.views import AccountViewSet, JournalEntryViewSet, JournalLineViewSet

router = DefaultRouter()
router.register("accounts", AccountViewSet)
router.register("journal-entries", JournalEntryViewSet)
router.register("journal-lines", JournalLineViewSet)

urlpatterns = [path("", include(router.urls))]
