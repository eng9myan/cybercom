from rest_framework import serializers
from products.cymed.core.documents.models import ClinicalDocument, SOAPNote, ProgressNote

class SOAPNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SOAPNote
        fields = ["id", "subjective", "objective", "assessment", "plan"]

class ProgressNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressNote
        fields = ["id", "narrative"]

class ClinicalDocumentSerializer(serializers.ModelSerializer):
    soap_note = SOAPNoteSerializer(required=False)
    progress_note = ProgressNoteSerializer(required=False)

    class Meta:
        model = ClinicalDocument
        fields = [
            "id", "patient", "encounter", "title", "document_type", "status",
            "content", "version", "parent_document", "digitally_signed_by", "signed_at",
            "soap_note", "progress_note", "created_at", "updated_at"
        ]
        read_only_fields = ["version", "digitally_signed_by", "signed_at", "created_at", "updated_at"]

    def create(self, validated_data):
        soap_data = validated_data.pop("soap_note", None)
        progress_data = validated_data.pop("progress_note", None)

        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        doc = ClinicalDocument.objects.create(**validated_data)

        if soap_data:
            SOAPNote.objects.create(clinical_document=doc, tenant_id=doc.tenant_id, **soap_data)
        if progress_data:
            ProgressNote.objects.create(clinical_document=doc, tenant_id=doc.tenant_id, **progress_data)

        return doc
