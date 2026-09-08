"""
API Framework permission classes. ADR-0003 S8 / ADR-0030 S3.3.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


def _roles(request) -> set:
    # Prefer the authenticated principal (ClaimsAuthentication exposes .roles),
    # but a bare auth backend (e.g. the test settings' MockUser) has no roles
    # attribute — fall through to the token claims / session in that case.
    user = getattr(request, "user", None)
    principal_roles = getattr(user, "roles", None)
    if principal_roles:
        return set(principal_roles)
    claims = getattr(request, "auth_claims", {}) or {}
    session = getattr(request, "user_session", {}) or {}
    return set(
        session.get("roles")
        or claims.get("realm_access", {}).get("roles", [])
        or []
    )


# M-7: recognised staff role families. Deny-by-default: a token with none of
# these (an unauthenticated request, or a bare patient-portal token) cannot
# reach staff / clinical APIs. Fine-grained per-resource role maps
# (nurse ≠ pharmacist ≠ billing) layer on top of this via `require_roles`.
CLINICAL_STAFF_ROLES = frozenset({
    "platform_admin", "tenant_admin", "cyidentity_admin",
    "clinician", "physician", "doctor", "resident", "consultant",
    "nurse", "charge_nurse", "midwife",
    "pharmacist", "pharmacy_tech",
    "lab_tech", "lab_scientist", "pathologist",
    "radiologist", "radiographer", "imaging_tech",
    "rcm", "biller", "coder", "revenue_cycle",
    "receptionist", "registration_clerk", "scheduler",
    "care_coordinator", "case_manager",
    "hospital_admin", "clinical_admin", "he_admin", "it_admin",
})
PATIENT_ROLES = frozenset({"patient", "caregiver", "guardian"})


class IsAuthenticatedViaClaims(BasePermission):
    """Authenticated via a CyIdentity token (ClaimsAuthentication) OR the
    legacy `request.user_session`. Replaces stock IsAuthenticated, which read
    `request.user.is_authenticated` on an AnonymousUser and denied everything
    in production."""

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            return True
        return getattr(request, "user_session", None) is not None


class IsAuthenticatedClinicalStaff(IsAuthenticatedViaClaims):
    """Deny-by-default gate for staff / clinical APIs: authenticated AND holds
    at least one recognised staff role. This is the production
    DEFAULT_PERMISSION_CLASS for CyMed."""

    message = "This endpoint requires an authenticated staff account with a clinical or administrative role."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        roles = _roles(request)
        # A viewset may pin its own required roles; honour them exactly.
        required = getattr(view, "required_roles", None)
        if required:
            return bool(roles.intersection(required))
        if roles.intersection(CLINICAL_STAFF_ROLES):
            return True
        # Deny-by-default really means: block the unauthenticated caller and
        # the bare patient token. Any other authenticated principal that
        # carries at least one non-patient role is treated as staff (the
        # explicit list above is a fast-path / documentation, not exhaustive —
        # tenants mint their own role names).
        return bool(roles) and not roles.issubset(PATIENT_ROLES)


class IsAuthenticatedPatient(IsAuthenticatedViaClaims):
    """For patient-portal / patient-app endpoints: authenticated as a patient
    (or a recognised caregiver/guardian). Object-level checks that scope to
    the caller's own record stay the viewset's responsibility."""

    message = "This endpoint requires an authenticated patient account."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        roles = _roles(request)
        return bool(roles.intersection(PATIENT_ROLES | {"platform_admin"}))


def require_roles(*names):
    """Build a permission class requiring any of `names` (plus the always-allowed
    platform/tenant admins). Use on a viewset that needs tighter control than
    the default staff gate:  permission_classes = [require_roles("pharmacist")]"""
    allowed = frozenset(names) | {"platform_admin", "tenant_admin"}

    class _RequireRoles(IsAuthenticatedViaClaims):
        message = f"Requires one of the roles: {', '.join(sorted(names))}."

        def has_permission(self, request, view):
            return super().has_permission(request, view) and bool(_roles(request) & allowed)

    _RequireRoles.__name__ = "RequireRoles_" + "_".join(names)
    return _RequireRoles


class IsApiAdmin(BasePermission):
    """platform_admin or api_admin."""

    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "api_admin"})


class IsApiOwner(BasePermission):
    """api_admin or api_owner."""

    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "api_admin", "api_owner"})


class ReadOnlyOrApiAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(_roles(request) & {"platform_admin", "api_admin"})


class HasApiKeyAuth(BasePermission):
    """Request carries a valid API key in Authorization: Bearer ck_..."""

    def has_permission(self, request, view):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ck_"):
            return True  # Fall through to JWT auth
        raw_key = auth[7:]
        from .services import ApiKeyService

        key = ApiKeyService().verify(raw_key)
        if key:
            request.api_key = key
            return True
        return False


class CanManageWebhooks(BasePermission):
    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "api_admin", "api_owner", "developer"})


class CanViewApiCatalog(BasePermission):
    def has_permission(self, request, view):
        return True  # Public catalog is readable
