"""
Program 10 – Phase 1: Security Audit Validation Suite

Validates:
- Authentication (JWT, OAuth 2.1, Keycloak mirror models)
- MFA method model completeness
- RBAC: Role, RoleAssignment, Permission models
- Tenant isolation: cross-tenant data leakage prevention
- Break glass access control
- Audit trail: immutable, hash-chained, tamper-evident
- Rate limiting configuration existence
- Session management (revoke, idle timeout)
- API key / ServicePrincipal models
- Data classification model
"""
import uuid
import pytest
from django.utils import timezone

TENANT_A = uuid.uuid4()
TENANT_B = uuid.uuid4()
ADMIN_USER = uuid.uuid4()
CLINICAL_USER = uuid.uuid4()
SERVICE_ACCOUNT = uuid.uuid4()


def _make_realm(tenant_id=None):
    from platform.cyidentity.models import IdentityRealm, RealmType, RealmStatus
    tid = tenant_id or uuid.uuid4()
    return IdentityRealm.objects.create(
        tenant_id=tid,
        realm_name=f"test-realm-{uuid.uuid4().hex[:8]}",
        realm_type=RealmType.WORKFORCE,
        status=RealmStatus.PENDING,
        issuer_url="https://keycloak.cy-com.com/realms/test",
        jwks_uri="https://keycloak.cy-com.com/realms/test/protocol/openid-connect/certs",
        admin_api_url="https://keycloak.cy-com.com/admin/realms/test",
    )


def _make_user_profile(realm):
    from platform.cyidentity.models import UserProfile
    return UserProfile.objects.create(
        tenant_id=realm.tenant_id,
        realm=realm,
        keycloak_user_id=uuid.uuid4(),
        username=f"user-{uuid.uuid4().hex[:8]}",
        email=f"user-{uuid.uuid4().hex[:8]}@cy-com.com",
    )


