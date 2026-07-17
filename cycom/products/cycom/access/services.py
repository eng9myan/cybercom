from django.db.models import Q
from rest_framework.exceptions import ValidationError

from products.cycom.access.models import AccessGrant, RoleAssignment

ADMIN_ROLES = {"platform_admin", "cyidentity_admin", "tenant_admin"}


def is_platform_admin(request):
    claims = getattr(request, "auth_claims", {}) or {}
    roles = set(claims.get("realm_access", {}).get("roles", []))
    return bool(roles & ADMIN_ROLES)


def current_user_id(request):
    claims = getattr(request, "auth_claims", {}) or {}
    return claims.get("sub")


def create_grant(tenant_id, subject_type, user_id="", role_id=None, warehouse_id=None, product_id=None):
    if subject_type == "user":
        if not user_id:
            raise ValidationError("user_id is required when subject_type is 'user'.")
        role_id = None
    elif subject_type == "role":
        if not role_id:
            raise ValidationError("role is required when subject_type is 'role'.")
        user_id = ""
    else:
        raise ValidationError("subject_type must be 'user' or 'role'.")

    if not warehouse_id and not product_id:
        raise ValidationError("Grant must specify a warehouse and/or a product.")

    return AccessGrant.objects.create(
        tenant_id=tenant_id,
        subject_type=subject_type,
        user_id=user_id,
        role_id=role_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )


def _user_grants(tenant_id, user_id):
    role_ids = list(
        RoleAssignment.objects.filter(tenant_id=tenant_id, user_id=user_id).values_list(
            "role_id", flat=True
        )
    )
    return AccessGrant.objects.filter(tenant_id=tenant_id).filter(
        Q(subject_type="user", user_id=user_id) | Q(subject_type="role", role_id__in=role_ids)
    )


def accessible_warehouse_ids(tenant_id, user_id):
    """None means unrestricted (no warehouse-scoped grant exists for this user)."""
    ids = set(
        _user_grants(tenant_id, user_id).exclude(warehouse_id=None).values_list("warehouse_id", flat=True)
    )
    return ids or None


def accessible_product_ids(tenant_id, user_id):
    """None means unrestricted (no product-scoped grant exists for this user)."""
    ids = set(
        _user_grants(tenant_id, user_id).exclude(product_id=None).values_list("product_id", flat=True)
    )
    return ids or None


def restrict_to_accessible_warehouses(queryset, request, field="id"):
    if is_platform_admin(request):
        return queryset
    tenant_id = getattr(request, "tenant_id", None)
    user_id = current_user_id(request)
    if tenant_id is None or not user_id:
        return queryset
    ids = accessible_warehouse_ids(tenant_id, user_id)
    if ids is None:
        return queryset
    return queryset.filter(**{f"{field}__in": ids})


def restrict_to_accessible_products(queryset, request, field="id"):
    if is_platform_admin(request):
        return queryset
    tenant_id = getattr(request, "tenant_id", None)
    user_id = current_user_id(request)
    if tenant_id is None or not user_id:
        return queryset
    ids = accessible_product_ids(tenant_id, user_id)
    if ids is None:
        return queryset
    return queryset.filter(**{f"{field}__in": ids})
