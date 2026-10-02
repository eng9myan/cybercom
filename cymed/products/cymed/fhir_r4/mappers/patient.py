"""Patient mapper — CyMed Patient ↔ FHIR R4 Patient."""
from django.apps import apps

from ..search import parse_search


class PatientMapper:
    resource_type = "Patient"

    @property
    def django_model(self):
        return apps.get_model("cymed_patients", "Patient")

    _search_map = {
        "birthdate": "dob",
        "gender": "gender",
    }
    # MRN and names are encrypted per tenant (M-6), so only an exact match
    # through the deterministic blind index is possible — no partial search.
    _blind_search_map = {
        "identifier": "mrn_bidx",
        "family": "last_name_bidx",
        "given": "first_name_bidx",
    }

    def to_fhir(self, p) -> dict:
        return {
            "resourceType": "Patient",
            "id": str(p.id),
            "identifier": [{"system": "https://cymed.sa/mrn", "value": p.mrn}],
            "active": getattr(p, "is_active", True),
            "name": [{"family": getattr(p, "last_name", ""),
                      "given": [getattr(p, "first_name", "")]}],
            "gender": getattr(p, "gender", ""),
            "birthDate": str(getattr(p, "dob", "")) or None,
            "telecom": [
                *([{"system": "phone", "value": p.phone}] if getattr(p, "phone", None) else []),
                *([{"system": "email", "value": p.email}] if getattr(p, "email", None) else []),
            ],
            "address": ([{"line": [p.address], "city": getattr(p, "city", "")}]
                        if getattr(p, "address", None) else []),
            "communication": [{"language": {"coding": [{"code": getattr(p, "preferred_language", "ar")}]}}],
        }

    def from_fhir(self, data: dict):
        Patient = self.django_model
        mrn = ""
        for i in data.get("identifier", []):
            if i.get("system", "").endswith("/mrn"):
                mrn = i.get("value", "")
                break
        name = (data.get("name") or [{}])[0]
        return Patient(
            mrn=mrn,
            first_name=(name.get("given") or [""])[0],
            last_name=name.get("family", ""),
            gender=data.get("gender") or "unknown",
            dob=data.get("birthDate"),
        )

    def search(self, params: dict, tenant_id):
        from platform.security.crypto import blind_index

        q, limit, order = parse_search(params, self._search_map)
        exact = {field: blind_index(params[key])
                 for key, field in self._blind_search_map.items() if params.get(key)}
        qs = self.django_model.objects.filter(q, tenant_id=tenant_id, **exact)
        if order:
            qs = qs.order_by(*order)
        return qs[:limit]
