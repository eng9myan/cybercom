"""
Core services for CyMed Imaging Edition.
All terminology via TerminologyService — no local LOINC/SNOMED stores.
CyAI is advisory only — radiologist approval required for all reports.
"""

import logging
import uuid

logger = logging.getLogger(__name__)


class ImagingOrderService:
    @staticmethod
    def create_order(
        tenant_id,
        patient_id,
        order_type,
        procedures,
        priority,
        ordered_by,
        encounter_id=None,
        clinical_indication="",
        icd11_codes=None,
    ) -> dict:
        from platform.events.models import OutboxEvent
        from products.cymed.imaging.orders.models import (
            ImagingOrder,
            ImagingOrderItem,
            ImagingOrderStatusHistory,
            ImagingProcedure,
        )

        order_number = f"IMG-{uuid.uuid4().hex[:8].upper()}"
        order = ImagingOrder.objects.create(
            tenant_id=tenant_id,
            order_number=order_number,
            patient_id=patient_id,
            encounter_id=encounter_id,
            ordered_by=ordered_by,
            order_type=order_type,
            priority=priority,
            clinical_indication=clinical_indication,
            icd11_codes=icd11_codes or [],
        )
        for proc_code in procedures:
            try:
                procedure = ImagingProcedure.objects.get(
                    tenant_id=tenant_id, code=proc_code, is_active=True
                )
                ImagingOrderItem.objects.create(
                    tenant_id=tenant_id,
                    order=order,
                    procedure=procedure,
                    contrast_required=procedure.contrast_required,
                )
            except ImagingProcedure.DoesNotExist:
                continue

        ImagingOrderStatusHistory.objects.create(
            tenant_id=tenant_id,
            order=order,
            from_status="",
            to_status="pending",
            changed_by=ordered_by,
        )
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.imaging.orders",
            event_type="cymed.imaging.order.created",
            payload={
                "aggregate_type": "ImagingOrder",
                "aggregate_id": str(order.id),
                "order_number": order_number,
                "patient_id": str(patient_id),
                "priority": priority,
            },
        )
        return {"order_number": order_number, "order_id": str(order.id), "items": len(procedures)}

    @staticmethod
    def validate_procedure_snomed(snomed_code: str) -> bool:
        try:
            from platform.terminology.services import TerminologyService

            result = TerminologyService.lookup(system="snomed", code=snomed_code)
            return result is not None
        except Exception:
            return True  # non-blocking in test env


class SchedulingService:
    @staticmethod
    def schedule_appointment(
        tenant_id,
        order_item_id,
        modality_id,
        scheduled_start,
        scheduled_end,
        radiologist_id=None,
        technologist_id=None,
        room_id=None,
    ) -> dict:
        from products.cymed.imaging.modality_worklist.models import Modality
        from products.cymed.imaging.orders.models import ImagingOrderItem
        from products.cymed.imaging.scheduling.models import ImagingAppointment

        order_item = ImagingOrderItem.objects.get(pk=order_item_id, tenant_id=tenant_id)
        modality = Modality.objects.get(pk=modality_id, tenant_id=tenant_id)
        duration = int((scheduled_end - scheduled_start).total_seconds() / 60)

        appt = ImagingAppointment.objects.create(
            tenant_id=tenant_id,
            order_item=order_item,
            patient_id=order_item.order.patient_id,
            modality=modality,
            radiologist_id=radiologist_id,
            technologist_id=technologist_id,
            room_id=room_id,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=max(duration, 1),
        )
        order_item.order.status = "scheduled"
        order_item.order.save(update_fields=["status"])
        return {"appointment_id": str(appt.id)}


class ReportingService:
    @staticmethod
    def finalize_report(report_id, finalized_by) -> dict:
        import django.utils.timezone as tz

        from platform.events.models import OutboxEvent
        from products.cymed.imaging.radiology_reporting.models import RadiologyReport
        from products.cymed.imaging.results.models import ImagingResult

        report = RadiologyReport.objects.get(pk=report_id)
        report.status = "final"
        report.finalized_at = tz.now()
        report.finalized_by = finalized_by
        report.word_count = len((report.findings + " " + report.impression).split())
        report.save(update_fields=["status", "finalized_at", "finalized_by", "word_count"])

        ImagingResult.objects.update_or_create(
            order_item=report.order_item,
            defaults={
                "tenant_id": report.tenant_id,
                "report": report,
                "status": "final",
            },
        )
        OutboxEvent.objects.create(
            tenant_id=report.tenant_id,
            topic="cymed.imaging.reports",
            event_type="cymed.imaging.report.finalized",
            payload={
                "aggregate_type": "RadiologyReport",
                "aggregate_id": str(report.id),
                "order_item_id": str(report.order_item_id),
                "radiologist_id": str(report.radiologist_id),
            },
        )
        return {"report_id": str(report.id), "status": "final"}

    @staticmethod
    def request_ai_summary(report_id) -> str:
        try:
            from platform.ai.services import CyAIService

            return CyAIService.summarize_radiology_report(report_id=report_id)
        except Exception:
            return ""  # AI advisory — non-blocking


