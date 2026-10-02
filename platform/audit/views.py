"""
Audit & Compliance API views.
"""

import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import (
    AuditArchive,
    AuditCategory,
    AuditChain,
    AuditEntry,
    AuditEvent,
    AuditExport,
    AuditLog,
    AuditRetentionPolicy,
    AuditSignature,
    ComplianceAssessment,
    ComplianceProfile,
    ComplianceReport,
    ComplianceRule,
    ComplianceViolation,
    EvidencePackage,
    EvidenceRecord,
    LegalHold,
)
from .permissions import (
    CanCreateLegalHold,
    CanReadAudit,
    caller_tenant_id,
    is_platform_admin,
    CanExportAuditLogs,
    CanReleaseLegalHold,
    IsAuditAdmin,
    IsComplianceOfficer,
    ReadOnlyOrAuditAdmin,
)
from .serializers import (
    AuditArchiveSerializer,
    AuditCategorySerializer,
    AuditChainSerializer,
    AuditEntrySerializer,
    AuditEventSerializer,
    AuditExportCreateSerializer,
    AuditExportSerializer,
    AuditLogSerializer,
    AuditRetentionPolicySerializer,
    AuditSearchSerializer,
    AuditSignatureSerializer,
    ChainVerifySerializer,
    ComplianceAssessmentSerializer,
    ComplianceProfileSerializer,
    ComplianceReportSerializer,
    ComplianceRuleSerializer,
    ComplianceViolationSerializer,
    EvidencePackageSealSerializer,
    EvidencePackageSerializer,
    EvidenceRecordSerializer,
    LegalHoldReleaseSerializer,
    LegalHoldSerializer,
    ViolationAcceptRiskSerializer,
    ViolationRemediateSerializer,
)
from .services import (
    AuditChainVerifier,
    AuditExportService,
    AuditMetrics,
    AuditSearchService,
    ComplianceAssessmentService,
    EvidenceService,
    LegalHoldService,
    ViolationService,
)

log = logging.getLogger(__name__)


class TenantScopedAuditMixin:
    """Every audit / compliance record is visible only within the caller's
    own tenant; platform admins see across tenants. A caller whose tenant
    can't be resolved sees nothing (fail closed). Previously these viewsets
    used Model.objects.all(), so any caller passing the role gate could read
    every tenant's audit trail."""

    # Scoping is done here (with the platform-admin cross-tenant view), so the
    # project-wide TenantScopeFilterBackend must not narrow it a second time.
    tenant_scope_exempt = True

    def get_queryset(self):
        qs = super().get_queryset()
        if not any(f.name == "tenant_id" for f in qs.model._meta.get_fields()):
            return qs
        if is_platform_admin(self.request):
            return qs
        tid = caller_tenant_id(self.request)
        return qs.filter(tenant_id=tid) if tid else qs.none()

    def _has_tenant(self, serializer) -> bool:
        return any(f.name == "tenant_id" for f in serializer.Meta.model._meta.get_fields())

    def perform_create(self, serializer):
        # A non-platform caller always writes into its own tenant, whatever
        # tenant_id the request body claims.
        if self._has_tenant(serializer) and not is_platform_admin(self.request):
            serializer.save(tenant_id=caller_tenant_id(self.request))
        else:
            serializer.save()

    def perform_update(self, serializer):
        if self._has_tenant(serializer) and not is_platform_admin(self.request):
            serializer.save(tenant_id=serializer.instance.tenant_id)
        else:
            serializer.save()


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


