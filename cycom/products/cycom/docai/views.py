import mimetypes

from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.docai.extraction import DocAIExtractionError, DocAIExtractionNotConfigured, extract
from products.cycom.docai.models import ParsedDocument
from products.cycom.docai.serializers import ParsedDocumentSerializer


class ParsedDocumentViewSet(TenantScopedModelViewSet):
    # Bare-array response: this is a review queue a settings-style page
    # lists in full, same posture as the other small per-tenant catalogs
    # fixed earlier this session (provisioning packs, custom-field
    # definitions) -- the project default PageNumberPagination would
    # silently wrap it and break a frontend `.map()` call.
    pagination_class = None
    serializer_class = ParsedDocumentSerializer
    queryset = ParsedDocument.objects.all()
    http_method_names = ["get", "post", "delete", "head", "options"]

    def perform_create(self, serializer):
        upload = self.request.FILES.get("file")
        media_type = (getattr(upload, "content_type", "") or "").split(";")[0].strip()
        if not media_type and upload is not None:
            media_type, _ = mimetypes.guess_type(upload.name)
        original_filename = upload.name if upload is not None else ""

        instance = serializer.save(
            tenant_id=self.request.tenant_id,
            original_filename=original_filename,
        )

        try:
            instance.file.open("rb")
            file_bytes = instance.file.read()
        finally:
            instance.file.close()

        try:
            result = extract(
                document_type=instance.document_type,
                file_bytes=file_bytes,
                media_type=media_type or "",
            )
            instance.extracted_data = result
            instance.status = "parsed"
        except DocAIExtractionNotConfigured as exc:
            instance.status = "failed"
            instance.error_message = str(exc)
        except DocAIExtractionError as exc:
            instance.status = "failed"
            instance.error_message = str(exc)
        instance.save(update_fields=["extracted_data", "status", "error_message", "updated_at"])

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        """Records the human-corrected version. Does not create any real
        Invoice/PurchaseOrder -- that's a separate, explicit action."""
        doc = self.get_object()
        reviewed = request.data.get("reviewed_data")
        if not isinstance(reviewed, dict):
            return Response({"detail": "'reviewed_data' must be an object."}, status=400)
        doc.reviewed_data = reviewed
        doc.status = "reviewed"
        doc.save(update_fields=["reviewed_data", "status", "updated_at"])
        return Response(ParsedDocumentSerializer(doc).data)

    @action(detail=True, methods=["post"])
    def reparse(self, request, pk=None):
        """Retries extraction -- e.g. after ANTHROPIC_API_KEY was configured
        following an earlier 'not configured' failure."""
        doc = self.get_object()
        doc.file.open("rb")
        try:
            file_bytes = doc.file.read()
        finally:
            doc.file.close()
        media_type, _ = mimetypes.guess_type(doc.original_filename or doc.file.name)
        try:
            doc.extracted_data = extract(
                document_type=doc.document_type, file_bytes=file_bytes, media_type=media_type or "",
            )
            doc.status = "parsed"
            doc.error_message = ""
        except (DocAIExtractionNotConfigured, DocAIExtractionError) as exc:
            doc.status = "failed"
            doc.error_message = str(exc)
        doc.save(update_fields=["extracted_data", "status", "error_message", "updated_at"])
        return Response(ParsedDocumentSerializer(doc).data)
