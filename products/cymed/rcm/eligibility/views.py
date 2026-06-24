from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    EligibilityRequest,
    EligibilityResponse,
    CoverageVerification,
    BenefitVerification,
)
from .serializers import (
    EligibilityRequestSerializer,
    EligibilityResponseSerializer,
    CoverageVerificationSerializer,
    CoverageVerificationWriteSerializer,
    BenefitVerificationSerializer,
)


class EligibilityRequestViewSet(ModelViewSet):
    """
    ViewSet for managing eligibility requests.
    Supports CRUD operations and a `submit` action to send a request to the payer.
    """

    queryset = EligibilityRequest.objects.all().order_by("-created_at")
    serializer_class = EligibilityRequestSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["patient_id", "status", "service_date", "service_type", "request_type"]
    search_fields = ["payer_transaction_id", "fhir_coverage_eligibility_request_id"]
    ordering_fields = ["created_at", "service_date", "status"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        """
        Submit an eligibility request to the payer.
        Transitions status from 'pending' to 'submitted'.
        Integration with external payer API should be triggered here.
        """
        eligibility_request = self.get_object()

        if eligibility_request.status != "pending":
            return Response(
                {"detail": f"Cannot submit a request with status '{eligibility_request.status}'. Only 'pending' requests can be submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Transition status to submitted
        eligibility_request.status = "submitted"
        eligibility_request.save(update_fields=["status", "updated_at"])

        serializer = self.get_serializer(eligibility_request)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EligibilityResponseViewSet(ModelViewSet):
    """
    ViewSet for managing eligibility responses received from payers.
    """

    queryset = EligibilityResponse.objects.all().order_by("-created_at")
    serializer_class = EligibilityResponseSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["eligibility_request", "is_eligible", "coverage_status"]
    search_fields = ["fhir_coverage_eligibility_response_id"]
    ordering_fields = ["created_at", "coverage_start_date", "coverage_end_date"]
    ordering = ["-created_at"]


class CoverageVerificationViewSet(ModelViewSet):
    """
    ViewSet for managing coverage verifications.
    Supports CRUD operations and a `verify` action to mark a verification as complete.
    """

    queryset = CoverageVerification.objects.prefetch_related("benefit_verifications").order_by("-created_at")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["patient_id", "encounter_id", "insurance_plan_id", "coverage_confirmed", "verification_method"]
    search_fields = ["notes"]
    ordering_fields = ["created_at", "verified_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CoverageVerificationSerializer
        return CoverageVerificationWriteSerializer

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        """
        Mark a coverage verification as verified.
        Sets verified_at timestamp and coverage_confirmed flag.
        """
        coverage_verification = self.get_object()

        coverage_verification.coverage_confirmed = True
        coverage_verification.verified_at = timezone.now()
        if request.user and request.user.is_authenticated:
            coverage_verification.verified_by_user_id = request.user.id

        coverage_verification.save(update_fields=["coverage_confirmed", "verified_at", "verified_by_user_id", "updated_at"])

        serializer = CoverageVerificationSerializer(coverage_verification)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BenefitVerificationViewSet(ModelViewSet):
    """
    ViewSet for managing benefit verifications nested under coverage verifications.
    """

    queryset = BenefitVerification.objects.all().order_by("benefit_type")
    serializer_class = BenefitVerificationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["coverage_verification", "benefit_type", "is_covered", "requires_preauth", "network_status"]
    search_fields = ["benefit_notes"]
    ordering_fields = ["benefit_type", "created_at"]
    ordering = ["benefit_type"]
