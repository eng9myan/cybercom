from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from platform.api.permissions import IsAuthenticatedClinicalStaff as IsAuthenticated  # M-7: staff-role gate

from products.cymed.core.orders.models import Order, OrderStatus, OrderType
from products.cymed.core.patients.models import Patient
from products.cymed.core.providers.models import Provider
from products.cymed.core.providers.serializers import (
    PatientRosterSerializer,
    ProviderSerializer,
    ScheduleAppointmentSerializer,
)
from products.cymed.core.scheduling.models import Appointment, AppointmentParticipantType


class ProviderViewSet(viewsets.ModelViewSet):
    queryset = Provider.objects.filter(is_deleted=False)
    serializer_class = ProviderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def _current_provider(self, request):
        user_id = (getattr(request, "user_session", None) or {}).get("user_id")
        provider = self.get_queryset().filter(user_id=user_id).first() if user_id else None
        if provider is None:
            raise NotFound("No provider profile is linked to this account.")
        return provider

    def _active_patient_ids(self, tenant_id, provider):
        return list(
            Patient.objects.filter(
                tenant_id=tenant_id, is_active=True, encounters__participants__provider_id=provider.id
            ).distinct().values_list("id", flat=True)
        )

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        provider = self._current_provider(request)
        return Response(self.get_serializer(provider).data)

    @action(detail=False, methods=["get"], url_path="me/dashboard")
    def me_dashboard(self, request):
        from products.cymed.ai_cds.models import CDSAlert
        from products.cymed.ai_cds.serializers import CDSAlertSerializer
        from products.cymed.clinic.telemedicine.models import VirtualVisit
        from products.cymed.provider_portal.models import (
            ProviderCredentialingStatus,
            ProviderPortalProfile,
        )
        from products.cymed.provider_portal.serializers import (
            ProviderCredentialingStatusSerializer,
            ProviderPortalProfileSerializer,
        )

        tenant_id = request.tenant_id
        provider = self._current_provider(request)
        active_patient_ids = self._active_patient_ids(tenant_id, provider)

        todays_appointments = Appointment.objects.filter(
            tenant_id=tenant_id,
            start_time__date=date.today(),
            participants__actor_type=AppointmentParticipantType.PROVIDER,
            participants__actor_id=provider.id,
        ).distinct().count()

        # "Pending results for this provider" has no ordering-provider FK to
        # scope by (Order.ordered_by is free text) — scoped to the provider's
        # active patient panel instead, not to who placed the order.
        pending_results = Order.objects.filter(
            tenant_id=tenant_id,
            order_type__in=[OrderType.LABORATORY, OrderType.IMAGING],
            status=OrderStatus.ACTIVE,
            patient_id__in=active_patient_ids,
        ).count()

        telemedicine_queue = VirtualVisit.objects.filter(
            tenant_id=tenant_id, provider_id=provider.id, status__in=["scheduled", "in_progress"],
        ).count()

        recent_alerts = CDSAlert.objects.filter(
            tenant_id=tenant_id, patient_id__in=active_patient_ids, acknowledged_at__isnull=True,
        ).order_by("-severity", "-created_at")[:5]

        profile = ProviderPortalProfile.objects.filter(tenant_id=tenant_id, provider=provider).first()
        credentialing = ProviderCredentialingStatus.objects.filter(
            tenant_id=tenant_id, provider=provider
        ).first()

        return Response({
            "provider": ProviderSerializer(provider).data,
            "todays_appointments": todays_appointments,
            "active_patients": len(active_patient_ids),
            "pending_results": pending_results,
            "telemedicine_queue": telemedicine_queue,
            "recent_alerts": CDSAlertSerializer(recent_alerts, many=True).data,
            "profile": ProviderPortalProfileSerializer(profile).data if profile else None,
            "credentialing": ProviderCredentialingStatusSerializer(credentialing).data if credentialing else None,
        })

    @action(detail=False, methods=["get"], url_path="me/patients")
    def me_patients(self, request):
        tenant_id = request.tenant_id
        provider = self._current_provider(request)
        qs = Patient.objects.filter(
            tenant_id=tenant_id, encounters__participants__provider_id=provider.id
        ).distinct().order_by("last_name", "first_name")
        page = self.paginate_queryset(qs)
        serializer = PatientRosterSerializer(page if page is not None else qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="me/schedule")
    def me_schedule(self, request):
        tenant_id = request.tenant_id
        provider = self._current_provider(request)
        date_param = request.query_params.get("date")
        if date_param:
            try:
                target_date = date.fromisoformat(date_param)
            except ValueError:
                raise ValidationError({"date": "Must be YYYY-MM-DD."})
        else:
            target_date = date.today()

        qs = Appointment.objects.filter(
            tenant_id=tenant_id,
            start_time__date=target_date,
            participants__actor_type=AppointmentParticipantType.PROVIDER,
            participants__actor_id=provider.id,
        ).distinct().select_related("patient").order_by("start_time")

        return Response({
            "date": target_date.isoformat(),
            "appointments": ScheduleAppointmentSerializer(qs, many=True).data,
        })

    @action(detail=False, methods=["get"], url_path="me/orders")
    def me_orders(self, request):
        """
        Unified recent orders/results across lab, imaging and pharmacy —
        three separate apps with three separate models, none of which share
        a base serializer, so this returns plain normalized dicts rather
        than forcing an artificial common serializer on them.

        Lab and imaging orders carry a real `ordered_by` provider UUID;
        pharmacy's MedicationOrder is inpatient-only (requires admission_id)
        and carries `prescriber_id` instead — included on the same terms so
        an inpatient-facing provider sees their med orders here too.
        """
        from products.cymed.imaging.orders.models import ImagingOrder
        from products.cymed.laboratory.orders.models import LabOrder
        from products.cymed.pharmacy.prescriptions.models import MedicationOrder

        tenant_id = request.tenant_id
        provider = self._current_provider(request)
        limit = 50

        lab = LabOrder.objects.filter(tenant_id=tenant_id, ordered_by=provider.id)
        imaging = ImagingOrder.objects.filter(tenant_id=tenant_id, ordered_by=provider.id)
        medication = MedicationOrder.objects.filter(tenant_id=tenant_id, prescriber_id=provider.id)

        rows = []
        for kind, qs, label_field in (
            ("lab", lab, None),
            ("imaging", imaging, None),
            ("medication", medication, "drug_name"),
        ):
            for o in qs.order_by("-created_at")[:limit]:
                rows.append({
                    "id": str(o.id),
                    "kind": kind,
                    "order_number": o.order_number,
                    "patient_id": str(o.patient_id),
                    "label": getattr(o, label_field) if label_field else None,
                    "status": o.status,
                    "priority": o.priority,
                    "created_at": o.created_at,
                })

        rows.sort(key=lambda r: r["created_at"], reverse=True)
        rows = rows[:limit]

        patient_ids = {r["patient_id"] for r in rows}
        patients = {
            str(p.id): f"{p.first_name} {p.last_name}"
            for p in Patient.objects.filter(tenant_id=tenant_id, id__in=patient_ids)
        }
        for r in rows:
            r["patient_name"] = patients.get(r["patient_id"], "")
            r["created_at"] = r["created_at"].isoformat()

        return Response({"orders": rows})

    @action(detail=False, methods=["get"], url_path="me/telemedicine")
    def me_telemedicine(self, request):
        from products.cymed.clinic.telemedicine.models import VirtualVisit

        tenant_id = request.tenant_id
        provider = self._current_provider(request)
        status_param = request.query_params.get("status")

        qs = VirtualVisit.objects.filter(
            tenant_id=tenant_id, provider_id=provider.id
        ).select_related("patient")
        if status_param:
            qs = qs.filter(status=status_param)
        qs = qs.order_by("-scheduled_start")[:50]

        visits = []
        for v in qs:
            # VirtualSession is an optional OneToOne — a visit not yet
            # started has none. hasattr() safely absorbs the
            # RelatedObjectDoesNotExist Django raises on direct attribute
            # access, rather than a fragile try/except per row.
            has_session = hasattr(v, "session")
            visits.append({
                "id": str(v.id),
                "patient_name": f"{v.patient.first_name} {v.patient.last_name}",
                "patient_mrn": v.patient.mrn,
                "status": v.status,
                "scheduled_start": v.scheduled_start.isoformat(),
                "connection_url": v.session.connection_url if has_session else None,
            })

        return Response({"visits": visits})