class AuditLogViewSet(TenantScopedAuditMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [ReadOnlyOrAuditAdmin]


class AuditEventViewSet(TenantScopedAuditMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.all()
    serializer_class = AuditEventSerializer
    permission_classes = [ReadOnlyOrAuditAdmin]

    @action(detail=False, methods=["post"], serializer_class=AuditSearchSerializer,
            permission_classes=[CanReadAudit])
    def search(self, request):
        ser = AuditSearchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        params = dict(ser.validated_data)
        if not is_platform_admin(request):
            tid = caller_tenant_id(request)
            if not tid:
                return Response([])
            params["tenant_id"] = tid          # never another tenant's trail
        events = AuditSearchService().search(**params)
        return Response(AuditEventSerializer(events, many=True).data)

    @action(
        detail=False,
        methods=["post"],
        serializer_class=ChainVerifySerializer,
        # read-only and tenant-scoped below, so audit readers may run it
        permission_classes=[CanReadAudit],
    )
    def verify_chain(self, request):
        ser = ChainVerifySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        verifier = AuditChainVerifier()
        chain_key = ser.validated_data.get("chain_key")
        if is_platform_admin(request):
            return Response(verifier.verify(chain_key) if chain_key else verifier.verify_all())
        # Tenant-level auditors verify only their own tenant's chains.
        own = AuditChain.objects.filter(tenant_id=caller_tenant_id(request))
        if chain_key:
            if not own.filter(chain_key=chain_key).exists():
                return Response({"valid": False, "error": "chain_not_found", "chain_key": chain_key})
            return Response(verifier.verify(chain_key))
        # same list shape as verify_all(), restricted to the caller's chains
        return Response([verifier.verify(k) for k in own.values_list("chain_key", flat=True)])


class AuditCategoryViewSet(TenantScopedAuditMixin, viewsets.ModelViewSet):
    queryset = AuditCategory.objects.all()
    serializer_class = AuditCategorySerializer
    permission_classes = [ReadOnlyOrAuditAdmin]


class AuditChainViewSet(TenantScopedAuditMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AuditChain.objects.all()
    serializer_class = AuditChainSerializer
    permission_classes = [IsAuditAdmin]


class AuditEntryViewSet(TenantScopedAuditMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AuditEntry.objects.all()
    serializer_class = AuditEntrySerializer
    permission_classes = [ReadOnlyOrAuditAdmin]


class AuditRetentionPolicyViewSet(TenantScopedAuditMixin, viewsets.ModelViewSet):
    queryset = AuditRetentionPolicy.objects.all()
    serializer_class = AuditRetentionPolicySerializer
    permission_classes = [ReadOnlyOrAuditAdmin]


class AuditArchiveViewSet(TenantScopedAuditMixin, viewsets.ModelViewSet):
    queryset = AuditArchive.objects.all()
    serializer_class = AuditArchiveSerializer
    permission_classes = [IsAuditAdmin]


class AuditSignatureViewSet(TenantScopedAuditMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AuditSignature.objects.all()
    serializer_class = AuditSignatureSerializer
    permission_classes = [IsAuditAdmin]


class AuditExportViewSet(TenantScopedAuditMixin, viewsets.ModelViewSet):
    queryset = AuditExport.objects.all()
    serializer_class = AuditExportSerializer
    permission_classes = [CanExportAuditLogs]

    def create(self, request):
        ser = AuditExportCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        svc = AuditExportService()
        export = svc.create_export(
            tenant_id=(ser.validated_data.get("tenant_id") if is_platform_admin(request)
                       else caller_tenant_id(request)),
            requested_by=str(getattr(request.user, "id", "system")),
            reason=ser.validated_data["reason"],
            filter_criteria=ser.validated_data.get("filter_criteria", {}),
            format=ser.validated_data.get("format", "json"),
            period_start=ser.validated_data.get("period_start"),
            period_end=ser.validated_data.get("period_end"),
        )
        return Response(AuditExportSerializer(export).data, status=status.HTTP_201_CREATED)


class LegalHoldViewSet(TenantScopedAuditMixin, viewsets.ModelViewSet):
    queryset = LegalHold.objects.all()
    serializer_class = LegalHoldSerializer
    permission_classes = [CanCreateLegalHold]

    @action(
        detail=True,
        methods=["post"],
        serializer_class=LegalHoldReleaseSerializer,
        permission_classes=[CanReleaseLegalHold],
    )
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


class ComplianceProfileViewSet(TenantScopedAuditMixin, viewsets.ModelViewSet):
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
        return Response(
            ComplianceAssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED
        )

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


class ComplianceRuleViewSet(TenantScopedAuditMixin, viewsets.ModelViewSet):
    queryset = ComplianceRule.objects.all()
    serializer_class = ComplianceRuleSerializer
    permission_classes = [IsComplianceOfficer]


class ComplianceViolationViewSet(TenantScopedAuditMixin, viewsets.ModelViewSet):
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


class ComplianceAssessmentViewSet(TenantScopedAuditMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ComplianceAssessment.objects.all()
    serializer_class = ComplianceAssessmentSerializer
    permission_classes = [IsComplianceOfficer]


class ComplianceReportViewSet(TenantScopedAuditMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ComplianceReport.objects.all()
    serializer_class = ComplianceReportSerializer
    permission_classes = [IsComplianceOfficer]


class EvidenceRecordViewSet(TenantScopedAuditMixin, viewsets.ModelViewSet):
    queryset = EvidenceRecord.objects.all()
    serializer_class = EvidenceRecordSerializer
    permission_classes = [IsAuditAdmin]

    @action(detail=True, methods=["post"])
    def lock(self, request, pk=None):
        record = self.get_object()
        record.lock()
        return Response(EvidenceRecordSerializer(record).data)


class EvidencePackageViewSet(TenantScopedAuditMixin, viewsets.ModelViewSet):
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
