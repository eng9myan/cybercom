from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.tenants.models import BaseEntity, generate_uuid7, Branch

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_created'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_updated'
    )
    is_deleted = models.BooleanField(default=False)
    version = models.IntegerField(default=1)

    mfa_secret = models.CharField(max_length=100, null=True, blank=True)
    is_mfa_enabled = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.pk:
            self.version += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class Permission(BaseEntity):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class PermissionGroup(BaseEntity):
    name = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission, related_name='groups')

    def __str__(self):
        return self.name

class Role(BaseEntity):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')
    permission_groups = models.ManyToManyField(PermissionGroup, blank=True, related_name='roles')

    def __str__(self):
        return self.name

class RoleAssignment(BaseEntity):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='assignments')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True, related_name='role_assignments')

    class Meta:
        unique_together = ('tenant_id', 'user', 'role', 'branch')

    def __str__(self):
        return f"{self.user.username} - {self.role.code} ({self.branch.name if self.branch else 'All Branches'})"

class UserProfile(BaseEntity):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=50, null=True, blank=True)
    avatar_url = models.URLField(max_length=500, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

class UserSession(BaseEntity):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Session for {self.user.username}"

class UserDevice(BaseEntity):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=50, default='WEB') # WEB, MOBILE, DESKTOP
    os_name = models.CharField(max_length=100, null=True, blank=True)
    push_token = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.device_name} ({self.user.username})"
