"""
CyMed Payments — models per P0-2 spec.
"""
import secrets
from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel, SoftDeleteMixin


# ── Wallet ──────────────────────────────────────────────────────────────
class PatientWallet(BaseModel):
    profile = models.OneToOneField(
        "cymed_patient_portal.PatientPortalProfile",
        on_delete=models.CASCADE,
        related_name="wallet",
    )
    currency = models.CharField(max_length=3, default="SAR")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    top_up_locked = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_patient_wallets"


# ── Payment method ──────────────────────────────────────────────────────
class PaymentMethod(BaseModel, SoftDeleteMixin):
    TYPES = [
        ("card", "Card"),
        ("apple_pay", "Apple Pay"),
        ("google_pay", "Google Pay"),
        ("stc_pay", "STC Pay"),
        ("cliq", "CliQ"),
        ("bank_transfer", "Bank Transfer"),
        ("wallet", "Wallet"),
    ]
    GATEWAYS = [
        ("hyperpay", "HyperPay"),
        ("checkout", "Checkout.com"),
        ("stripe", "Stripe"),
        ("stc", "STC Pay"),
        ("cliq", "CliQ"),
    ]

    profile = models.ForeignKey(
        "cymed_patient_portal.PatientPortalProfile",
        on_delete=models.CASCADE,
        related_name="payment_methods",
    )
    type = models.CharField(max_length=20, choices=TYPES)
    brand = models.CharField(max_length=50, blank=True)
    last4 = models.CharField(max_length=4, blank=True)
    gateway = models.CharField(max_length=20, choices=GATEWAYS)
    gateway_token = models.CharField(max_length=500)  # PCI-safe token, never PAN
    holder_name = models.CharField(max_length=200, blank=True)
    is_default = models.BooleanField(default=False)
    expires_at = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cymed_payment_methods"
        indexes = [models.Index(fields=["profile", "is_default"])]


# ── Insurance ───────────────────────────────────────────────────────────
class InsurancePolicy(BaseModel, SoftDeleteMixin):
    TIER_CHOICES = [("gold", "Gold"), ("silver", "Silver"), ("bronze", "Bronze"), ("other", "Other")]
    VERIFIED_VIA = [
        ("nphies", "NPHIES"),
        ("jofotara", "JoFotara"),
        ("manual", "Manual"),
        ("clearinghouse", "Clearinghouse"),
    ]

    profile = models.ForeignKey(
        "cymed_patient_portal.PatientPortalProfile",
        on_delete=models.CASCADE,
        related_name="insurance_policies",
    )
    insurer_code = models.CharField(max_length=50, db_index=True)
    policy_number = models.CharField(max_length=100)
    member_no = models.CharField(max_length=100)
    network_tier = models.CharField(max_length=20, choices=TIER_CHOICES, blank=True)
    deductible = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    deductible_met = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    co_pay_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    co_pay_fixed = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    pre_auth_required = models.JSONField(default=list, blank=True)
    excluded_services = models.JSONField(default=list, blank=True)
    card_image = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_via = models.CharField(max_length=20, choices=VERIFIED_VIA, blank=True)

    class Meta:
        db_table = "cymed_insurance_policies"


class EligibilityCheck(BaseModel):
    policy = models.ForeignKey(InsurancePolicy, on_delete=models.CASCADE,
                                related_name="eligibility_checks")
    service_code = models.CharField(max_length=50, db_index=True)
    provider_tenant_id = models.UUIDField(null=True, blank=True)
    covered = models.BooleanField()
    co_pay_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    requires_preauth = models.BooleanField(default=False)
    checked_at = models.DateTimeField(auto_now_add=True)
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cymed_eligibility_checks"
        ordering = ["-checked_at"]


