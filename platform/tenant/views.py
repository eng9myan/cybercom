"""
CyberCom Multi-Tenant Framework — REST API Views.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle


class DemoRequestThrottle(AnonRateThrottle):
    scope = "website_demo_request"

from platform.tenant.models import (
    Tenant,
    TenantAuditConfiguration,
    TenantBranding,
    TenantComplianceProfile,
    TenantConfiguration,
    TenantDeploymentProfile,
    TenantDomain,
    TenantEnvironment,
    TenantFeatureFlag,
    TenantLicense,
    TenantProfile,
    TenantRegion,
    TenantRetentionPolicy,
    TenantSSOConfiguration,
    TenantStatus,
    TenantStoragePolicy,
    TenantSubscription,
)
from platform.tenant.permissions import (
    CanProvisionTenant,
    CanTerminateTenant,
    IsPlatformAdmin,
    ReadOnlyOrPlatformAdmin,
)
from platform.tenant.serializers import (
    DemoProvisionSerializer,
    SubscriptionRegisterSerializer,
    TenantAuditConfigurationSerializer,
    TenantBootstrapSerializer,
    TenantBrandingSerializer,
    TenantComplianceProfileSerializer,
    TenantConfigurationSerializer,
    TenantCreateSerializer,
    TenantDeploymentProfileSerializer,
    TenantDomainSerializer,
    TenantEnvironmentSerializer,
    TenantFeatureFlagSerializer,
    TenantFeatureFlagToggleSerializer,
    TenantLicenseSerializer,
    TenantProfileSerializer,
    TenantRealmAssignSerializer,
    TenantRegionSerializer,
    TenantRetentionPolicySerializer,
    TenantSerializer,
    TenantSSOConfigurationSerializer,
    TenantStoragePolicySerializer,
    TenantSubscriptionSerializer,
    TenantSuspendSerializer,
    TenantTerminateSerializer,
)
from platform.tenant.services import (
    SANDBOX_TRIAL_HOURS,
    DemoProvisioningService,
    SubscriptionRegistrationService,
    TenantBootstrapRequest,
    TenantBootstrapService,
    TenantDomainService,
    TenantFeatureFlagService,
    TenantLifecycleService,
    TenantRealmMappingService,
    render_prometheus,
)

# Product codes that are always sales-assisted, never self-serve demo.
DEMO_EXCLUDED_PRODUCTS = {"cymed_hospital"}

# ---------------------------------------------------------------------------
# Health + Metrics
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([AllowAny])
def tenant_health(request):
    try:
        count = Tenant.objects.filter(status=TenantStatus.ACTIVE).count()
        db_ok = True
    except Exception:
        count = 0
        db_ok = False

    return Response(
        {
            "status": "ok" if db_ok else "degraded",
            "active_tenants": count,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def tenant_metrics(request):
    return Response(render_prometheus(), content_type="text/plain; version=0.0.4")


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([DemoRequestThrottle])
def demo_provision(request):
    """Public self-serve 72-hour trial signup. Hospital is sales-assisted only."""
    ser = DemoProvisionSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    if d["product_code"] in DEMO_EXCLUDED_PRODUCTS:
        return Response(
            {
                "detail": "This product is sales-assisted only. Please use the contact form.",
                "contact_required": True,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    tenant, user = DemoProvisioningService().provision_demo(
        product_code=d["product_code"],
        email=d["email"],
        org_name=d.get("org_name", ""),
        locale=d.get("locale", "en"),
        trial_hours=SANDBOX_TRIAL_HOURS if d.get("sandbox") else None,
    )
    subscription = tenant.subscriptions.first()

    if user is None:
        # cyshop adapter path — no CyIdentity realm/user, cyshop has its own
        # separate login. See DemoProvisioningService._provision_demo_cyshop.
        return Response(
            {
                "tenant_slug": tenant.slug,
                "product_code": d["product_code"],
                "cyshop_subdomain": getattr(tenant, "demo_subdomain", None),
                "username": getattr(tenant, "demo_username", None),
                "password": getattr(tenant, "demo_password", None),
                "trial_ends_at": subscription.trial_ends_at.isoformat() if subscription else None,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {
            "tenant_slug": tenant.slug,
            "realm_name": user.realm.realm_name,
            "username": user.username,
            # provision_user() now always sets a real Keycloak password (it
            # never did before — see services.py) — must be returned here since
            # it's never persisted anywhere; this is the only chance to hand it
            # to the person who just signed up.
            "password": getattr(tenant, "demo_password", None),
            "trial_ends_at": subscription.trial_ends_at.isoformat() if subscription else None,
        },
        status=status.HTTP_201_CREATED,
    )


class SubscriptionRequestThrottle(AnonRateThrottle):
    scope = "website_public_write"


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([SubscriptionRequestThrottle])
def subscription_register(request):
    """Public self-serve subscription signup: unified Basic/Pro/Enterprise
    tiers across every product except hospital (sales-assisted only, same
    exclusion demo_provision enforces). Creates a real, permanent tenant
    (status=pending) plus a real bank-transfer-pending invoice — no card
    payment is actually processed by this endpoint."""
    ser = SubscriptionRegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    if d["product_code"] in DEMO_EXCLUDED_PRODUCTS:
        return Response(
            {
                "detail": "This product is sales-assisted only. Please use the contact form.",
                "contact_required": True,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    tenant, subscription, invoice = SubscriptionRegistrationService().register(
        product_code=d["product_code"],
        tier=d["tier"],
        email=d["email"],
        org_name=d.get("org_name", ""),
        locale=d.get("locale", "en"),
    )

    return Response(
        {
            "tenant_slug": tenant.slug,
            "product_code": d["product_code"],
            "tier": subscription.plan,
            "invoice_number": invoice.invoice_number,
            "amount": str(invoice.amount),
            "currency": invoice.currency,
            "payment_method": invoice.payment_method,
            "due_date": invoice.due_date.isoformat(),
            "status": "pending_approval",
            "username": getattr(tenant, "demo_username", None),
            "password": getattr(tenant, "demo_password", None),
        },
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# TenantViewSet — main CRUD + lifecycle actions
# ---------------------------------------------------------------------------


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all().order_by("name")
    permission_classes = [ReadOnlyOrPlatformAdmin]

    def get_serializer_class(self):
        if self.action == "create":
            return TenantCreateSerializer
        return TenantSerializer

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[CanProvisionTenant],
        url_path="bootstrap",
    )
    def bootstrap(self, request):
        ser = TenantBootstrapSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        req = TenantBootstrapRequest(
            name=d["name"],
            slug=d["slug"],
            display_name=d.get("display_name", ""),
            tenant_type=d.get("tenant_type", "saas"),
            tier=d.get("tier", "shared"),
            country_code=d.get("country_code", "SA"),
            locale=d.get("locale", "ar"),
            home_region=d.get("home_region", "me-central-1"),
            plan=d.get("plan", "professional"),
            compliance_frameworks=d.get("compliance_frameworks", []),
            contact_email=d.get("contact_email", ""),
        )
        tenant = TenantBootstrapService().bootstrap(req, created_by=str(request.user))
        return Response(TenantSerializer(tenant).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True, methods=["post"], permission_classes=[IsPlatformAdmin], url_path="activate"
    )
    def activate(self, request, pk=None):
        tenant = self.get_object()
        TenantLifecycleService().activate(tenant, by=str(request.user))
        return Response(TenantSerializer(tenant).data)

    @action(detail=True, methods=["post"], permission_classes=[IsPlatformAdmin], url_path="suspend")
    def suspend(self, request, pk=None):
        tenant = self.get_object()
        ser = TenantSuspendSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        TenantLifecycleService().suspend(
            tenant, reason=ser.validated_data.get("reason", ""), by=str(request.user)
        )
        return Response(TenantSerializer(tenant).data)

    @action(detail=True, methods=["post"], permission_classes=[IsPlatformAdmin], url_path="archive")
    def archive(self, request, pk=None):
        tenant = self.get_object()
        TenantLifecycleService().archive(tenant, by=str(request.user))
        return Response(TenantSerializer(tenant).data)

    @action(detail=True, methods=["post"], permission_classes=[IsPlatformAdmin], url_path="restore")
    def restore(self, request, pk=None):
        tenant = self.get_object()
        try:
            TenantLifecycleService().restore(tenant, by=str(request.user))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TenantSerializer(tenant).data)

    @action(
        detail=True, methods=["post"], permission_classes=[CanTerminateTenant], url_path="terminate"
    )
    def terminate(self, request, pk=None):
        tenant = self.get_object()
        ser = TenantTerminateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        TenantLifecycleService().terminate(
            tenant, reason=ser.validated_data["reason"], by=str(request.user)
        )
        return Response(TenantSerializer(tenant).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[CanTerminateTenant],
        url_path="decommission",
    )
    def decommission(self, request, pk=None):
        tenant = self.get_object()
        try:
            TenantLifecycleService().decommission(tenant, by=str(request.user))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TenantSerializer(tenant).data)

    @action(
        detail=True, methods=["post"], permission_classes=[IsPlatformAdmin], url_path="assign-realm"
    )
    def assign_realm(self, request, pk=None):
        tenant = self.get_object()
        ser = TenantRealmAssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        TenantRealmMappingService().assign_realm(
            tenant,
            ser.validated_data["realm_id"],
            ser.validated_data["realm_name"],
        )
        return Response(TenantSerializer(tenant).data)


# ---------------------------------------------------------------------------
# Sub-resource ViewSets
# ---------------------------------------------------------------------------


class TenantProfileViewSet(viewsets.ModelViewSet):
    queryset = TenantProfile.objects.all()
    serializer_class = TenantProfileSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantConfigurationViewSet(viewsets.ModelViewSet):
    queryset = TenantConfiguration.objects.all()
    serializer_class = TenantConfigurationSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantBrandingViewSet(viewsets.ModelViewSet):
    queryset = TenantBranding.objects.all()
    serializer_class = TenantBrandingSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = TenantSubscription.objects.all()
    serializer_class = TenantSubscriptionSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantLicenseViewSet(viewsets.ModelViewSet):
    queryset = TenantLicense.objects.all()
    serializer_class = TenantLicenseSerializer
    permission_classes = [IsPlatformAdmin]


class TenantEnvironmentViewSet(viewsets.ModelViewSet):
    queryset = TenantEnvironment.objects.all()
    serializer_class = TenantEnvironmentSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantRegionViewSet(viewsets.ModelViewSet):
    queryset = TenantRegion.objects.all()
    serializer_class = TenantRegionSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantDeploymentProfileViewSet(viewsets.ModelViewSet):
    queryset = TenantDeploymentProfile.objects.all()
    serializer_class = TenantDeploymentProfileSerializer
    permission_classes = [IsPlatformAdmin]


class TenantFeatureFlagViewSet(viewsets.ModelViewSet):
    queryset = TenantFeatureFlag.objects.all()
    serializer_class = TenantFeatureFlagSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]

    @action(detail=False, methods=["post"], url_path="toggle")
    def toggle(self, request):
        ser = TenantFeatureFlagToggleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        tenant_id = request.data.get("tenant_id")
        tenant = Tenant.objects.get(pk=tenant_id)
        svc = TenantFeatureFlagService()
        if ser.validated_data["enabled"]:
            flag = svc.enable(
                tenant,
                ser.validated_data["key"],
                by=str(request.user),
                value=ser.validated_data.get("value"),
            )
        else:
            flag = svc.disable(tenant, ser.validated_data["key"])
        return Response(TenantFeatureFlagSerializer(flag).data)


class TenantDomainViewSet(viewsets.ModelViewSet):
    queryset = TenantDomain.objects.all()
    serializer_class = TenantDomainSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        domain_obj = self.get_object()
        TenantDomainService().verify_domain(domain_obj)
        return Response(TenantDomainSerializer(domain_obj).data)


class TenantSSOConfigurationViewSet(viewsets.ModelViewSet):
    queryset = TenantSSOConfiguration.objects.all()
    serializer_class = TenantSSOConfigurationSerializer
    permission_classes = [IsPlatformAdmin]


class TenantStoragePolicyViewSet(viewsets.ModelViewSet):
    queryset = TenantStoragePolicy.objects.all()
    serializer_class = TenantStoragePolicySerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantRetentionPolicyViewSet(viewsets.ModelViewSet):
    queryset = TenantRetentionPolicy.objects.all()
    serializer_class = TenantRetentionPolicySerializer
    permission_classes = [IsPlatformAdmin]


class TenantComplianceProfileViewSet(viewsets.ModelViewSet):
    queryset = TenantComplianceProfile.objects.all()
    serializer_class = TenantComplianceProfileSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantAuditConfigurationViewSet(viewsets.ModelViewSet):
    queryset = TenantAuditConfiguration.objects.all()
    serializer_class = TenantAuditConfigurationSerializer
    permission_classes = [IsPlatformAdmin]
