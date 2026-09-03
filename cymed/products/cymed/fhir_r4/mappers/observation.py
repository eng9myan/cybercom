"""Observation mapper — CyMed clinical Observation ↔ FHIR R4 Observation."""
from django.apps import apps

from ..search import parse_search


class ObservationMapper:
    resource_type = "Observation"

    @property
    def django_model(self):
        # Best-effort — falls back to loose lookup
        try:
            return apps.get_model("observations", "Observation")
        except LookupError:
            return apps.get_model("clinical", "Observation")

    _search_map = {
        "patient": "patient_id",
        "subject": "patient_id",
        "code": "loinc_code",
        "category": "category",
        "date": "effective_at",
    }

    def to_fhir(self, o) -> dict:
        val = getattr(o, "value", None)
        return {
            "resourceType": "Observation",
            "id": str(o.id),
            "status": getattr(o, "status", "final"),
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": getattr(o, "category", "vital-signs")}]}],
            "code": {"coding": [{"system": "http://loinc.org",
                                  "code": getattr(o, "loinc_code", ""),
                                  "display": getattr(o, "name", "")}]},
            "subject": {"reference": f"Patient/{o.patient_id}"},
            "effectiveDateTime": str(getattr(o, "effective_at", "")) or None,
            **({"valueQuantity": {
                "value": float(val),
                "unit": getattr(o, "unit", ""),
                "system": "http://unitsofmeasure.org",
            }} if val is not None else {}),
        }

    def from_fhir(self, data: dict):
        Model = self.django_model
        vq = data.get("valueQuantity", {}) or {}
        return Model(
            status=data.get("status", "final"),
            category=(((data.get("category") or [{}])[0].get("coding") or [{}])[0].get("code", "")),
            loinc_code=(((data.get("code", {}).get("coding") or [{}])[0]).get("code", "")),
            name=(((data.get("code", {}).get("coding") or [{}])[0]).get("display", "")),
            patient_id=data.get("subject", {}).get("reference", "").split("/")[-1],
            effective_at=data.get("effectiveDateTime"),
            value=vq.get("value"),
            unit=vq.get("unit", ""),
        )

    def search(self, params: dict):
        q, limit, order = parse_search(params, self._search_map)
        qs = self.django_model.objects.filter(q)
        if order: qs = qs.order_by(*order)
        return qs[:limit]
