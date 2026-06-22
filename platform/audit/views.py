"""
Audit & Compliance API views.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import (
    AuditArchive, AuditCategory, AuditChain, AuditEntry, AuditEvent, AuditExport,
    AuditLog, AuditRetentionPolicy, AuditSignature,
    ComplianceAssessment, ComplianceProfile, ComplianceReport, ComplianceRule,
    ComplianceViolation, EvidencePackage, EvidenceRecord, LegalHold,
)
from .permissions import (
    CanCreateLegalHold, CanExportAuditLogs, CanReleaseLegalHold,
    IsAuditAdmin, IsComplianceOfficer, ReadOnlyOrAuditAdmin,
)
from .serializers import (
    AuditArchiveSerializer, AuditCategorySerializer, AuditChainSerializer,
    AuditEntrySerializer, AuditEventSerializer, AuditExportCreateSerializer,
    AuditExportSerializer, AuditLogSerializer, AuditRetentionPolicySerializer,
    AuditSearchSerializer, AuditSignatureSerializer, ChainVerifySerializer,
    ComplianceAssessmentSerializer, ComplianceProfileSerializer, ComplianceReportSerializer,
    ComplianceRuleSerializer, ComplianceViolationSerializer,
    EvidencePackageSealSerializer, EvidencePackageSerializer, EvidenceRecordSerializer,
    LegalHoldReleaseSerializer, LegalHoldSerializer,
    ViolationAcceptRiskSerializer, ViolationRemediateSerializer,
)
from .services import (
    AuditChainVerifier, AuditExportService, AuditMetrics, AuditSearchService,
    ComplianceAssessmentService, ComplianceProfileService,
    EvidenceService, LegalHoldService, ViolationService,
)

log = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def audit_health(request):
    total = AuditEvent.objects.count()
    return Response({"status": "ok", "total_audit_events": total})


@api_view(["GET"])
@permission_classes([AllowAny])
def audit_metrics(request):
    from django.http import HttpResponse
    payload = AuditMetrics().render_prometheus()
    return HttpResponse(payload, content_type="text/plain; version=0.0.4")


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [ReadOnlyOrAuditAdmin]


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.all()
    serializer_class = AuditEventSerializer
    permission_classes = [ReadOnlyOrAuditAdmin]

    @action(detail=False, methods=["post"], serializer_class=AuditSearchSerializer)
    def search(self, request):
        ser = AuditSearchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        svc = AuditSearchService()
        events = svc.search(**ser.validated_data)
        return Response(AuditEventSerializer(events, many=True).data)

    @action(detail=False, methods=["post"], serializer_class=ChainVerifySerializer,
            permission_classes=[IsAuditAdmin])
    def verify_chain(self, request):
        ser = ChainVerifySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        verifier = AuditChainVerifier()
        chain_key = ser.validated_data.get("chain_key")
        if chain_key:
            result = verifier.verify(chain_key)
        else:
            result = verifier.verify_all()
        return Response(result)


class AuditCategoryViewSet(viewsets.ModelViewSet):
    queryset = AuditCategory.objects.all()
    serializer_class = AuditCategorySerializer
    permission_classes = [ReadOnlyOrAuditAdmin]


class AuditChainViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditChain.objects.all()
    serializer_class = AuditChainSerializer
    permission_classes = [IsAuditAdmin]


class AuditEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEntry.objects.all()
    serializer_class = AuditEntrySerializer
    permission_classes = [ReadOnlyOrAuditAdmin]


class AuditRetentionPolicyViewSet(viewsets.ModelViewSet):
    queryset = AuditRetentionPolicy.objects.all()
    serializer_class = AuditRetentionPolicySerializer
    permission_classes = [ReadOnlyOrAuditAdmin]


class AuditArchiveViewSet(viewsets.ModelViewSet):
    queryset = AuditArchive.objects.all()
    serializer_class = AuditArchiveSerializer
    permission_classes = [IsAuditAdmin]


class AuditSignatureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditSignature.objects.all()
    serializer_class = AuditSignatureSerializer
    permission_classes = [IsAuditAdmin]


class AuditExportViewSet(viewsets.ModelViewSet):
    queryset = AuditExport.objects.all()
    serializer_class = AuditExportSerializer
    permission_classes = [CanExportAuditLogs]

    def create(self, request):
        ser = AuditExportCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        svc = AuditExportService()
        export = svc.create_export(
            tenant_id=ser.validated_data.get("tenant_id"),
            requested_by=str(getattr(request.user, "id", "system")),
            reason=ser.validated_data["reason"],
            filter_criteria=ser.validated_data.get("filter_criteria", {}),
            format=ser.validated_data.get("format", "json"),
            period_start=ser.validated_data.get("period_start"),
            period_end=ser.validated_data.get("period_end"),
        )
        return Response(AuditExportSerializer(export).data, status=status.HTTP_201_CREATED)


class LegalHoldViewSet(viewsets.ModelViewSet):
    queryset = LegalHold.objects.all()
    serializer_class = LegalHoldSerializer
    permission_classes = [CanCreateLegalHold]

    @action(detail=True, methods=["post"], serializer_class=LegalHoldReleaseSerializer,
            permission_classes=[CanReleaseLegalHold])
    def release(self, request, pk=None):
        hold = self.get_object()
        ser = LegalHoldReleaseSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        svc = LegalHoldService()
        try:
            svc.release(hold, **ser.validated_data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LegalHoldSerializer(hold).data)


class ComplianceProfileViewSet(viewsets.ModelViewSet):
    queryset = ComplianceProfile.objects.all()
    serializer_class = ComplianceProfileSerializer
    permission_classes = [IsComplianceOfficer]

    @action(detail=True, methods=["post"], permission_classes=[IsComplianceOfficer])
    def assess(self, request, pk=None):
        profile = self.get_object()
        svc = ComplianceAssessmentService()
        assessment = svc.assess(
            profile=profile,
            tenant_id=profile.tenant_id,
            assessed_by=str(getattr(request.user, "id", "system")),
        )
        return Response(ComplianceAssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsComplianceOfficer])
    def generate_report(self, request, pk=None):
        profile = self.get_object()
        svc = ComplianceAssessmentService()
        report = svc.generate_report(
            framework=profile.framework,
            tenant_id=profile.tenant_id,
            generated_by=str(getattr(request.user, "id", "system")),
        )
        return Response(ComplianceReportSerializer(report).data, status=status.HTTP_201_CREATED)


class ComplianceRuleViewSet(viewsets.ModelViewSet):
    queryset = ComplianceRule.objects.all()
    serializer_class = ComplianceRuleSerializer
    permission_classes = [IsComplianceOfficer]


class ComplianceViolationViewSet(viewsets.ModelViewSet):
    queryset = ComplianceViolation.objects.all()
    serializer_class = ComplianceViolationSerializer
    permission_classes = [IsComplianceOfficer]

    @action(detail=True, methods=["post"], serializer_class=ViolationRemediateSerializer)
    def remediate(self, request, pk=None):
        violation = self.get_object()
        ser = ViolationRemediateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ViolationService().remediate(violation, **ser.validated_data)
        return Response(ComplianceViolationSerializer(violation).data)

    @action(detail=True, methods=["post"], serializer_class=ViolationAcceptRiskSerializer)
    def accept_risk(self, request, pk=None):
        violation = self.get_object()
        ser = ViolationAcceptRiskSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ViolationService().accept_risk(violation, **ser.validated_data)
        return Response(ComplianceViolationSerializer(violation).data)


class ComplianceAssessmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ComplianceAssessment.objects.all()
    serializer_class = ComplianceAssessmentSerializer
    permission_classes = [IsComplianceOfficer]


class ComplianceReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ComplianceReport.objects.all()
    serializer_class = ComplianceReportSerializer
    permission_classes = [IsComplianceOfficer]


class EvidenceRecordViewSet(viewsets.ModelViewSet):
    queryset = EvidenceRecord.objects.all()
    serializer_class = EvidenceRecordSerializer
    permission_classes = [IsAuditAdmin]

    @action(detail=True, methods=["post"])
    def lock(self, request, pk=None):
        record = self.get_object()
        record.lock()
        return Response(EvidenceRecordSerializer(record).data)


class EvidencePackageViewSet(viewsets.ModelViewSet):
    queryset = EvidencePackage.objects.all()
    serializer_class = EvidencePackageSerializer
    permission_classes = [IsAuditAdmin]

    @action(detail=True, methods=["post"], serializer_class=EvidencePackageSealSerializer)
    def seal(self, request, pk=None):
        package = self.get_object()
        ser = EvidencePackageSealSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            EvidenceService().seal_package(package, sealed_by=ser.validated_data["sealed_by"])
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(EvidencePackageSerializer(package).data)
