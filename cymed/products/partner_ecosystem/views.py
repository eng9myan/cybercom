from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    LeadRegistration,
    MarketplaceExtension,
    Partner,
    PartnerApplication,
    PartnerCertification,
    PartnerPortalAccess,
)
from .serializers import (
    LeadRegistrationSerializer,
    MarketplaceExtensionSerializer,
    PartnerApplicationSerializer,
    PartnerCertificationSerializer,
    PartnerPortalAccessSerializer,
    PartnerSerializer,
)


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        serializer.save(tenant_id=getattr(self.request, "tenant_id", None))


class PartnerViewSet(BaseViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    filterset_fields = [
        "partner_type",
        "status",
        "tier",
        "country_code",
        "region",
        "assigned_am_id",
    ]
    search_fields = ["name", "code", "contact_name", "contact_email"]
    ordering_fields = ["name", "tier", "status", "joined_at", "created_at"]

    @action(detail=True, methods=["post"])
    def certify(self, request, pk=None):
        partner = self.get_object()
        partner.status = "certified"
        partner.save(update_fields=["status", "updated_at"])
        return Response({"status": "certified", "id": str(partner.id)})

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        partner = self.get_object()
        partner.status = "suspended"
        partner.save(update_fields=["status", "updated_at"])
        return Response({"status": "suspended", "id": str(partner.id)})


class PartnerApplicationViewSet(BaseViewSet):
    queryset = PartnerApplication.objects.all()
    serializer_class = PartnerApplicationSerializer
    filterset_fields = ["partner_type", "status", "country_code"]
    search_fields = ["partner_name", "contact_name", "contact_email", "organization"]
    ordering_fields = ["submitted_at", "decided_at", "created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        application = self.get_object()
        application.status = "approved"
        application.reviewed_by_id = request.data.get("reviewed_by_id")
        application.review_notes = request.data.get("review_notes", application.review_notes)
        application.decided_at = timezone.now()
        application.save(
            update_fields=["status", "reviewed_by_id", "review_notes", "decided_at", "updated_at"]
        )
        return Response(
            {"status": "approved", "decided_at": application.decided_at, "id": str(application.id)}
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        application = self.get_object()
        application.status = "rejected"
        application.reviewed_by_id = request.data.get("reviewed_by_id")
        application.review_notes = request.data.get("review_notes", application.review_notes)
        application.decided_at = timezone.now()
        application.save(
            update_fields=["status", "reviewed_by_id", "review_notes", "decided_at", "updated_at"]
        )
        return Response(
            {"status": "rejected", "decided_at": application.decided_at, "id": str(application.id)}
        )


class PartnerCertificationViewSet(BaseViewSet):
    queryset = PartnerCertification.objects.select_related("partner")
    serializer_class = PartnerCertificationSerializer
    filterset_fields = ["partner", "product_code", "certification_type", "status"]
    search_fields = ["product_code"]
    ordering_fields = ["issued_at", "expires_at", "created_at"]


class LeadRegistrationViewSet(BaseViewSet):
    queryset = LeadRegistration.objects.select_related("partner")
    serializer_class = LeadRegistrationSerializer
    filterset_fields = ["partner", "status", "country_code"]
    search_fields = ["lead_name", "lead_organization", "lead_email"]
    ordering_fields = ["approved_at", "expires_at", "estimated_value", "created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        lead = self.get_object()
        lead.status = "approved"
        lead.approved_by_id = request.data.get("approved_by_id")
        lead.approved_at = timezone.now()
        lead.save(update_fields=["status", "approved_by_id", "approved_at", "updated_at"])
        return Response({"status": "approved", "approved_at": lead.approved_at, "id": str(lead.id)})

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        lead = self.get_object()
        lead.status = "converted"
        lead.save(update_fields=["status", "updated_at"])
        return Response({"status": "converted", "id": str(lead.id)})


class MarketplaceExtensionViewSet(BaseViewSet):
    queryset = MarketplaceExtension.objects.select_related("partner")
    serializer_class = MarketplaceExtensionSerializer
    filterset_fields = ["partner", "category", "status", "price_model"]
    search_fields = ["extension_name", "code", "description"]
    ordering_fields = ["extension_name", "install_count", "published_at", "created_at"]

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        extension = self.get_object()
        extension.status = "published"
        extension.published_at = timezone.now()
        extension.save(update_fields=["status", "published_at", "updated_at"])
        return Response(
            {"status": "published", "published_at": extension.published_at, "id": str(extension.id)}
        )

    @action(detail=True, methods=["post"])
    def deprecate(self, request, pk=None):
        extension = self.get_object()
        extension.status = "deprecated"
        extension.save(update_fields=["status", "updated_at"])
        return Response({"status": "deprecated", "id": str(extension.id)})

    @action(detail=True, methods=["post"])
    def record_install(self, request, pk=None):
        extension = self.get_object()
        extension.install_count += 1
        extension.save(update_fields=["install_count", "updated_at"])
        return Response({"install_count": extension.install_count, "id": str(extension.id)})


class PartnerPortalAccessViewSet(BaseViewSet):
    queryset = PartnerPortalAccess.objects.select_related("partner")
    serializer_class = PartnerPortalAccessSerializer
    filterset_fields = ["partner", "user_id", "access_level", "is_active"]
    ordering_fields = ["last_login_at", "created_at"]