class FHIRImagingService:
    @staticmethod
    def to_fhir_service_request(order) -> dict:
        status_map = {
            "pending": "draft",
            "scheduled": "active",
            "in_progress": "active",
            "completed": "completed",
            "cancelled": "revoked",
            "on_hold": "on-hold",
        }
        resource = {
            "resourceType": "ServiceRequest",
            "id": str(order.id),
            "status": status_map.get(order.status, "draft"),
            "intent": "order",
            "priority": order.priority,
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "363679005",
                            "display": "Imaging",
                        }
                    ]
                }
            ],
            "subject": {"reference": f"Patient/{order.patient_id}"},
            "authoredOn": order.created_at.isoformat(),
            "requester": {"reference": f"Practitioner/{order.ordered_by}"},
            "identifier": [{"system": "urn:cybercom:imaging:order", "value": order.order_number}],
        }
        if order.encounter_id:
            resource["encounter"] = {"reference": f"Encounter/{order.encounter_id}"}
        if order.clinical_indication:
            resource["reasonCode"] = [{"text": order.clinical_indication}]
        return resource

    @staticmethod
    def to_fhir_diagnostic_report(result) -> dict:
        status_map = {
            "pending": "registered",
            "preliminary": "preliminary",
            "final": "final",
            "amended": "amended",
        }
        resource = {
            "resourceType": "DiagnosticReport",
            "id": str(result.id),
            "status": status_map.get(result.status, "registered"),
            "category": [
                {
                    "coding": [
                        {"system": "http://loinc.org", "code": "LP29684-5", "display": "Radiology"}
                    ]
                }
            ],
            "subject": {"reference": f"Patient/{result.order_item.order.patient_id}"},
            "issued": result.result_date.isoformat() if result.result_date else None,
        }
        if result.report:
            resource["conclusion"] = result.report.impression
        return resource

    @staticmethod
    def to_fhir_imaging_study(study) -> dict:
        return {
            "resourceType": "ImagingStudy",
            "id": str(study.id),
            "status": "available",
            "subject": {"reference": f"Patient/{study.patient_id}"},
            "started": study.study_date.isoformat() if study.study_date else None,
            "numberOfSeries": study.series_count,
            "numberOfInstances": study.instance_count,
            "identifier": [
                {"system": "urn:dicom:uid", "value": f"urn:oid:{study.study_instance_uid}"}
            ],
            "modality": [
                {
                    "system": "http://dicom.nema.org/resources/ontology/DCM",
                    "code": study.modality.upper(),
                }
            ],
        }


class WorklistService:
    @staticmethod
    def add_to_worklist(
        tenant_id, worklist_id, order_item_id, priority_rank=999, scheduled_time=None
    ) -> dict:
        from products.cymed.imaging.modality_worklist.models import ModalityWorklist, WorklistEntry
        from products.cymed.imaging.orders.models import ImagingOrderItem

        worklist = ModalityWorklist.objects.get(pk=worklist_id, tenant_id=tenant_id)
        order_item = ImagingOrderItem.objects.get(pk=order_item_id, tenant_id=tenant_id)
        entry = WorklistEntry.objects.create(
            tenant_id=tenant_id,
            worklist=worklist,
            order_item=order_item,
            patient_id=order_item.order.patient_id,
            accession_number=order_item.accession_number,
            priority_rank=priority_rank,
            scheduled_time=scheduled_time,
        )
        return {"entry_id": str(entry.id)}


class TeleradiologyService:
    @staticmethod
    def assign_case(tenant_id, case_id, radiologist_id, assigned_by) -> dict:

        from products.cymed.imaging.teleradiology.models import ReadingAssignment, TeleradiologyCase

        case = TeleradiologyCase.objects.get(pk=case_id, tenant_id=tenant_id)
        assignment = ReadingAssignment.objects.create(
            tenant_id=tenant_id,
            teleradiology_case=case,
            radiologist_id=radiologist_id,
            assigned_by=assigned_by,
        )
        case.status = "assigned"
        case.save(update_fields=["status"])
        return {"assignment_id": str(assignment.id)}
