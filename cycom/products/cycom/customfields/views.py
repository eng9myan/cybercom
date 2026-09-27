from datetime import date

from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cycom.customfields.models import CustomFieldDefinition
from products.cycom.customfields.registry import catalog, resolve_model
from products.cycom.customfields.serializers import CustomFieldDefinitionSerializer


class CustomFieldRegistryView(APIView):
    """Which real cycom models a tenant may attach custom fields to -- the
    only source of truth for the settings UI's model picker, so the list
    can never drift from what the backend actually accepts."""

    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        return Response(catalog())


class CustomFieldDefinitionViewSet(TenantScopedModelViewSet):
    # Bare-array response: a tenant's field definitions for one model are a
    # small, bounded list a settings UI needs in full, not a paginated feed
    # -- the same class of bug as the provisioning catalogs (a paginated
    # envelope silently breaks a frontend that expects `data.map(...)`).
    pagination_class = None
    serializer_class = CustomFieldDefinitionSerializer
    queryset = CustomFieldDefinition.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        model_key = self.request.query_params.get("model_key")
        if model_key:
            qs = qs.filter(model_key=model_key)
        return qs


def _validate_value(defn: CustomFieldDefinition, value):
    """Returns (cleaned_value, error) -- error is None on success. `value`
    is already known non-None here; the caller handles clearing/required."""
    if defn.field_type == "text":
        if not isinstance(value, str):
            return None, f"'{defn.label}' must be text."
        return value, None
    if defn.field_type == "number":
        try:
            return float(value), None
        except (TypeError, ValueError):
            return None, f"'{defn.label}' must be a number."
    if defn.field_type == "date":
        try:
            date.fromisoformat(str(value))
        except ValueError:
            return None, f"'{defn.label}' must be a date (YYYY-MM-DD)."
        return str(value), None
    if defn.field_type == "boolean":
        if not isinstance(value, bool):
            return None, f"'{defn.label}' must be yes/no."
        return value, None
    if defn.field_type == "select":
        if value not in (defn.options or []):
            return None, f"'{defn.label}' must be one of: {', '.join(defn.options or [])}."
        return value, None
    return None, f"Unknown field type for '{defn.label}'."


class CustomFieldValuesView(APIView):
    """
    GET  ?model_key=product&record_id=<uuid>  -> every active field definition
         for that model merged with this record's stored value (null if unset).
    POST {model_key, record_id, values: {field_key: value, ...}} -> validates
         each key against the model's active definitions (fail closed: an
         unknown or inactive field_key is rejected, not silently written) and
         merges into the record's own `attributes` JSON -- fields not present
         in `values` are left untouched.
    """

    permission_classes = [IsAuthenticatedViaClaims]

    def _get_record(self, request, model_key, record_id):
        resolved = resolve_model(model_key)
        if resolved is None:
            return None, None, Response({"detail": f"'{model_key}' is not a valid model_key."}, status=400)
        _label, model = resolved
        try:
            record = model.objects.filter(tenant_id=request.tenant_id).get(pk=record_id)
        except model.DoesNotExist:
            return None, None, Response({"detail": "Record not found."}, status=404)
        except (ValueError, TypeError):
            return None, None, Response({"detail": "Invalid record_id."}, status=400)
        return model, record, None

    def get(self, request):
        model_key = request.query_params.get("model_key", "")
        record_id = request.query_params.get("record_id", "")
        _model, record, error = self._get_record(request, model_key, record_id)
        if error:
            return error

        definitions = CustomFieldDefinition.objects.filter(
            tenant_id=request.tenant_id, model_key=model_key, is_active=True,
        )
        attributes = record.attributes or {}
        return Response([
            {
                "field_key": d.field_key,
                "label": d.label,
                "field_type": d.field_type,
                "options": d.options,
                "required": d.is_required,
                "value": attributes.get(d.field_key),
            }
            for d in definitions
        ])

    def post(self, request):
        model_key = request.data.get("model_key", "")
        record_id = request.data.get("record_id", "")
        values = request.data.get("values") or {}
        if not isinstance(values, dict):
            return Response({"detail": "'values' must be an object."}, status=400)

        _model, record, error = self._get_record(request, model_key, record_id)
        if error:
            return error

        definitions = {
            d.field_key: d
            for d in CustomFieldDefinition.objects.filter(
                tenant_id=request.tenant_id, model_key=model_key, is_active=True,
            )
        }

        cleaned = {}
        errors = {}
        for field_key, raw_value in values.items():
            defn = definitions.get(field_key)
            if defn is None:
                errors[field_key] = "Unknown or inactive custom field."
                continue
            if raw_value is None or raw_value == "":
                if defn.is_required:
                    errors[field_key] = f"'{defn.label}' is required."
                    continue
                cleaned[field_key] = None
                continue
            value, err = _validate_value(defn, raw_value)
            if err:
                errors[field_key] = err
                continue
            cleaned[field_key] = value

        if errors:
            return Response({"detail": "Validation failed.", "errors": errors}, status=400)

        attributes = dict(record.attributes or {})
        attributes.update(cleaned)
        record.attributes = attributes
        record.save(update_fields=["attributes", "updated_at"])

        return Response({"model_key": model_key, "record_id": str(record.pk), "values": attributes})
