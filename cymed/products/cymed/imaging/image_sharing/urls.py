"""URL routes for the image_sharing sub-app."""
from django.urls import path

from .views import (
    ExternalImportViewSet,
    ShareableStudyViewSet,
    ShareAccessLogViewSet,
    ShareLinkViewSet,
)

shareable_study_list = ShareableStudyViewSet.as_view({"get": "list", "post": "create"})
shareable_study_detail = ShareableStudyViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
shareable_study_index = ShareableStudyViewSet.as_view({"post": "index_study"})

share_link_list = ShareLinkViewSet.as_view({"get": "list", "post": "create"})
share_link_detail = ShareLinkViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
share_link_create = ShareLinkViewSet.as_view({"post": "create_link"})
share_link_open = ShareLinkViewSet.as_view({"post": "open_link"})
share_link_download = ShareLinkViewSet.as_view({"post": "download"})
share_link_revoke = ShareLinkViewSet.as_view({"post": "revoke"})

share_access_log_list = ShareAccessLogViewSet.as_view({"get": "list"})
share_access_log_detail = ShareAccessLogViewSet.as_view({"get": "retrieve"})

external_import_list = ExternalImportViewSet.as_view({"get": "list", "post": "create"})
external_import_detail = ExternalImportViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
external_import_import = ExternalImportViewSet.as_view({"post": "import_study"})


urlpatterns = [
    path("shareable-studies/", shareable_study_list, name="image-sharing-study-list"),
    path("shareable-studies/<uuid:pk>/", shareable_study_detail, name="image-sharing-study-detail"),
    path("shareable-studies/index/", shareable_study_index, name="image-sharing-study-index"),
    path("share-links/", share_link_list, name="image-sharing-link-list"),
    path("share-links/<uuid:pk>/", share_link_detail, name="image-sharing-link-detail"),
    path("share-links/create-link/", share_link_create, name="image-sharing-link-create"),
    path("share-links/open/", share_link_open, name="image-sharing-link-open"),
    path("share-links/download/", share_link_download, name="image-sharing-link-download"),
    path("share-links/<uuid:pk>/revoke/", share_link_revoke, name="image-sharing-link-revoke"),
    path("access-logs/", share_access_log_list, name="image-sharing-access-log-list"),
    path("access-logs/<uuid:pk>/", share_access_log_detail, name="image-sharing-access-log-detail"),
    path("external-imports/", external_import_list, name="image-sharing-external-import-list"),
    path(
        "external-imports/<uuid:pk>/",
        external_import_detail,
        name="image-sharing-external-import-detail",
    ),
    path(
        "external-imports/import/",
        external_import_import,
        name="image-sharing-external-import-create",
    ),
]
