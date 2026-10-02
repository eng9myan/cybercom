"""FHIR R4 REST views — one generic view for every resource type."""
import json

from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from . import mappers  # noqa: F401  register default mappers
from .bundle import execute_bundle
from .capability import capability_statement
from .registry import get_mapper
from platform.api.permissions import CLINICAL_STAFF_ROLES, _roles


def _json(data, status=200):
    resp = JsonResponse(data, status=status)
    resp["Content-Type"] = "application/fhir+json"
    return resp


def _outcome(code, status):
    return _json({"resourceType": "OperationOutcome",
                  "issue": [{"severity": "error", "code": code}]}, status=status)


class _TenantFhirView(View):
    """Plain Django views get none of DRF's permission classes, and these
    shipped with none of their own: any valid token — a patient's, from any
    tenant — could read, create, overwrite and delete every tenant's
    Patient / Observation / Claim / Coverage rows. Staff only, and every
    query runs inside the caller's tenant."""

    def dispatch(self, request, *args, **kwargs):
        if not (_roles(request) & CLINICAL_STAFF_ROLES):
            return _outcome("forbidden", 403)
        self.tenant_id = getattr(request, "tenant_id", None)
        if not self.tenant_id:
            return _outcome("forbidden", 403)
        return super().dispatch(request, *args, **kwargs)

    def _get(self, mapper, id):
        return mapper.django_model.objects.get(id=id, tenant_id=self.tenant_id)


@method_decorator(csrf_exempt, name="dispatch")
class CapabilityView(View):
    def get(self, request):
        return _json(capability_statement())


@method_decorator(csrf_exempt, name="dispatch")
class BundleView(_TenantFhirView):
    def post(self, request):
        try:
            body = json.loads(request.body.decode())
        except json.JSONDecodeError:
            return _json({"resourceType": "OperationOutcome",
                          "issue": [{"severity": "error", "code": "invalid"}]}, status=400)
        return _json(execute_bundle(body, self.tenant_id))


@method_decorator(csrf_exempt, name="dispatch")
class ResourceView(_TenantFhirView):
    def get(self, request, resource_type: str, id: str | None = None):
        try:
            mapper = get_mapper(resource_type)
        except KeyError:
            return _json({"resourceType": "OperationOutcome",
                          "issue": [{"severity": "error", "code": "not-supported"}]}, status=404)
        if id:
            try:
                obj = self._get(mapper, id)
            except mapper.django_model.DoesNotExist:
                return _json({"resourceType": "OperationOutcome",
                              "issue": [{"severity": "error", "code": "not-found"}]}, status=404)
            return _json(mapper.to_fhir(obj))
        params = dict(request.GET.items())
        results = mapper.search(params, self.tenant_id)
        return _json({
            "resourceType": "Bundle", "type": "searchset",
            "total": len(results) if hasattr(results, "__len__") else None,
            "entry": [{"resource": mapper.to_fhir(o)} for o in results],
        })

    def post(self, request, resource_type: str, id: str | None = None):
        mapper = get_mapper(resource_type)
        try:
            body = json.loads(request.body.decode())
        except json.JSONDecodeError:
            return _json({"resourceType": "OperationOutcome",
                          "issue": [{"severity": "error", "code": "invalid"}]}, status=400)
        obj = mapper.from_fhir(body)
        obj.tenant_id = self.tenant_id
        obj.save()
        return _json(mapper.to_fhir(obj), status=201)

    def put(self, request, resource_type: str, id: str):
        mapper = get_mapper(resource_type)
        try:
            obj = self._get(mapper, id)
        except mapper.django_model.DoesNotExist:
            return _json({"resourceType": "OperationOutcome",
                          "issue": [{"severity": "error", "code": "not-found"}]}, status=404)
        payload = json.loads(request.body.decode())
        new = mapper.from_fhir(payload)
        for f in obj._meta.fields:
            if f.name in ("id", "created_at", "tenant_id"): continue
            v = getattr(new, f.name, None)
            if v is not None: setattr(obj, f.name, v)
        obj.save()
        return _json(mapper.to_fhir(obj))

    def delete(self, request, resource_type: str, id: str):
        mapper = get_mapper(resource_type)
        try:
            obj = self._get(mapper, id)
        except mapper.django_model.DoesNotExist:
            return HttpResponse(status=404)
        # soft delete if supported
        if hasattr(obj, "is_deleted"):
            obj.delete()
        else:
            obj.delete()
        return HttpResponse(status=204)