class PreAuthorization(BaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    policy = models.ForeignKey(InsurancePolicy, on_delete=models.CASCADE)
    provider_tenant_id = models.UUIDField()
    service_code = models.CharField(max_length=50)
    clinical_justification = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reference_number = models.CharField(max_length=100, blank=True)
    approved_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cymed_pre_authorizations"


# ── Unified bill ────────────────────────────────────────────────────────
def _default_bill_number():
    return f"BILL-{secrets.token_hex(6).upper()}"


class UnifiedBill(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending_insurance", "Pending insurance"),
        ("patient_due", "Patient due"),
        ("partial", "Partial"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]

    bill_number = models.CharField(max_length=50, unique=True, default=_default_bill_number)
    patient_profile = models.ForeignKey(
        "cymed_patient_portal.PatientPortalProfile",
        on_delete=models.PROTECT,
        related_name="bills",
    )
    encounter_ids = models.JSONField(default=list, blank=True)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    vat = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    insurance_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    patient_due = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="draft", db_index=True)
    zatca_qr = models.TextField(blank=True)
    zatca_uuid = models.CharField(max_length=100, blank=True)
    jofotara_qr = models.TextField(blank=True)
    jofotara_uuid = models.CharField(max_length=100, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_unified_bills"
        ordering = ["-created_at"]

    def recompute(self):
        items = self.line_items.all()
        self.subtotal = sum((i.amount for i in items), Decimal("0"))
        self.vat = sum((i.vat for i in items), Decimal("0"))
        self.total = self.subtotal + self.vat
        insured = sum((i.insurance_paid for i in items), Decimal("0"))
        self.insurance_paid = insured
        self.patient_due = self.total - insured
        self.save(update_fields=["subtotal", "vat", "total", "insurance_paid", "patient_due", "updated_at"])


class BillLineItem(BaseModel):
    CATEGORIES = [
        ("consultation", "Consultation"),
        ("procedure", "Procedure"),
        ("medication", "Medication"),
        ("lab", "Lab"),
        ("imaging", "Imaging"),
        ("room", "Room"),
        ("supply", "Supply"),
        ("other", "Other"),
    ]

    bill = models.ForeignKey(UnifiedBill, on_delete=models.CASCADE, related_name="line_items")
    provider_tenant_id = models.UUIDField()
    encounter_id = models.UUIDField(null=True, blank=True)
    service_code = models.CharField(max_length=50)
    service_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1"))
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    vat = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    category = models.CharField(max_length=20, choices=CATEGORIES, default="other")
    insurance_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))

    class Meta:
        db_table = "cymed_bill_line_items"


# ── Transactions ────────────────────────────────────────────────────────
def _default_txn_number():
    return f"TXN-{secrets.token_hex(6).upper()}"


def _default_payment_request_token():
    return secrets.token_urlsafe(48)


class PaymentTransaction(BaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
        ("disputed", "Disputed"),
    ]

    txn_number = models.CharField(max_length=50, unique=True, default=_default_txn_number)
    bill = models.ForeignKey(UnifiedBill, on_delete=models.PROTECT, related_name="transactions")
    payer_profile = models.ForeignKey(
        "cymed_patient_portal.PatientPortalProfile",
        on_delete=models.PROTECT,
        related_name="payments_made",
    )
    payee_profile = models.ForeignKey(
        "cymed_patient_portal.PatientPortalProfile",
        on_delete=models.PROTECT,
        related_name="payments_received",
    )
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default="SAR")
    method_type = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    gateway_reference = models.CharField(max_length=200, blank=True)
    gateway_raw = models.JSONField(default=dict, blank=True)
    on_behalf_note = models.CharField(max_length=500, blank=True)
    delegation_id = models.UUIDField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_payment_transactions"
        ordering = ["-created_at"]


class PaymentRequest(BaseModel):
    bill = models.ForeignKey(UnifiedBill, on_delete=models.CASCADE, related_name="payment_requests")
    requester_profile = models.ForeignKey(
        "cymed_patient_portal.PatientPortalProfile",
        on_delete=models.CASCADE,
    )
    payer_phone = models.CharField(max_length=30, blank=True)
    payer_email = models.EmailField(blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    token = models.CharField(max_length=64, unique=True, db_index=True,
                              default=_default_payment_request_token)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL,
                                     null=True, blank=True)

    class Meta:
        db_table = "cymed_payment_requests"


class Installment(BaseModel):
    PROVIDERS = [("tabby", "Tabby"), ("tamara", "Tamara"), ("bank_bnpl", "Bank BNPL")]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("defaulted", "Defaulted"),
        ("cancelled", "Cancelled"),
    ]

    bill = models.ForeignKey(UnifiedBill, on_delete=models.PROTECT, related_name="installments")
    provider = models.CharField(max_length=20, choices=PROVIDERS)
    plan_reference = models.CharField(max_length=200)
    number_of_installments = models.IntegerField()
    monthly_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        db_table = "cymed_installments"


class RevenueSettlement(BaseModel):
    """Aggregator model split — one payout row per provider per transaction."""
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.PROTECT,
                                     related_name="settlements")
    provider_tenant_id = models.UUIDField(db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    commission = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    payout_at = models.DateTimeField(null=True, blank=True)
    payout_reference = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "cymed_revenue_settlements"
