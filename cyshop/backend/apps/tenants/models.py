from django.db import models
from django.conf import settings
import uuid
import time
import os

def generate_uuid7():
    try:
        import uuid6
        return uuid6.uuid7()
    except ImportError:
        ms = int(time.time() * 1000)
        byte_array = bytearray(16)
        byte_array[0:6] = ms.to_bytes(6, byteorder='big')
        seq_val = int.from_bytes(os.urandom(2), byteorder='big') & 0x0FFF
        byte_array[6:8] = (0x7000 | seq_val).to_bytes(2, byteorder='big')
        rand_val = int.from_bytes(os.urandom(8), byteorder='big') & 0x3FFFFFFFFFFFFFFF
        byte_array[8:16] = (0x8000000000000000 | rand_val).to_bytes(8, byteorder='big')
        return uuid.UUID(bytes=bytes(byte_array))

class BaseEntity(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    version = models.IntegerField(default=1)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk:
            self.version += 1
        super().save(*args, **kwargs)

class Tenant(BaseEntity):
    name = models.CharField(max_length=255)
    subdomain = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class TenantSettings(BaseEntity):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='settings')
    logo_url = models.URLField(max_length=500, null=True, blank=True)
    theme_mode = models.CharField(max_length=20, default='DARK') # LIGHT, DARK, SYSTEM
    primary_color = models.CharField(max_length=7, default='#ED6C00')
    currency = models.CharField(max_length=3, default='JOD')
    timezone = models.CharField(max_length=100, default='Asia/Amman')
    language = models.CharField(max_length=10, default='ar') # ar, en
    subscription_tier = models.CharField(max_length=50, default='STARTER') # STARTER, GROWTH, BUSINESS, ENTERPRISE
    subscription_status = models.CharField(max_length=50, default='ACTIVE') # ACTIVE, SUSPENDED, TRIAL
    onboarding_completed = models.BooleanField(default=False)
    onboarding_step = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"Settings for {self.tenant.name}"

class Company(BaseEntity):
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, null=True, blank=True)
    tax_number = models.CharField(max_length=100, null=True, blank=True)
    country_code = models.CharField(max_length=2, default='JO') # JO, SA, AE

    def __str__(self):
        return self.name

class Branch(BaseEntity):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    address = models.TextField()
    timezone = models.CharField(max_length=100, default='Asia/Amman')

    def __str__(self):
        return self.name

class Department(BaseEntity):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class WarehousePlaceholder(BaseEntity):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouses')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class CostCenterPlaceholder(BaseEntity):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cost_centers')
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.name}"
