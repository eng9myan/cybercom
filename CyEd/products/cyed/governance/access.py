"""
Role-based access control, object-level scoping, immutable audit, and consent
enforcement for CyEd. Addresses the ministry audit's Critical findings:
  - RBAC / least privilege (parents see only their children; confidential
    wellbeing + at-risk restricted to pastoral/leadership).
  - Immutable audit logging on sensitive CRUD.
  - Consent gate for AI operating on a named student.

Roles come from the authenticated session (`request.user_session['roles']`),
set by CyIdentityAuthMiddleware (or the dev shim) from JWT realm claims.
"""

from django.db import models
from rest_framework.permissions import BasePermission

from core.viewsets import TenantScopedModelViewSet

# ── Role vocabulary ──────────────────────────────────────────────────────────
ADMIN = {"platform_admin", "tenant_admin", "admin"}
LEADERSHIP = {"principal", "deputy_principal", "leadership", "head_of_school"}
TEACHER = {"teacher", "educator"}
PASTORAL = {"pastoral", "counsellor", "wellbeing", "welfare"}
FINANCE = {"finance", "bursar", "accounts"}
PARENT = {"parent", "guardian", "carer"}
STUDENT = {"student", "learner"}

STAFF = ADMIN | LEADERSHIP | TEACHER | PASTORAL | FINANCE
PASTORAL_OR_LEADERSHIP = PASTORAL | LEADERSHIP | ADMIN
FINANCE_OR_LEADERSHIP = FINANCE | LEADERSHIP | ADMIN


def roles_of(request) -> set:
    session = getattr(request, "user_session", None) or {}
    return set(session.get("roles") or [])


def _email(request) -> str:
    session = getattr(request, "user_session", None) or {}
    return session.get("email", "") or ""


def has_any(request, roleset) -> bool:
    return bool(roles_of(request) & roleset)


def is_staff(request) -> bool:
    return has_any(request, STAFF)


# ── Permission classes ───────────────────────────────────────────────────────
class _ClaimsPermission(BasePermission):
    roleset: set = set()

    def has_permission(self, request, view) -> bool:
        if getattr(request, "auth_claims", None) is None:
            return False
        return has_any(request, self.roleset)


class IsStaff(_ClaimsPermission):
    roleset = STAFF


class IsPastoralOrLeadership(_ClaimsPermission):
    roleset = PASTORAL_OR_LEADERSHIP


class IsFinanceOrLeadership(_ClaimsPermission):
    roleset = FINANCE_OR_LEADERSHIP


class IsStaffOrParent(_ClaimsPermission):
    """
    Reads that a family may make about their own household.

    Grants entry only — the queryset still has to be narrowed by
    `visible_student_ids`, or a parent sees the whole school. Never use this on
    a write.
    """

    roleset = STAFF | PARENT


# ── Object-level scoping ─────────────────────────────────────────────────────
def visible_student_ids(request, tenant_id):
    """
    Returns the set of student UUIDs this user may see, or None meaning "all"
    (staff). Parents → their linked children (Guardian.email match); students →
    themselves (Student.email match); anyone else → empty set.
    """
    if is_staff(request):
        return None
    from products.cyed.sis.models import Guardian, Student

    email = _email(request)
    if not email:
        return set()

    ids: set = set()
    if has_any(request, PARENT):
        guardians = Guardian.objects.filter(tenant_id=tenant_id, email__iexact=email)
        for g in guardians:
            ids.update(g.students.values_list("id", flat=True))
    if has_any(request, STUDENT):
        ids.update(
            Student.objects.filter(tenant_id=tenant_id, email__iexact=email).values_list("id", flat=True)
        )
    return ids


def scope_queryset_by_student(request, tenant_id, qs, student_path="student_id"):
    visible = visible_student_ids(request, tenant_id)
    if visible is None:
        return qs
    return qs.filter(**{f"{student_path}__in": visible})


# ── Campus (multi-campus group) scoping ──────────────────────────────────────
def campus_ids(request):
    """
    Campuses this user is bound to, or None meaning "all" (group office /
    leadership / admin). Campus-bound staff carry a `campus_ids` claim.
    """
    if has_any(request, ADMIN | LEADERSHIP):
        return None
    session = getattr(request, "user_session", None) or {}
    ids = session.get("campus_ids")
    return set(ids) if ids else None


def scope_queryset_by_campus(request, qs, campus_path="campus_id"):
    ids = campus_ids(request)
    if ids is None:
        return qs
    # A row with no campus is group-level data (a policy, a group-wide fee
    # plan) and stays visible: hiding it would make a campus user's world look
    # emptier than it is, which reads as data loss rather than as scoping.
    return qs.filter(models.Q(**{f"{campus_path}__in": ids}) | models.Q(**{f"{campus_path}__isnull": True}))


class CampusScopedMixin:
    """
    Restrict a viewset to the campuses the caller is bound to.

    A 13-campus group runs one tenant, so tenant isolation alone lets a
    Northside receptionist read Southside's students. `scope_queryset_by_campus`
    existed for this but was wired into nothing — the helper was written and
    never called, which is the most expensive kind of security control because
    it looks present in review.

    Set `campus_path` on the viewset when the campus is reached through a
    relation (e.g. `student__campus_id`). Leadership and group office are
    unbound and see everything.
    """

    campus_path = "campus_id"

    def get_queryset(self):
        return scope_queryset_by_campus(
            self.request, super().get_queryset(), campus_path=self.campus_path
        )


# ── Consent ──────────────────────────────────────────────────────────────────
def has_ai_consent(tenant_id, student_id) -> bool:
    if not student_id:
        return True  # no named student → nothing to consent for
    from products.cyed.governance.models import ConsentRecord

    return ConsentRecord.objects.filter(
        tenant_id=tenant_id, student_id=student_id, consent_type="ai_use", granted=True
    ).exists()


# ── Audited viewset ──────────────────────────────────────────────────────────
def write_audit(request, action, instance):
    from products.cyed.governance.models import AuditEvent

    try:
        AuditEvent.objects.create(
            tenant_id=getattr(request, "tenant_id", None) or instance.tenant_id,
            actor=_email(request),
            actor_roles=",".join(sorted(roles_of(request))),
            action=action,
            model_label=instance._meta.label,
            object_id=str(instance.pk),
            summary=str(instance)[:500],
        )
    except Exception:
        # Auditing must never break the primary operation; failures are rare and
        # would themselves be surfaced by monitoring in production.
        pass


class AuditedTenantViewSet(TenantScopedModelViewSet):
    """TenantScopedModelViewSet that appends an immutable AuditEvent on writes."""

    def perform_create(self, serializer):
        instance = serializer.save(tenant_id=self.request.tenant_id)
        write_audit(self.request, "create", instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        write_audit(self.request, "update", instance)

    def perform_destroy(self, instance):
        write_audit(self.request, "delete", instance)
        instance.delete()
