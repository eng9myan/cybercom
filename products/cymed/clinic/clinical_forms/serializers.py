from rest_framework import serializers

from products.cymed.clinic.clinical_forms.models import (
    ClinicalForm,
    ClinicalFormField,
    ClinicalFormSection,
    ClinicalFormSubmission,
    ClinicalFormTemplate,
)


class ClinicalFormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalFormField
        fields = [
            "id",
            "label",
            "label_ar",
            "field_type",
            "options_json",
            "required",
            "display_order",
        ]


class ClinicalFormSectionSerializer(serializers.ModelSerializer):
    fields = ClinicalFormFieldSerializer(many=True, read_only=True)

    class Meta:
        model = ClinicalFormSection
        fields = ["id", "title", "title_ar", "display_order", "fields"]


class ClinicalFormSerializer(serializers.ModelSerializer):
    sections = ClinicalFormSectionSerializer(many=True, read_only=True)

    class Meta:
        model = ClinicalForm
        fields = ["id", "name", "code", "description", "is_active", "sections"]


class ClinicalFormTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalFormTemplate
        fields = "__all__"


class ClinicalFormSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalFormSubmission
        fields = [
            "id",
            "form",
            "patient_id",
            "encounter_id",
            "submitted_by",
            "submitted_at",
            "values_json",
        ]
        read_only_fields = ["submitted_at"]

    def validate(self, attrs):
        form = attrs.get("form")
        values = attrs.get("values_json", {})

        # Run schema validations
        fields = ClinicalFormField.objects.filter(section__form=form)
        for f in fields:
            val = values.get(f.label)
            if f.required and (val is None or val == ""):
                raise serializers.ValidationError(f"Field '{f.label}' is mandatory.")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id
        return super().create(validated_data)
