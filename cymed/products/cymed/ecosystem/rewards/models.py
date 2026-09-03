"""Data models for ecosystem-wide loyalty program spanning clinics, pharmacies, labs, and imaging."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class EcosystemProgram(BaseModel):
    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    currency_conversion = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("1"))
    redeem_ratio = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("100"))
    partner_tenant_ids = models.JSONField(default=list)
    cross_country_convertible = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_eco_rewards_ecosystem_program"

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class EcosystemAccount(BaseModel):
    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    program = models.ForeignKey(EcosystemProgram, on_delete=models.CASCADE, related_name="accounts")
    patient_profile_id = models.UUIDField(db_index=True)
    primary_country = models.CharField(max_length=2, blank=True)
    balance_points = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)
    current_tier = models.CharField(max_length=64, blank=True)
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_eco_rewards_ecosystem_account"
        unique_together = [("program", "patient_profile_id")]

    def __str__(self) -> str:
        return f"Account {self.patient_profile_id} @ {self.program_id}"


class EcosystemTier(BaseModel):
    program = models.ForeignKey(EcosystemProgram, on_delete=models.CASCADE, related_name="tiers")
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    name_ar = models.CharField(max_length=128, blank=True)
    threshold_points = models.IntegerField()
    benefits = models.JSONField(default=dict)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = "cymed_eco_rewards_ecosystem_tier"

    def __str__(self) -> str:
        return f"{self.code} ({self.threshold_points})"


class EcosystemPointsEvent(BaseModel):
    class Kind(models.TextChoices):
        EARN = "earn", "Earn"
        REDEEM = "redeem", "Redeem"
        TRANSFER_OUT = "transfer_out", "Transfer Out"
        TRANSFER_IN = "transfer_in", "Transfer In"
        EXPIRE = "expire", "Expire"
        ADJUST = "adjust", "Adjust"

    account = models.ForeignKey(EcosystemAccount, on_delete=models.CASCADE, related_name="events")
    at = models.DateTimeField(default=timezone.now)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    points = models.IntegerField()
    source_tenant_id = models.UUIDField(null=True, blank=True)
    reference_kind = models.CharField(max_length=32, blank=True)
    reference_id = models.UUIDField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_eco_rewards_ecosystem_points_event"

    def __str__(self) -> str:
        return f"{self.kind} {self.points} @ {self.at:%Y-%m-%d}"


class EcosystemReward(BaseModel):
    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    program = models.ForeignKey(EcosystemProgram, on_delete=models.CASCADE, related_name="rewards")
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    cost_points = models.IntegerField()
    monetary_value = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    currency = models.CharField(max_length=3, default="SAR")
    redeemable_at_tenant_ids = models.JSONField(default=list)
    redeemable_at_kinds = models.JSONField(default=list)
    active = models.BooleanField(default=True)
    stock_left = models.IntegerField(default=-1)

    class Meta:
        db_table = "cymed_eco_rewards_ecosystem_reward"

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class EcosystemRedemption(BaseModel):
    class Status(models.TextChoices):
        ISSUED = "issued", "Issued"
        USED = "used", "Used"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    account = models.ForeignKey(EcosystemAccount, on_delete=models.CASCADE, related_name="redemptions")
    reward = models.ForeignKey(EcosystemReward, on_delete=models.PROTECT, related_name="redemptions")
    at = models.DateTimeField(default=timezone.now)
    points_spent = models.IntegerField()
    code = models.CharField(max_length=64)
    redeemed_at_tenant_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ISSUED)

    class Meta:
        db_table = "cymed_eco_rewards_ecosystem_redemption"

    def __str__(self) -> str:
        return f"Redemption {self.code} ({self.status})"
