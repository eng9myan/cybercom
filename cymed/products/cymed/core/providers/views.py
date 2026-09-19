from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from platform.api.permissions import IsAuthenticatedClinicalStaff as IsAuthenticated  # M-7: staff-role gate

from products.cymed.core.orders.models import Order, OrderStatus, OrderType
from products.cymed.core.patients.models import Patient
from products.cymed.core.providers.models import Provider
from products.cymed.core.providers.serializers import PatientRosterSerializer, ProviderSerializer
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
