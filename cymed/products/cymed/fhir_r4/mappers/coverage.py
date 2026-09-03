"""Coverage mapper — CyMed InsurancePolicy ↔ FHIR R4 Coverage."""
from django.apps import apps

from ..search import parse_search


class CoverageMapper:
    resource_type = "Coverage"

    @property
    def django_model(self):
        return apps.get_model("cymed_payments", "InsurancePolicy")

    _search_map = {
        "patient": "profile_id",
        "beneficiary": "profile_id",
        "payor": "insurer_code",
        "identifier": "policy_number",
    }

    def to_fhir(self, p) -> dict:
        return {
            "resourceType": "Coverage",
            "id": str(p.id),
            "status": "active" if not p.is_deleted else "cancelled",
            "identifier": [{"value": p.policy_number}],
            "beneficiary": {"reference": f"Patient/{p.profile.patient_id}"},
            "subscriberId": p.member_no,
            "payor": [{"identifier": {"value": p.insurer_code}}],
            "class": ([{"type": {"coding": [{"code": "plan"}]},
                        "value": p.network_tier}] if p.network_tier else []),
            "period": {
                "start": str(p.valid_from) if p.valid_from else None,
                "end": str(p.valid_to) if p.valid_to else None,
            },
            "costToBeneficiary": ([{
                "type": {"coding": [{"code": "copay"}]},
                "valueMoney": {"value": float(p.co_pay_fixed), "currency": "SAR"},
            }] if p.co_pay_fixed else []),
        }

    def from_fhir(self, data: dict):
        Policy = self.django_model
        return Policy(
            insurer_code=(data.get("payor") or [{}])[0].get("identifier", {}).get("value", ""),
            policy_number=(data.get("identifier") or [{}])[0].get("value", ""),
            member_no=data.get("subscriberId", ""),
        )

    def search(self, params: dict):
        q, limit, order = parse_search(params, self._search_map)
        qs = self.django_model.objects.filter(q)
        if order: qs = qs.order_by(*order)
        return qs[:limit]