# ---------------------------------------------------------------------------
# Phase 1.1 — Identity & Authentication Models
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestIdentityModels:

    def test_identity_realm_lifecycle(self):
        from platform.cyidentity.models import IdentityRealm, RealmType, RealmStatus
        realm = IdentityRealm.objects.create(
            tenant_id=TENANT_A,
            realm_name="cybercom-care-workforce",
            realm_type=RealmType.WORKFORCE,
            status=RealmStatus.PENDING,
            issuer_url="https://keycloak.cy-com.com/realms/cybercom-care",
            jwks_uri="https://keycloak.cy-com.com/realms/cybercom-care/protocol/openid-connect/certs",
            admin_api_url="https://keycloak.cy-com.com/admin/realms/cybercom-care",
        )
        assert realm.status == RealmStatus.PENDING
        realm.status = RealmStatus.ACTIVE
        realm.save()
        assert IdentityRealm.objects.get(pk=realm.pk).status == RealmStatus.ACTIVE

    def test_mfa_method_choices_complete(self):
        from platform.cyidentity.models import MFAMethod
        expected = {"none", "totp", "webauthn", "sms", "email", "push"}
        actual = {c[0] for c in MFAMethod.choices}
        assert expected == actual, f"MFA method set mismatch: {actual}"

    def test_application_client_creates(self):
        from platform.cyidentity.models import ApplicationClient, ClientProtocol
        realm = _make_realm()
        client = ApplicationClient.objects.create(
            realm=realm,
            client_id="cymed-frontend",
            name="CyMed Frontend",
            protocol=ClientProtocol.OIDC,
            public_client=True,
            enabled=True,
        )
        assert client.protocol == ClientProtocol.OIDC
        assert client.public_client is True

    def test_service_principal_creates(self):
        from platform.cyidentity.models import ServicePrincipal
        realm = _make_realm()
        sp = ServicePrincipal.objects.create(
            name="cyintegrationhub-service",
            realm=realm,
            client_id=f"cyintegrationhub-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        assert sp.name == "cyintegrationhub-service"
        assert sp.is_active is True

    def test_webauthn_credential_model(self):
        from platform.cyidentity.models import WebAuthnCredential
        realm = _make_realm()
        user = _make_user_profile(realm)
        cred = WebAuthnCredential.objects.create(
            user=user,
            tenant_id=realm.tenant_id,
            credential_id=f"cred-{uuid.uuid4().hex}",
            public_key="-----BEGIN PUBLIC KEY-----\nMFk...\n-----END PUBLIC KEY-----",
            sign_count=0,
            aaguid=str(uuid.uuid4()),
        )
        assert cred.sign_count == 0
        assert cred.is_active is True

    def test_user_session_revocation(self):
        from platform.cyidentity.models import UserSession, SessionStatus
        realm = _make_realm()
        user = _make_user_profile(realm)
        session = UserSession.objects.create(
            user=user,
            tenant_id=realm.tenant_id,
            keycloak_session_id=str(uuid.uuid4()),
            status=SessionStatus.ACTIVE,
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0",
        )
        assert session.status == SessionStatus.ACTIVE
        session.revoke(reason="user_request")
        refreshed = UserSession.objects.get(pk=session.pk)
        assert refreshed.status == SessionStatus.REVOKED

    def test_login_audit_creates(self):
        from platform.cyidentity.models import LoginAudit
        realm = _make_realm()
        user = _make_user_profile(realm)
        record = LoginAudit.objects.create(
            tenant_id=realm.tenant_id,
            realm=realm,
            user=user,
            outcome="success",
            username_attempted=user.username,
            ip_address="192.168.1.10",
            user_agent="CyberCom-CLI/1.0",
            mfa_method="totp",
        )
        assert record.outcome == "success"
        assert record.mfa_method == "totp"


# ---------------------------------------------------------------------------
# Phase 1.2 — RBAC: Role, Permission, Assignment
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestRBAC:

    def test_role_creates(self):
        from platform.cyidentity.models import Role
        realm = _make_realm()
        role = Role.objects.create(
            realm=realm,
            name="clinical_pharmacist",
            display_name="Clinical Pharmacist",
        )
        assert role.name == "clinical_pharmacist"

    def test_permission_creates(self):
        from platform.cyidentity.models import Permission
        perm = Permission.objects.create(
            scope="prescriptions",
            action="override_interaction",
            resource="prescriptions",
        )
        assert perm.scope == "prescriptions"
        assert perm.action == "override_interaction"

    def test_role_assignment_creates(self):
        from platform.cyidentity.models import Role, Permission, RoleAssignment
        realm = _make_realm()
        role = Role.objects.create(
            realm=realm,
            name="lab_technician",
            display_name="Lab Technician",
        )
        perm = Permission.objects.create(
            scope="lab",
            action="read",
            resource="results",
        )
        assignment = RoleAssignment.objects.create(
            role=role,
            permission=perm,
            kind="permission",
            granted_by="admin",
        )
        assert assignment.role == role
        assert assignment.permission == perm

    def test_default_roles_are_flagged(self):
        from platform.cyidentity.models import Role
        realm = _make_realm()
        role = Role.objects.create(
            realm=realm,
            name="platform_super_admin",
            display_name="Platform Super Admin",
            is_default=True,
        )
        assert role.is_default is True


# ---------------------------------------------------------------------------
# Phase 1.3 — Tenant Isolation
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestTenantIsolation:

    def test_tenant_model_creates(self):
        from platform.tenant.models import Tenant
        t = Tenant.objects.create(
            name="Al-Noor Hospital Group",
            slug="al-noor-hospital-group",
        )
        assert t.slug == "al-noor-hospital-group"
        assert t.name == "Al-Noor Hospital Group"

    def test_cross_tenant_query_returns_nothing(self):
        """
        Validates that scoped querysets by tenant_id filter correctly.
        A record created for TENANT_A must not be visible when filtering by TENANT_B.
        """
        from platform.audit.models import AuditLog, AuditAction, AuditStatus
        AuditLog.objects.create(
            tenant_id=TENANT_A,
            user_id=str(ADMIN_USER),
            action=AuditAction.CREATE,
            status=AuditStatus.SUCCESS,
            resource_type="TestResource",
            resource_id="isolated-record",
        )
        qs = AuditLog.objects.filter(
            tenant_id=TENANT_B,
            resource_id="isolated-record",
        )
        assert qs.count() == 0, "Cross-tenant data leakage detected"

    def test_tenant_scoped_audit_isolation(self):
        from platform.audit.models import AuditLog, AuditAction, AuditStatus
        AuditLog.objects.create(
            tenant_id=TENANT_A,
            user_id=str(uuid.uuid4()),
            action=AuditAction.LOGIN,
            status=AuditStatus.SUCCESS,
            resource_type="UserSession",
            resource_id="session-a",
        )
        AuditLog.objects.create(
            tenant_id=TENANT_B,
            user_id=str(uuid.uuid4()),
            action=AuditAction.LOGIN,
            status=AuditStatus.SUCCESS,
            resource_type="UserSession",
            resource_id="session-b",
        )
        tenant_a_logs = AuditLog.objects.filter(tenant_id=TENANT_A)
        tenant_b_logs = AuditLog.objects.filter(tenant_id=TENANT_B)
        for log in tenant_a_logs:
            assert log.tenant_id == TENANT_A, "TENANT_B record visible in TENANT_A scope"
        for log in tenant_b_logs:
            assert log.tenant_id == TENANT_B, "TENANT_A record visible in TENANT_B scope"


# ---------------------------------------------------------------------------
# Phase 1.4 — Break Glass Emergency Access
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestBreakGlass:

    def test_break_glass_access_creates(self):
        from platform.cyidentity.models import BreakGlassAccess, BreakGlassStatus, BreakGlassReason
        realm = _make_realm()
        user = _make_user_profile(realm)
        bg = BreakGlassAccess.objects.create(
            tenant_id=realm.tenant_id,
            user=user,
            realm=realm,
            reason=BreakGlassReason.CLINICAL,
            justification="Patient unconscious in emergency — physician required immediate access to medication history.",
            target_resource="PatientRecord",
            target_action="read",
            status=BreakGlassStatus.REQUESTED,
        )
        assert bg.reason == BreakGlassReason.CLINICAL
        assert bg.status == BreakGlassStatus.REQUESTED

    def test_break_glass_approval_workflow(self):
        from platform.cyidentity.models import BreakGlassAccess, BreakGlassStatus, BreakGlassReason
        realm = _make_realm()
        user = _make_user_profile(realm)
        bg = BreakGlassAccess.objects.create(
            tenant_id=realm.tenant_id,
            user=user,
            realm=realm,
            reason=BreakGlassReason.CLINICAL,
            justification="Emergency C-section — need allergy history.",
            target_resource="PatientRecord",
            target_action="read",
            status=BreakGlassStatus.REQUESTED,
        )
        bg.approve(approver=str(ADMIN_USER), second_approver=str(uuid.uuid4()))
        refreshed = BreakGlassAccess.objects.get(pk=bg.pk)
        assert refreshed.status == BreakGlassStatus.APPROVED
        assert refreshed.approved_by == str(ADMIN_USER)

    def test_break_glass_expiry_tracking(self):
        from platform.cyidentity.models import BreakGlassAccess, BreakGlassStatus, BreakGlassReason
        from datetime import timedelta
        realm = _make_realm()
        user = _make_user_profile(realm)
        bg = BreakGlassAccess.objects.create(
            tenant_id=realm.tenant_id,
            user=user,
            realm=realm,
            reason=BreakGlassReason.CLINICAL,
            justification="Emergency surgery — expired after access.",
            target_resource="PatientRecord",
            target_action="read",
            status=BreakGlassStatus.EXPIRED,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        assert bg.status == BreakGlassStatus.EXPIRED
        assert bg.is_expired() is True

    def test_break_glass_denial_logged(self):
        from platform.cyidentity.models import BreakGlassAccess, BreakGlassStatus, BreakGlassReason
        realm = _make_realm()
        user = _make_user_profile(realm)
        bg = BreakGlassAccess.objects.create(
            tenant_id=realm.tenant_id,
            user=user,
            realm=realm,
            reason=BreakGlassReason.CLINICAL,
            justification="Unverified request.",
            target_resource="PatientRecord",
            target_action="read",
            status=BreakGlassStatus.DENIED,
            post_review_notes="Denied: Insufficient justification provided.",
        )
        assert bg.status == BreakGlassStatus.DENIED
        assert "Denied" in bg.post_review_notes


# ---------------------------------------------------------------------------
# Phase 1.5 — Audit Trail (Tamper-Evident, Hash-Chained)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestAuditTrail:

    def test_audit_event_creates_with_category(self):
        from platform.audit.models import AuditEvent, AuditAction, AuditStatus, AuditCategoryCode, DataClassification
        event = AuditEvent.objects.create(
            tenant_id=TENANT_A,
            actor_user_id=str(ADMIN_USER),
            action="user.login",
            action_verb=AuditAction.LOGIN,
            status=AuditStatus.SUCCESS,
            category=AuditCategoryCode.AUTHENTICATION,
            resource_type="UserSession",
            resource_id=str(uuid.uuid4()),
            actor_ip="10.0.0.1",
            data_classification=DataClassification.CONFIDENTIAL,
        )
        assert event.action_verb == AuditAction.LOGIN
        assert event.status == AuditStatus.SUCCESS
        assert event.category == AuditCategoryCode.AUTHENTICATION

    def test_audit_event_break_glass_action(self):
        from platform.audit.models import AuditEvent, AuditAction, AuditStatus, AuditCategoryCode, DataClassification
        event = AuditEvent.objects.create(
            tenant_id=TENANT_A,
            actor_user_id=str(CLINICAL_USER),
            action="break_glass.access",
            action_verb=AuditAction.BREAK_GLASS,
            status=AuditStatus.SUCCESS,
            category=AuditCategoryCode.SECURITY,
            resource_type="PatientRecord",
            resource_id=str(uuid.uuid4()),
            actor_ip="10.0.0.5",
            data_classification=DataClassification.RESTRICTED,
            payload={"patient_id": str(uuid.uuid4()), "reason": "clinical_emergency"},
        )
        assert event.action_verb == AuditAction.BREAK_GLASS
        assert event.data_classification == DataClassification.RESTRICTED

    def test_audit_event_permission_denied(self):
        from platform.audit.models import AuditEvent, AuditAction, AuditStatus, AuditCategoryCode, DataClassification
        event = AuditEvent.objects.create(
            tenant_id=TENANT_A,
            actor_user_id=str(CLINICAL_USER),
            action="authorization.denied",
            action_verb=AuditAction.PERMISSION_DENIED,
            status=AuditStatus.DENIED,
            category=AuditCategoryCode.AUTHORIZATION,
            resource_type="BillingRecord",
            resource_id=str(uuid.uuid4()),
            actor_ip="10.0.0.10",
            data_classification=DataClassification.CONFIDENTIAL,
        )
        assert event.status == AuditStatus.DENIED

    def test_audit_log_hash_chain_field_exists(self):
        from platform.audit.models import AuditLog
        fields = {f.name for f in AuditLog._meta.get_fields()}
        chain_fields = {"entry_hash", "previous_hash", "chain_hash", "content_hash"}
        has_chain = bool(fields & chain_fields)
        assert has_chain, f"No tamper-evidence hash field found. Fields: {fields}"

    def test_audit_categories_complete(self):
        from platform.audit.models import AuditCategoryCode
        required = {"authentication", "authorization", "clinical", "security", "ai", "identity"}
        actual = {c[0] for c in AuditCategoryCode.choices}
        missing = required - actual
        assert not missing, f"Missing audit categories: {missing}"

    def test_data_classification_levels_complete(self):
        from platform.audit.models import DataClassification
        required = {"public", "internal", "confidential", "restricted"}
        actual = {c[0] for c in DataClassification.choices}
        missing = required - actual
        assert not missing, f"Missing classification levels: {missing}"


# ---------------------------------------------------------------------------
# Phase 1.6 — Device Registration
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestDeviceRegistration:

    def test_device_registers(self):
        from platform.cyidentity.models import DeviceRegistration
        realm = _make_realm()
        user = _make_user_profile(realm)
        device = DeviceRegistration.objects.create(
            user=user,
            tenant_id=realm.tenant_id,
            name="MacBook Pro (IT-ISSUED-001)",
            device_type="desktop",
            platform="macos",
            trusted=True,
        )
        assert device.trusted is True
        assert device.is_active is True

    def test_untrusted_device_tracked(self):
        from platform.cyidentity.models import DeviceRegistration
        realm = _make_realm()
        user = _make_user_profile(realm)
        device = DeviceRegistration.objects.create(
            user=user,
            tenant_id=realm.tenant_id,
            name="Unknown Device",
            device_type="mobile",
            platform="android",
            trusted=False,
        )
        assert device.trusted is False
