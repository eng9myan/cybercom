"""Data models for CyMed Pharmacy Loyalty & Rewards."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class LoyaltyProgram(BaseModel):
    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    earn_ratio = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("1"))
    redeem_ratio = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("100"))
    min_redemption_points = models.IntegerField(default=100)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_pharmacy_loyalty_loyalty_program"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class LoyaltyTier(BaseModel):
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name="tiers")
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    name_ar = models.CharField(max_length=128, blank=True)
    threshold_points = models.IntegerField()
    benefits = models.JSONField(default=dict, blank=True)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = "cymed_pharmacy_loyalty_loyalty_tier"

    def __str__(self) -> str:
        return f"{self.code} ({self.threshold_points}pt)"


class PatientLoyaltyAccount(BaseModel):
    tenant_id = models.UUIDField(db_index=True)
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name="accounts")
    patient_profile_id = models.UUIDField(db_index=True)
    balance_points = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)
    current_tier = models.ForeignKey(
        LoyaltyTier,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_pharmacy_loyalty_patient_loyalty_account"
        unique_together = [("program", "patient_profile_id")]

    def __str__(self) -> str:
        return f"Account {self.patient_profile_id} @ {self.program_id}"


class PointsTransaction(BaseModel):
    class Kind(models.TextChoices):
        EARN = "earn", "Earn"
        REDEEM = "redeem", "Redeem"
        ADJUST_UP = "adjust_up", "Adjust Up"
        ADJUST_DOWN = "adjust_down", "Adjust Down"
        EXPIRE = "expire", "Expire"

    account = models.ForeignKey(
        PatientLoyaltyAccount,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    at = models.DateTimeField(default=timezone.now)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    points = models.IntegerField()
    reason = models.CharField(max_length=255, blank=True)
    reference_order_id = models.UUIDField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_loyalty_points_transaction"

    def __str__(self) -> str:
        return f"{self.kind} {self.points} pts"


class Reward(BaseModel):
    class Kind(models.TextChoices):
        DISCOUNT = "discount", "Discount"
        FREE_ITEM = "free_item", "Free Item"
        COUPON = "coupon", "Coupon"
        DONATION = "donation", "Donation"

    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name="rewards")
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    cost_points = models.IntegerField()
    monetary_value = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    kind = models.CharField(max_length=32, choices=Kind.choices)
    active = models.BooleanField(default=True)
    stock_left = models.IntegerField(default=-1)

    class Meta:
        db_table = "cymed_pharmacy_loyalty_reward"

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class Redemption(BaseModel):
    class Status(models.TextChoices):
        ISSUED = "issued", "Issued"
        USED = "used", "Used"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    account = models.ForeignKey(
        PatientLoyaltyAccount,
        on_delete=models.CASCADE,
        related_name="redemptions",
    )
    reward = models.ForeignKey(Reward, on_delete=models.PROTECT, related_name="redemptions")
    at = models.DateTimeField(default=timezone.now)
    points_spent = models.IntegerField()
    code = models.CharField(max_length=64)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ISSUED)

    class Meta:
        db_table = "cymed_pharmacy_loyalty_redemption"

    def __str__(self) -> str:
        return f"Redemption {self.code} ({self.status})"
