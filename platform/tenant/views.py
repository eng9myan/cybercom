"""
CyberCom Multi-Tenant Framework — REST API Views.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from platform.canonical import flavors


class DemoRequestThrottle(AnonRateThrottle):
    scope = "website_demo_request"

from platform.tenant.models import (
    InvoicePaymentMethod,
    InvoiceStatus,
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
    TenantSubscriptionInvoice,
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
    TenantFlavorActionSerializer,
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
    SUPPORTED_CURRENCIES,
    DemoProvisioningService,
    SubscriptionRegistrationService,
    TenantBootstrapRequest,
    TenantBootstrapService,
    TenantDomainService,
    TenantFeatureFlagService,
    TenantLifecycleService,
    TenantRealmMappingService,
    activate_paid_subscription,
    render_prometheus,
    subscription_pricing,
)
from platform.tenant.payments import (
    PaymentError,
    PaymentProviderNotConfigured,
    WebhookVerificationError,
    active_provider_code,
    get_payment_provider,
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
        currency=d.get("currency", ""),
        country=d.get("country", ""),
    )

    # Start a checkout with the active provider. The manual provider returns
    # bank-transfer instructions (no online charge); an online gateway returns
    # a redirect URL or client secret. A provider misconfiguration must not lose
    # the already-created invoice, so fall back to manual instructions.
    checkout = None
    try:
        checkout = get_payment_provider().create_checkout(invoice).as_dict()
    except PaymentError as exc:
        checkout = {"provider": invoice.provider, "mode": "manual", "error": str(exc)}

    # Manual / bank-transfer invoices sit with finance until the transfer is
    # confirmed; an online gateway checkout is waiting on the payer. The tenant
    # stays PENDING either way, but the label reflects who acts next.
    reg_status = (
        "pending_approval"
        if checkout.get("mode") == "manual"
        or invoice.payment_method == InvoicePaymentMethod.BANK_TRANSFER
        else "pending_payment"
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
            "provider": invoice.provider,
            "due_date": invoice.due_date.isoformat(),
            "status": reg_status,
            "checkout": checkout,
            "username": getattr(tenant, "demo_username", None),
            "password": getattr(tenant, "demo_password", None),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def pricing_config(request):
    """Public pricing + active-provider config for the website pricing page.

    No secrets: returns the tier catalog per supported currency and the
    provider's publishable key only (never the secret key)."""
    catalog = subscription_pricing()
    tiers = [
        {
            "code": code,
            "display_name": entry["display_name"],
            "prices": entry["prices"],
        }
        for code, entry in catalog.items()
    ]
    publishable = ""
    try:
        publishable = getattr(get_payment_provider(), "publishable_key", "") or ""
    except PaymentError:
        publishable = ""
    return Response(
        {
            "currencies": list(SUPPORTED_CURRENCIES),
            "default_currency": SUPPORTED_CURRENCIES[0],
            "tiers": tiers,
            "provider": active_provider_code(),
            "publishable_key": publishable,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([SubscriptionRequestThrottle])
def payment_webhook(request, provider: str):
    """Inbound gateway webhook. Verifies the event, and on a confirmed payment
    activates the subscription through the single activation path. Idempotent —
    gateways retry."""
    try:
        prov = get_payment_provider(provider)
    except PaymentError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    raw_body = request.body
    headers = {k: v for k, v in request.headers.items()}
    try:
        event = prov.parse_webhook(body=raw_body, headers=headers)
    except WebhookVerificationError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if not event.paid:
        return Response({"detail": "event acknowledged (not a paid event)"}, status=status.HTTP_200_OK)

    try:
        invoice = TenantSubscriptionInvoice.objects.get(invoice_number=event.invoice_number)
    except TenantSubscriptionInvoice.DoesNotExist:
        return Response({"detail": "unknown invoice"}, status=status.HTTP_404_NOT_FOUND)

    if event.provider_ref and invoice.provider_ref != event.provider_ref:
        invoice.provider_ref = event.provider_ref
        invoice.save(update_fields=["provider_ref", "updated_at"])

    tenant = activate_paid_subscription(invoice, approved_by=f"gateway:{provider}")
    return Response(
        {"tenant_slug": tenant.slug, "invoice_number": invoice.invoice_number, "status": "active"},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([SubscriptionRequestThrottle])
def payment_verify(request, provider: str):
    """Redirect-return path for gateways that hand the browser back with a
    checkout id (HyperPay COPYandPAY). Verifies the result server-side and,
    on a confirmed payment, activates the subscription through the single
    activation path. Idempotent."""
    try:
        prov = get_payment_provider(provider)
    except PaymentError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    verify = getattr(prov, "verify_payment", None)
    if verify is None:
        return Response(
            {"detail": f"provider '{provider}' has no redirect-return verification"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    checkout_id = request.data.get("checkout_id") or request.GET.get("id") or ""
    try:
        event = verify(checkout_id)
    except (PaymentError, WebhookVerificationError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if not event.paid:
        return Response({"detail": "payment not completed", "status": "pending"},
                        status=status.HTTP_200_OK)

    try:
        invoice = TenantSubscriptionInvoice.objects.get(invoice_number=event.invoice_number)
    except TenantSubscriptionInvoice.DoesNotExist:
        return Response({"detail": "unknown invoice"}, status=status.HTTP_404_NOT_FOUND)

    if event.provider_ref and invoice.provider_ref != event.provider_ref:
        invoice.provider_ref = event.provider_ref
        invoice.save(update_fields=["provider_ref", "updated_at"])

    tenant = activate_paid_subscription(invoice, approved_by=f"gateway:{provider}:verify")
    return Response(
        {"tenant_slug": tenant.slug, "invoice_number": invoice.invoice_number, "status": "active"},
        status=status.HTTP_200_OK,
    )


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def payment_simulate(request):
    """DEBUG-only: complete a fake-provider checkout by posting its own signed
    webhook back to ourselves. Lets the full online-payment loop be exercised
    with no external gateway."""
    from django.conf import settings as _s

    if not _s.DEBUG or active_provider_code() != "fake":
        return Response({"detail": "not available"}, status=status.HTTP_404_NOT_FOUND)
    invoice_number = request.GET.get("invoice") or request.data.get("invoice")
    try:
        invoice = TenantSubscriptionInvoice.objects.get(invoice_number=invoice_number)
    except TenantSubscriptionInvoice.DoesNotExist:
        return Response({"detail": "unknown invoice"}, status=status.HTTP_404_NOT_FOUND)
    prov = get_payment_provider("fake")
    event = prov.parse_webhook(
        body=(
            '{"invoice_number": "%s", "status": "paid", "ref": "fake-%s"}'
            % (invoice_number, invoice.pk)
        ).encode(),
        headers={"X-Fake-Signature": prov.sign(invoice_number)},
    )
    tenant = activate_paid_subscription(invoice, approved_by="gateway:fake")
    return Response(
        {"tenant_slug": tenant.slug, "invoice_number": invoice_number, "status": "active", "paid": event.paid},
        status=status.HTTP_200_OK,
    )


# ---------------------------------------------------------------------------
# Tenant scoping for the sub-resource viewsets
# ---------------------------------------------------------------------------


class TenantScopedReadMixin:
    """Scope tenant sub-resources to the caller's own tenant.

    Security: these are ModelViewSets with ReadOnlyOrPlatformAdmin, so without
    this a normal authenticated user could GET every tenant's rows
    (subscriptions, profiles, configurations, branding, ...). platform_admin
    operates cross-tenant (request.tenant_id is None) and still sees all.
    Defensive: only filters models that actually carry a `tenant` FK, so it is
    safe to apply broadly (non-tenant-scoped lookups pass through unchanged).
    """

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id is None:
            return qs
        if any(getattr(f, "name", None) == "tenant" for f in qs.model._meta.get_fields()):
            return qs.filter(tenant_id=tenant_id)
        return qs


# ---------------------------------------------------------------------------
# TenantViewSet — main CRUD + lifecycle actions
# ---------------------------------------------------------------------------


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all().order_by("name")
    permission_classes = [ReadOnlyOrPlatformAdmin]

    def get_queryset(self):
        # Tenant has no `tenant` FK (it IS the tenant), so scope by its own id:
        # a non-platform-admin sees only their own tenant, never the full list.
        qs = super().get_queryset()
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id is None:
            return qs
        return qs.filter(id=tenant_id)

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

    @action(
        detail=True, methods=["post"], permission_classes=[IsPlatformAdmin], url_path="enable-flavor"
    )
    def enable_flavor(self, request, pk=None):
        """Turn on a vertical flavor (blueprint N) for this tenant — appends
        its registry key to `flavor_set`. 404s if the key isn't registered."""
        tenant = self.get_object()
        ser = TenantFlavorActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            flavors.enable_for_tenant(tenant, ser.validated_data["key"])
        except flavors.FlavorNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(TenantSerializer(tenant).data)

    @action(
        detail=True, methods=["post"], permission_classes=[IsPlatformAdmin], url_path="disable-flavor"
    )
    def disable_flavor(self, request, pk=None):
        """Turn off a vertical flavor for this tenant. Always safe — no
        error if the key was never enabled or isn't registered."""
        tenant = self.get_object()
        ser = TenantFlavorActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        flavors.disable_for_tenant(tenant, ser.validated_data["key"])
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


class TenantProfileViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantProfile.objects.all()
    serializer_class = TenantProfileSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantConfigurationViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantConfiguration.objects.all()
    serializer_class = TenantConfigurationSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantBrandingViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantBranding.objects.all()
    serializer_class = TenantBrandingSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantSubscriptionViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantSubscription.objects.all()
    serializer_class = TenantSubscriptionSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantLicenseViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantLicense.objects.all()
    serializer_class = TenantLicenseSerializer
    permission_classes = [IsPlatformAdmin]


class TenantEnvironmentViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantEnvironment.objects.all()
    serializer_class = TenantEnvironmentSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantRegionViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantRegion.objects.all()
    serializer_class = TenantRegionSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantDeploymentProfileViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantDeploymentProfile.objects.all()
    serializer_class = TenantDeploymentProfileSerializer
    permission_classes = [IsPlatformAdmin]


class TenantFeatureFlagViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
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


class TenantDomainViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantDomain.objects.all()
    serializer_class = TenantDomainSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        domain_obj = self.get_object()
        TenantDomainService().verify_domain(domain_obj)
        return Response(TenantDomainSerializer(domain_obj).data)


class TenantSSOConfigurationViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantSSOConfiguration.objects.all()
    serializer_class = TenantSSOConfigurationSerializer
    permission_classes = [IsPlatformAdmin]


class TenantStoragePolicyViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantStoragePolicy.objects.all()
    serializer_class = TenantStoragePolicySerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantRetentionPolicyViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantRetentionPolicy.objects.all()
    serializer_class = TenantRetentionPolicySerializer
    permission_classes = [IsPlatformAdmin]


class TenantComplianceProfileViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantComplianceProfile.objects.all()
    serializer_class = TenantComplianceProfileSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class TenantAuditConfigurationViewSet(TenantScopedReadMixin, viewsets.ModelViewSet):
    queryset = TenantAuditConfiguration.objects.all()
    serializer_class = TenantAuditConfigurationSerializer
    permission_classes = [IsPlatformAdmin]
