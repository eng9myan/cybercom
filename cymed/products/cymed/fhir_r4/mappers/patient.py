"""Patient mapper — CyMed Patient ↔ FHIR R4 Patient."""
from django.apps import apps

from ..search import parse_search


class PatientMapper:
    resource_type = "Patient"

    @property
    def django_model(self):
        return apps.get_model("patients", "Patient")

    _search_map = {
        "identifier": "mrn",
        "family": "last_name",
        "given": "first_name",
        "birthdate": "dob",
        "gender": "sex",
        "telecom": "phone",
    }

    def to_fhir(self, p) -> dict:
        return {
            "resourceType": "Patient",
            "id": str(p.id),
            "identifier": [{"system": "https://cymed.sa/mrn", "value": p.mrn}],
            "active": getattr(p, "active", True),
            "name": [{"family": getattr(p, "last_name", ""),
                      "given": [getattr(p, "first_name", "")]}],
            "gender": getattr(p, "sex", ""),
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
            sex=data.get("gender", ""),
            dob=data.get("birthDate"),
            phone=next((t["value"] for t in data.get("telecom", [])
                        if t.get("system") == "phone"), ""),
        )

    def search(self, params: dict):
        q, limit, order = parse_search(params, self._search_map)
        qs = self.django_model.objects.filter(q)
        if order:
            qs = qs.order_by(*order)
        return qs[:limit]
