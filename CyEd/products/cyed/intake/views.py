from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff
from products.cyed.intake import extract, ocr
from products.cyed.intake.models import DocumentIntake
from products.cyed.intake.serializers import DocumentIntakeSerializer


class DocumentIntakeViewSet(TenantScopedModelViewSet):
    """
    Upload a document (multipart `file`) OR post `raw_text` directly (e.g. from a
    device that already ran OCR). OCR runs if a provider is configured; field
    extraction always runs. Pre-fills admission/accounting data.
    """

    queryset = DocumentIntake.objects.select_related("student").all()
    serializer_class = DocumentIntakeSerializer
    permission_classes = [IsStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _process(self, instance, file=None, raw_text=""):
        content_type = ""
        text = raw_text or ""
        if file is not None:
            content_type = getattr(file, "content_type", "") or ""
            data = file.read()
            instance.file_bytes = data
            got = ocr.extract_text(data, content_type)
            if got is not None:
                text = got
        instance.content_type = content_type
        instance.raw_text = text
        if text:
            instance.extracted_fields = extract.extract_fields(text, instance.doc_type)
            instance.status = "extracted"
        else:
            instance.status = "ocr_pending"
        instance.save()

    def perform_create(self, serializer):
        instance = serializer.save(tenant_id=self.request.tenant_id)
        self._process(instance, file=self.request.FILES.get("file"),
                      raw_text=self.request.data.get("raw_text", ""))

    @action(detail=True, methods=["post"])
    def reprocess(self, request, pk=None):
        """Re-run extraction (e.g. after a device posts OCR text for a pending doc)."""
        doc = self.get_object()
        raw_text = request.data.get("raw_text", doc.raw_text)
        doc.raw_text = raw_text
        if raw_text:
            doc.extracted_fields = extract.extract_fields(raw_text, doc.doc_type)
            doc.status = "extracted"
            doc.save(update_fields=["raw_text", "extracted_fields", "status", "updated_at"])
        return Response(self.get_serializer(doc).data)
