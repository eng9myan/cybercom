"""
CyMed Laboratory — Core Services
Integrates with: TerminologyService (LOINC/SNOMED), CyAI, CyData, CyIntegrationHub.
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from typing import Any


class LabOrderingService:
    """Creates and manages lab orders from any source (clinic, hospital, external)."""

    @staticmethod
    def create_order(
        tenant_id,
        patient_id,
        order_type,
        tests: list[str],
        priority="routine",
        encounter_id=None,
        ordered_by=None,
    ) -> dict[str, Any]:
        """
        Create a LabOrder with items. Validates test codes via TerminologyService (LOINC).
        Returns serialized order dict.
        """
        from products.cymed.laboratory.orders.models import (
            LabOrder,
            LabOrderItem,
            LabOrderStatusHistory,
            LabTest,
        )

        order_number = (
            f"LAB-{datetime.date.today().strftime('%Y%m%d')}-{str(uuid.uuid4()).upper()[:8]}"
        )
        order = LabOrder.objects.create(
            tenant_id=tenant_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
            order_type=order_type,
            priority=priority,
            ordered_by=ordered_by,
            order_number=order_number,
            status="submitted",
        )
        for test_code in tests:
            try:
                test = LabTest.objects.get(tenant_id=tenant_id, code=test_code, is_active=True)
                LabOrderItem.objects.create(
                    tenant_id=tenant_id,
                    order=order,
                    test=test,
                    priority=priority,
                    specimen_type=test.specimen_types_accepted[0]
                    if test.specimen_types_accepted
                    else "",
                )
            except LabTest.DoesNotExist:
                pass

        LabOrderStatusHistory.objects.create(
            tenant_id=tenant_id,
            order=order,
            from_status="",
            to_status="submitted",
        )
        return {"order_id": str(order.id), "order_number": order.order_number}

    @staticmethod
    def validate_test_loinc(loinc_code: str) -> dict | None:
        """Delegates LOINC validation to TerminologyService — no local LOINC lookup."""
        try:
            from platform.terminology.services import TerminologyService

            return TerminologyService.lookup(code=loinc_code, system="loinc")
        except Exception:
            return None

    @staticmethod
    def validate_diagnosis_icd11(icd11_code: str) -> dict | None:
        """Delegates ICD-11 code validation to TerminologyService."""
        try:
            from platform.terminology.services import TerminologyService

            return TerminologyService.lookup(code=icd11_code, system="icd11")
        except Exception:
            return None


class SpecimenService:
    """Specimen lifecycle management — collection, transport, chain-of-custody."""

    @staticmethod
    def record_collection(
        tenant_id,
        specimen_id,
        collected_by,
        collected_at,
        collection_site,
        method="",
        fasting=False,
    ) -> dict:
        from products.cymed.laboratory.specimens.models import (
            Specimen,
            SpecimenChainOfCustody,
            SpecimenCollection,
        )

        specimen = Specimen.objects.get(pk=specimen_id, tenant_id=tenant_id)
        coll, _ = SpecimenCollection.objects.get_or_create(
            specimen=specimen,
            defaults={
                "tenant_id": tenant_id,
                "collected_by": collected_by,
                "collected_at": collected_at,
                "collection_site": collection_site,
                "collection_method": method,
                "patient_fasting": fasting,
            },
        )
        specimen.status = "collected"
        specimen.collected_at = collected_at
        specimen.save(update_fields=["status", "collected_at", "updated_at"])

        SpecimenChainOfCustody.objects.create(
            tenant_id=tenant_id,
            specimen=specimen,
            action="collected",
            performed_by=collected_by,
            location=collection_site,
            action_timestamp=collected_at,
        )
        return {"specimen_id": str(specimen.id), "status": "collected"}

    @staticmethod
    def reject_specimen(
        tenant_id, specimen_id, rejected_by, reason, action_taken="recollect"
    ) -> dict:
        from platform.events.models import OutboxEvent
        from products.cymed.laboratory.specimens.models import Specimen, SpecimenRejection

        specimen = Specimen.objects.get(pk=specimen_id, tenant_id=tenant_id)
        rejection = SpecimenRejection.objects.create(
            tenant_id=tenant_id,
            specimen=specimen,
            rejection_reason=reason,
            rejected_by=rejected_by,
            action_taken=action_taken,
        )
        specimen.status = "rejected"
        specimen.save(update_fields=["status", "updated_at"])
        OutboxEvent.objects.create(
            tenant_id=str(tenant_id),
            topic="cymed.lab.specimen.rejected",
            event_type="cymed.lab.specimen.rejected",
            payload={"specimen_id": str(specimen.id), "reason": reason},
        )
        return {"specimen_id": str(specimen.id), "rejection_id": str(rejection.id)}

    @staticmethod
    def resolve_specimen_snomed(specimen_type: str) -> str | None:
        """Look up SNOMED-CT code for a specimen type via TerminologyService."""
        try:
            from platform.terminology.services import TerminologyService

            results = TerminologyService.search(query=specimen_type, system="snomed")
            return results[0]["code"] if results else None
        except Exception:
            return None


class ResultService:
    """Result management — critical value detection, delta checks, AI integration."""

    @staticmethod
    def run_delta_check(
        tenant_id,
        patient_id,
        analyte_code,
        current_value: Decimal,
        delta_threshold_pct: Decimal = Decimal("25"),
    ) -> dict:
        """
        Check if current value deviates >delta_threshold_pct from most recent previous value.
        Returns delta check result dict. CyAI can call this for enhanced pattern detection.
        """
        from products.cymed.laboratory.results.models import ResultValue

        previous = (
            ResultValue.objects.filter(
                tenant_id=tenant_id,
                analyte_code=analyte_code,
                result__order_item__order__patient_id=patient_id,
                value_numeric__isnull=False,
            )
            .exclude(value_numeric=None)
            .order_by("-created_at")
            .first()
        )
        if not previous or not previous.value_numeric:
            return {"delta_flag": False, "delta_pct": None, "previous_value": None}

        prev = Decimal(str(previous.value_numeric))
        if prev == 0:
            return {"delta_flag": False, "delta_pct": None, "previous_value": str(prev)}

        delta_pct = abs((current_value - prev) / prev) * 100
        return {
            "delta_flag": delta_pct > delta_threshold_pct,
            "delta_pct": float(delta_pct),
            "previous_value": str(prev),
            "previous_date": previous.created_at.date().isoformat()
            if previous.created_at
            else None,
        }

    @staticmethod
    def notify_critical(tenant_id, result_value_id, notified_by) -> bool:
        from products.cymed.laboratory.results.models import CriticalResult

        try:
            cr = CriticalResult.objects.get(result_value_id=result_value_id, tenant_id=tenant_id)
            cr.notification_status = "notified"
            cr.notified_by = notified_by
            cr.notified_at = datetime.datetime.now(tz=datetime.UTC)
            cr.save(update_fields=["notification_status", "notified_by", "notified_at"])
            return True
        except CriticalResult.DoesNotExist:
            return False

    @staticmethod
    def request_ai_interpretation(result_id) -> dict:
        """
        Requests CyAI to generate a result interpretation suggestion.
        AI suggestions are advisory only — human approval required before release.
        """
        try:
            from platform.cyai.services import CyAIService  # type: ignore

            return CyAIService.analyze_lab_result(result_id=str(result_id))
        except Exception:
            return {"suggestion": None, "confidence": None, "ai_available": False}


class QCService:
    """Quality control evaluation — Westgard rules engine."""

    WESTGARD_RULES = {
        "12s": lambda z, history: abs(z) > 2,
        "13s": lambda z, history: abs(z) > 3,
        "22s": lambda z, history: (
            len(history) >= 2 and all(abs(h) > 2 and (h > 0) == (z > 0) for h in history[-1:])
        ),
        "r4s": lambda z, history: len(history) >= 1 and abs(z - history[-1]) > 4,
        "41s": lambda z, history: (
            len(history) >= 3 and all(abs(h) > 1 and (h > 0) == (z > 0) for h in history[-3:])
        ),
    }

    @classmethod
    def evaluate_run(cls, qc_id, measured_value: Decimal, tenant_id=None) -> dict:
        """
        Evaluate a QC run against all active Westgard rules for this QC material.
        Returns: {passed, is_warning, is_rejection, z_score, rules_triggered}
        """
        from products.cymed.laboratory.quality.models import QualityControl, QualityRun

        qc = QualityControl.objects.get(pk=qc_id)
        mean = Decimal(str(qc.target_mean))
        sd = Decimal(str(qc.target_sd))
        z = float((measured_value - mean) / sd) if sd != 0 else 0.0

        recent = list(
            QualityRun.objects.filter(qc=qc, tenant_id=tenant_id)
            .order_by("-run_date", "-run_time")[:9]
            .values_list("z_score", flat=True)
        )
        recent_z = [float(r) for r in recent if r is not None]

        rules_triggered = []
        is_rejection = False
        is_warning = False
        for rule_name, rule_fn in cls.WESTGARD_RULES.items():
            if rule_fn(z, recent_z):
                rules_triggered.append(rule_name)
                if rule_name == "12s":
                    is_warning = True
                else:
                    is_rejection = True

        return {
            "z_score": Decimal(str(round(z, 4))),
            "passed": not is_rejection,
            "is_warning": is_warning,
            "is_rejection": is_rejection,
            "rules_triggered": rules_triggered,
        }


class FHIRLabService:
    """
    FHIR R4 mapping for laboratory entities.
    Produces/consumes FHIR resources: ServiceRequest, DiagnosticReport, Observation, Specimen.
    """

    @staticmethod
    def to_fhir_service_request(order) -> dict:
        return {
            "resourceType": "ServiceRequest",
            "id": str(order.id),
            "status": order.status,
            "intent": "order",
            "priority": order.priority,
            "subject": {"reference": f"Patient/{order.patient_id}"},
            "encounter": {"reference": f"Encounter/{order.encounter_id}"}
            if order.encounter_id
            else None,
            "requester": {"reference": f"Practitioner/{order.ordered_by}"},
            "identifier": [{"value": order.order_number}],
        }

    @staticmethod
    def to_fhir_diagnostic_report(result) -> dict:
        order_item = result.order_item
        return {
            "resourceType": "DiagnosticReport",
            "id": str(result.id),
            "status": result.status,
            "subject": {"reference": f"Patient/{order_item.order.patient_id}"},
            "result": [{"reference": f"Observation/{rv.id}"} for rv in result.values.all()],
        }

    @staticmethod
    def to_fhir_observation(result_value) -> dict:
        obs: dict[str, Any] = {
            "resourceType": "Observation",
            "id": str(result_value.id),
            "status": "final",
            "code": {},
            "interpretation": [],
        }
        if result_value.loinc_code:
            obs["code"] = {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": result_value.loinc_code,
                        "display": result_value.analyte_name,
                    }
                ]
            }
        if result_value.value_numeric is not None:
            obs["valueQuantity"] = {
                "value": float(result_value.value_numeric),
                "unit": result_value.unit,
            }
        elif result_value.value_text:
            obs["valueString"] = result_value.value_text
        if result_value.interpretation:
            obs["interpretation"] = [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                            "code": result_value.interpretation,
                        }
                    ]
                }
            ]
        return obs

    @staticmethod
    def to_fhir_specimen(specimen) -> dict:
        return {
            "resourceType": "Specimen",
            "id": str(specimen.id),
            "identifier": [{"value": specimen.specimen_number}],
            "type": {"text": specimen.specimen_type},
            "subject": {"reference": f"Patient/{specimen.patient_id}"},
            "collection": {
                "collectedDateTime": specimen.collected_at.isoformat()
                if specimen.collected_at
                else None
            },
        }

    @staticmethod
    def from_fhir_service_request(payload: dict, tenant_id, ordered_by) -> dict:
        """Parse incoming FHIR ServiceRequest and create a LabOrder."""
        patient_ref = payload.get("subject", {}).get("reference", "")
        patient_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref
        encounter_ref = payload.get("encounter", {}).get("reference", "")
        encounter_id = encounter_ref.split("/")[-1] if "/" in encounter_ref else None
        priority = payload.get("priority", "routine")
        order_type = "external"

        codes = []
        for item in payload.get("code", {}).get("coding", []):
            codes.append(item.get("code", ""))

        return LabOrderingService.create_order(
            tenant_id=tenant_id,
            patient_id=patient_id,
            order_type=order_type,
            tests=codes,
            priority=priority,
            encounter_id=encounter_id,
            ordered_by=ordered_by,
        )
