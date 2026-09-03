"""Claim mapper — CyMed UnifiedBill ↔ FHIR R4 Claim."""
from django.apps import apps

from ..search import parse_search


class ClaimMapper:
    resource_type = "Claim"

    @property
    def django_model(self):
        return apps.get_model("cymed_payments", "UnifiedBill")

    _search_map = {
        "patient": "patient_profile_id",
        "identifier": "bill_number",
        "status": "status",
        "created": "created_at",
    }

    def to_fhir(self, b) -> dict:
        items = []
        for i, li in enumerate(b.line_items.all(), 1):
            items.append({
                "sequence": i,
                "productOrService": {"coding": [{"code": li.service_code,
                                                   "display": li.service_name}]},
                "quantity": {"value": float(li.quantity)},
                "unitPrice": {"value": float(li.unit_price), "currency": "SAR"},
                "net": {"value": float(li.amount), "currency": "SAR"},
            })
        return {
            "resourceType": "Claim",
            "id": str(b.id),
            "status": "active" if b.status not in ("cancelled",) else "cancelled",
            "type": {"coding": [{"code": "institutional"}]},
            "use": "claim",
            "identifier": [{"value": b.bill_number}],
            "patient": {"reference": f"Patient/{b.patient_profile.patient_id}"},
            "created": str(b.created_at),
            "insurance": [{"sequence": 1, "focal": True,
                            "coverage": {"reference": "Coverage/1"}}],
            "item": items,
            "total": {"value": float(b.total), "currency": "SAR"},
        }

    def from_fhir(self, data: dict):
        # Read-only for now: external systems shouldn't create bills via FHIR
        raise NotImplementedError("Claim creation via FHIR handled by RCM engine")

    def search(self, params: dict):
        q, limit, order = parse_search(params, self._search_map)
        qs = self.django_model.objects.filter(q)
        if order: qs = qs.order_by(*order)
        return qs[:limit]
