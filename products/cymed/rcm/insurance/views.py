from django.db import models
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    InsuranceCompany,
    InsurancePlan,
    InsuranceMember,
    Coverage,
    Benefit,
    CoverageRule,
    InsuranceCard,
)
from .serializers import (
    InsuranceCompanySerializer,
    InsurancePlanSerializer,
    InsuranceMemberSerializer,
    CoverageSerializer,
    BenefitSerializer,
    CoverageRuleSerializer,
    InsuranceCardSerializer,
)


class InsuranceCompanyViewSet(ModelViewSet):
    """
    ViewSet for managing insurance companies / payers.
    Supports CRUD and a `search` action for quick payer lookup.
    """

    queryset = InsuranceCompany.objects.all().order_by("name")
    serializer_class = InsuranceCompanySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["company_type", "is_active", "country"]
    search_fields = ["name", "short_name", "payer_id", "contact_email"]
    ordering_fields = ["name", "short_name", "company_type", "created_at"]
    ordering = ["name"]

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        """
        Dedicated search endpoint for insurance companies.
        Query param: ?q=<search_term>
        """
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response(
                {"detail": "Query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(
            models.Q(name__icontains=query)
            | models.Q(short_name__icontains=query)
            | models.Q(payer_id__icontains=query)
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class InsurancePlanViewSet(ModelViewSet):
    """
    ViewSet for managing insurance plans offered by insurance companies.
    """

    queryset = InsurancePlan.objects.select_related("company").order_by("company", "plan_name")
    serializer_class = InsurancePlanSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["company", "plan_type", "is_active", "network_type", "coverage_category"]
    search_fields = ["plan_name", "plan_code"]
    ordering_fields = ["plan_name", "plan_code", "plan_type", "effective_date", "created_at"]
    ordering = ["plan_name"]


class InsuranceMemberViewSet(ModelViewSet):
    """
    ViewSet for managing patient insurance memberships.
    """

    queryset = InsuranceMember.objects.select_related("insurance_plan__company").order_by("patient_id", "priority_order")
    serializer_class = InsuranceMemberSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["patient_id", "insurance_plan", "priority_order", "is_active", "member_relationship"]
    search_fields = ["member_id", "group_number"]
    ordering_fields = ["patient_id", "priority_order", "effective_date", "created_at"]
    ordering = ["patient_id", "priority_order"]


class CoverageViewSet(ModelViewSet):
    """
    ViewSet for managing coverage details for insurance members.
    """

    queryset = Coverage.objects.select_related("insurance_member").order_by("insurance_member", "coverage_type")
    serializer_class = CoverageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["insurance_member", "coverage_type", "is_active"]
    search_fields = ["fhir_coverage_id"]
    ordering_fields = ["coverage_type", "start_date", "end_date", "created_at"]
    ordering = ["coverage_type"]


class BenefitViewSet(ModelViewSet):
    """
    ViewSet for managing benefits within a coverage.
    """

    queryset = Benefit.objects.select_related("coverage").order_by("coverage", "service_category")
    serializer_class = BenefitSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["coverage", "requires_preauth"]
    search_fields = ["service_category"]
    ordering_fields = ["service_category", "coverage_percentage", "copay_amount", "created_at"]
    ordering = ["service_category"]


class CoverageRuleViewSet(ModelViewSet):
    """
    ViewSet for managing coverage rules at the insurance plan level.
    """

    queryset = CoverageRule.objects.select_related("insurance_plan").order_by("insurance_plan", "rule_type")
    serializer_class = CoverageRuleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["insurance_plan", "rule_type", "is_active"]
    search_fields = ["service_code", "rule_description"]
    ordering_fields = ["rule_type", "service_code", "created_at"]
    ordering = ["rule_type"]


class InsuranceCardViewSet(ModelViewSet):
    """
    ViewSet for managing digital copies of insurance cards stored in CyData.
    """

    queryset = InsuranceCard.objects.select_related("insurance_member").order_by("-created_at")
    serializer_class = InsuranceCardSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["insurance_member", "is_current"]
    search_fields = []
    ordering_fields = ["issued_date", "expiry_date", "created_at"]
    ordering = ["-created_at"]

