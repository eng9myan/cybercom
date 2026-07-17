from django.db import models

from platform.common.models import BaseModel
from products.cycom.inventory.models import Product, Warehouse


class Role(BaseModel):
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cycom_access_roles"
        unique_together = [("tenant_id", "name")]
        ordering = ["name"]

    def __str__(self):
        return self.name


class RoleAssignment(BaseModel):
    """Links a real user (by JWT `sub`) to a Role, within a tenant."""

    user_id = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="assignments")

    class Meta:
        db_table = "cycom_access_role_assignments"
        unique_together = [("tenant_id", "user_id", "role")]
        ordering = ["user_id"]

    def __str__(self):
        return f"{self.user_id} -> {self.role}"


class AccessGrant(BaseModel):
    """
    A single scoped access grant: either directly to a user or to a role
    (whose assignees inherit it), restricting to a warehouse and/or product.

    Enforcement is additive and per-dimension (see access/services.py):
    a user with zero warehouse-scoped grants sees every warehouse; a user
    with one or more sees only those. Same independently for products.
    A grant naming both warehouse and product widens both dimensions'
    allowed sets — it does not pair them into "only that product in that
    warehouse." Simpler to reason about and to enforce; good enough for a
    first version.
    """

    SUBJECT_TYPE_CHOICES = [("user", "User"), ("role", "Role")]

    subject_type = models.CharField(max_length=10, choices=SUBJECT_TYPE_CHOICES)
    user_id = models.CharField(max_length=255, blank=True)
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, null=True, blank=True, related_name="grants"
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, null=True, blank=True, related_name="access_grants"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, blank=True, related_name="access_grants"
    )

    class Meta:
        db_table = "cycom_access_grants"
        ordering = ["-created_at"]

    def __str__(self):
        subject = self.user_id if self.subject_type == "user" else str(self.role)
        scope = " & ".join(filter(None, [str(self.warehouse or ""), str(self.product or "")]))
        return f"{subject}: {scope}"
