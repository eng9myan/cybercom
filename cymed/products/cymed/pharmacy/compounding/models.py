"""CyMed Pharmacy Compounding domain models."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class CompoundingFormulation(BaseModel):
    class Kind(models.TextChoices):
        STERILE = "sterile", "Sterile"
        NON_STERILE = "non_sterile", "Non-Sterile"
        HAZARDOUS = "hazardous", "Hazardous"
        IV_ADMIXTURE = "iv_admixture", "IV Admixture"
        TPN = "tpn", "TPN"

    class UspChapter(models.TextChoices):
        USP797 = "usp797", "USP <797>"
        USP795 = "usp795", "USP <795>"
        USP800 = "usp800", "USP <800>"
        NONE = "none", "None"

    class DosageForm(models.TextChoices):
        CAPSULE = "capsule", "Capsule"
        CREAM = "cream", "Cream"
        OINTMENT = "ointment", "Ointment"
        SOLUTION = "solution", "Solution"
        SUSPENSION = "suspension", "Suspension"
        INJECTION = "injection", "Injection"
        IV_BAG = "iv_bag", "IV Bag"

    class Storage(models.TextChoices):
        ROOM = "room", "Room"
        REFRIGERATED = "refrigerated", "Refrigerated"
        FROZEN = "frozen", "Frozen"

    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.NON_STERILE)
    usp_chapter = models.CharField(max_length=32, choices=UspChapter.choices, default=UspChapter.NONE)
    dosage_form = models.CharField(max_length=32, choices=DosageForm.choices, default=DosageForm.SOLUTION)
    final_volume_ml = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    beyond_use_hours = models.IntegerField(default=24)
    storage = models.CharField(max_length=32, choices=Storage.choices, default=Storage.ROOM)
    requires_hood = models.BooleanField(default=False)
    requires_ppe = models.BooleanField(default=False)
    controlled_substance = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_pharmacy_compounding_formulation"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class CompoundingIngredient(BaseModel):
    formulation = models.ForeignKey(
        CompoundingFormulation,
        on_delete=models.CASCADE,
        related_name="ingredients",
    )
    position = models.IntegerField(default=0)
    drug_id = models.UUIDField(null=True, blank=True)
    ingredient_name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    uom = models.CharField(max_length=16)
    is_active_ingredient = models.BooleanField(default=False)
    hazard_class = models.CharField(max_length=32, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_compounding_ingredient"
        ordering = ["formulation_id", "position"]

    def __str__(self) -> str:
        return f"{self.ingredient_name} ({self.quantity} {self.uom})"


class CompoundingOrder(BaseModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        VERIFIED = "verified", "Verified"
        INGREDIENTS_PULLED = "ingredients_pulled", "Ingredients Pulled"
        MIXING = "mixing", "Mixing"
        QA_PENDING = "qa_pending", "QA Pending"
        RELEASED = "released", "Released"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    class Priority(models.TextChoices):
        ROUTINE = "routine", "Routine"
        URGENT = "urgent", "Urgent"
        STAT = "stat", "Stat"

    tenant_id = models.UUIDField(db_index=True)
    prescription_id = models.UUIDField(null=True, blank=True)
    patient_profile_id = models.UUIDField(null=True, blank=True, db_index=True)
    formulation = models.ForeignKey(
        CompoundingFormulation,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    requested_qty = models.IntegerField(default=1)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.REQUESTED)
    priority = models.CharField(max_length=32, choices=Priority.choices, default=Priority.ROUTINE)
    assigned_compounder_id = models.UUIDField(null=True, blank=True)
    assigned_verifier_id = models.UUIDField(null=True, blank=True)
    hood_id = models.CharField(max_length=64, blank=True)
    lot_number = models.CharField(max_length=64, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    release_signed_by = models.UUIDField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    reject_reason = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_pharmacy_compounding_order"

    def __str__(self) -> str:
        return f"Order {self.id} - {self.status}"


class CompoundingStep(BaseModel):
    class StepKind(models.TextChoices):
        HAND_HYGIENE = "hand_hygiene", "Hand Hygiene"
        GOWNING = "gowning", "Gowning"
        GATHER = "gather", "Gather"
        CALC = "calc", "Calculation"
        MEASURE = "measure", "Measure"
        MIX = "mix", "Mix"
        FILL = "fill", "Fill"
        LABEL = "label", "Label"
        QA_VISUAL = "qa_visual", "QA Visual"
        QA_GC = "qa_gc", "QA GC"
        RELEASE = "release", "Release"

    class Result(models.TextChoices):
        PENDING = "pending", "Pending"
        PASS = "pass", "Pass"
        FAIL = "fail", "Fail"
        SKIPPED = "skipped", "Skipped"

    order = models.ForeignKey(
        CompoundingOrder,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    position = models.IntegerField()
    step_kind = models.CharField(max_length=32, choices=StepKind.choices)
    description = models.TextField(blank=True)
    performed_by = models.UUIDField(null=True, blank=True)
    performed_at = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=32, choices=Result.choices, default=Result.PENDING)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_pharmacy_compounding_step"
        ordering = ["order_id", "position"]

    def __str__(self) -> str:
        return f"Step {self.position} {self.step_kind} - {self.result}"


class IngredientLot(BaseModel):
    formulation = models.ForeignKey(
        CompoundingFormulation,
        on_delete=models.CASCADE,
        related_name="ingredient_lots",
    )
    ingredient_name = models.CharField(max_length=255)
    lot_number = models.CharField(max_length=64)
    expiry_date = models.DateField(null=True, blank=True)
    ndc = models.CharField(max_length=32, blank=True)
    qty_on_hand = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    source_vendor = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_compounding_ingredient_lot"

    def __str__(self) -> str:
        return f"{self.ingredient_name} lot {self.lot_number}"


class QATest(BaseModel):
    class Kind(models.TextChoices):
        VISUAL = "visual", "Visual"
        PH = "ph", "pH"
        POTENCY = "potency", "Potency"
        STERILITY = "sterility", "Sterility"
        ENDOTOXIN = "endotoxin", "Endotoxin"

    class Result(models.TextChoices):
        PENDING = "pending", "Pending"
        PASS = "pass", "Pass"
        FAIL = "fail", "Fail"

    order = models.ForeignKey(
        CompoundingOrder,
        on_delete=models.CASCADE,
        related_name="qa_tests",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    result = models.CharField(max_length=32, choices=Result.choices, default=Result.PENDING)
    value = models.CharField(max_length=64, blank=True)
    performed_by = models.UUIDField(null=True, blank=True)
    performed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_pharmacy_compounding_qa_test"

    def __str__(self) -> str:
        return f"QA {self.kind} - {self.result}"
