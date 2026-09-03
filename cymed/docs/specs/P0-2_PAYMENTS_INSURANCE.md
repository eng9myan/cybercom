# P0-2 · Payments + Insurance + Delegated-Pay — Technical Spec

**Owner:** CyMed Platform · **Status:** SPEC · **Target:** Sprint 3-4
**Depends on:** P0-1 (auth), existing `platform.wallet`, `cycom` ERP
**Blocks:** RCM Engine (P0-6) needs claims data

---

## 1. Product Requirements

### Goals
- Unified bill per patient across hospital + clinic + pharmacy + lab + imaging.
- Real-time insurance eligibility + pre-auth + coverage lookup (NPHIES / JoFotara).
- Delegated payments: family / friend / employer pays on behalf of patient.
- Health wallet (top-up + balance).
- Installments (Tabby / Tamara).
- ZATCA / JoFotara stamped invoices automatic.

### Model choice
Start **Model B (Router)** — patient pays directly to provider merchant account; CyMed keeps SaaS fee + audit only. No financial-license required in KSA / Jordan.
Migrate to **Model A (Aggregator)** when PCI DSS Level 1 + SAMA Open Banking licensing complete (~6 months).

---

## 2. Data Model — new Django app `products.cymed.payments`

```python
class PatientWallet(BaseModel):
    profile          = OneToOne(PatientPortalProfile, related_name='wallet')
    currency         = CharField(3, default='SAR')
    balance          = DecimalField(15, 2, default=0)
    top_up_locked    = Boolean(default=False)      # frozen accts

class PaymentMethod(BaseModel, SoftDeleteMixin):
    profile          = FK(PatientPortalProfile, related_name='payment_methods')
    type             = Choice('card','apple_pay','google_pay','stc_pay','cliq','bank_transfer','wallet')
    brand            = CharField(50, blank=True)         # visa, mc, mada
    last4            = CharField(4, blank=True)
    gateway          = Choice('hyperpay','checkout','stripe','stc','cliq')
    gateway_token    = CharField(500)                    # PCI-safe token, no PAN
    holder_name      = CharField(200, blank=True)
    is_default       = Boolean(default=False)
    expires_at       = DateField(null=True)

class InsurancePolicy(BaseModel):
    profile          = FK(PatientPortalProfile, related_name='insurance_policies')
    insurer_code     = CharField(50)                     # BUPA, TAWUNIYA, MEDGULF, NSSF, ...
    policy_number    = CharField(100)
    member_no        = CharField(100)
    network_tier     = Choice('gold','silver','bronze','other', blank=True)
    deductible       = DecimalField(15, 2, null=True)
    deductible_met   = DecimalField(15, 2, default=0)
    co_pay_percent   = DecimalField(5, 2, null=True)
    co_pay_fixed     = DecimalField(15, 2, null=True)
    valid_from       = DateField(null=True)
    valid_to         = DateField(null=True)
    pre_auth_required = JSONField(default=list)          # list of service codes
    excluded_services = JSONField(default=list)
    card_image       = TextField(blank=True)             # base64 encrypted
    verified_at      = DateTimeField(null=True)
    verified_via     = Choice('nphies','jofotara','manual','clearinghouse', blank=True)

class EligibilityCheck(BaseModel):
    policy           = FK(InsurancePolicy, related_name='eligibility_checks')
    service_code     = CharField(50)
    provider_tenant_id = UUIDField(null=True)
    covered          = Boolean()
    co_pay_amount    = DecimalField(15, 2, null=True)
    requires_preauth = Boolean(default=False)
    checked_at       = DateTimeField(auto_now_add=True)
    raw_response     = JSONField()                       # NPHIES / JoFotara payload

class PreAuthorization(BaseModel):
    policy           = FK(InsurancePolicy)
    provider_tenant_id = UUIDField()
    service_code     = CharField(50)
    clinical_justification = TextField()
    status           = Choice('pending','approved','denied','expired','cancelled')
    reference_number = CharField(100, blank=True)
    approved_amount  = DecimalField(15, 2, null=True)
    approved_at      = DateTimeField(null=True)
    expires_at       = DateTimeField(null=True)
    raw_response     = JSONField()

class UnifiedBill(BaseModel):
    bill_number      = CharField(50, unique=True)
    patient_profile  = FK(PatientPortalProfile, related_name='bills')
    encounter_ids    = JSONField(default=list)           # multi-encounter across providers
    subtotal         = DecimalField(15, 2)
    vat              = DecimalField(15, 2, default=0)
    total            = DecimalField(15, 2)
    insurance_paid   = DecimalField(15, 2, default=0)
    patient_due      = DecimalField(15, 2)
    status           = Choice('draft','pending_insurance','patient_due','partial','paid','cancelled')
    zatca_qr         = TextField(blank=True)
    zatca_uuid       = CharField(100, blank=True)
    jofotara_qr      = TextField(blank=True)
    jofotara_uuid    = CharField(100, blank=True)
    issued_at        = DateTimeField(null=True)
    paid_at          = DateTimeField(null=True)

class BillLineItem(BaseModel):
    bill             = FK(UnifiedBill, related_name='line_items')
    provider_tenant_id = UUIDField()
    encounter_id     = UUIDField(null=True)
    service_code     = CharField(50)                     # CPT / SFDA / local
    service_name     = CharField(200)
    quantity         = DecimalField(10, 2, default=1)
    unit_price       = DecimalField(15, 2)
    amount           = DecimalField(15, 2)
    vat              = DecimalField(15, 2, default=0)
    category         = Choice('consultation','procedure','medication','lab','imaging','room','supply','other')
    insurance_paid   = DecimalField(15, 2, default=0)

class PaymentTransaction(BaseModel):
    txn_number       = CharField(50, unique=True)
    bill             = FK(UnifiedBill, related_name='transactions')
    payer_profile    = FK(PatientPortalProfile, related_name='payments_made')
    payee_profile    = FK(PatientPortalProfile, related_name='payments_received')  # patient whose bill
    payment_method   = FK(PaymentMethod, null=True)
    amount           = DecimalField(15, 2)
    currency         = CharField(3, default='SAR')
    method_type      = CharField(50)                     # denormalised
    status           = Choice('pending','succeeded','failed','refunded','disputed')
    gateway_reference = CharField(200, blank=True)
    gateway_raw      = JSONField(default=dict)
    on_behalf_note   = CharField(500, blank=True)        # 'Paid by Ahmad for his mother'
    delegation_id    = UUIDField(null=True)              # links to DelegatedAccess if delegated pay
    completed_at     = DateTimeField(null=True)

class PaymentRequest(BaseModel):
    """Payment link: patient asks anyone (not necessarily a delegate) to pay."""
    bill             = FK(UnifiedBill, related_name='payment_requests')
    requester_profile = FK(PatientPortalProfile)
    payer_phone      = CharField(30, blank=True)         # SMS/WhatsApp target
    payer_email      = EmailField(blank=True)
    amount           = DecimalField(15, 2)
    token            = CharField(64, unique=True)        # random URL-safe
    expires_at       = DateTimeField()
    used_at          = DateTimeField(null=True)
    transaction      = FK(PaymentTransaction, null=True)

class Installment(BaseModel):
    """Tabby / Tamara installment plan on a bill."""
    bill             = FK(UnifiedBill, related_name='installments')
    provider         = Choice('tabby','tamara','bank_bnpl')
    plan_reference   = CharField(200)
    number_of_installments = IntegerField()
    monthly_amount   = DecimalField(15, 2)
    status           = Choice('active','completed','defaulted','cancelled')

class RevenueSettlement(BaseModel):
    """When aggregator model runs: splits a payment to each provider tenant."""
    transaction      = FK(PaymentTransaction, related_name='settlements')
    provider_tenant_id = UUIDField()
    amount           = DecimalField(15, 2)
    commission       = DecimalField(15, 2, default=0)
    payout_at        = DateTimeField(null=True)
    payout_reference = CharField(200, blank=True)
```

Migrations: `python manage.py makemigrations payments`.

---

## 3. Gateway Adapters

Isolate payment gateways behind a common interface `payments/gateways/base.py`:

```python
class BaseGateway(ABC):
    name: str
    supports: list[str]                                  # ['card','apple_pay','stc_pay',...]

    def tokenize(self, payload: dict) -> str: ...       # PAN → token; never store PAN
    def charge(self, token: str, amount: Decimal, currency: str,
               metadata: dict) -> ChargeResult: ...
    def refund(self, gateway_ref: str, amount: Decimal | None) -> RefundResult: ...
    def webhook_verify(self, headers: dict, body: bytes) -> bool: ...
    def webhook_parse(self, body: bytes) -> WebhookEvent: ...
```

Concrete adapters:
- `gateways/hyperpay.py` — KSA (Mada / Visa / MC / Apple Pay / STC Pay).
- `gateways/checkout_com.py` — KSA + Jordan international cards.
- `gateways/stripe.py` — Fallback + global.
- `gateways/stc_pay.py` — STC Pay direct (KSA wallet).
- `gateways/cliq.py` — Jordan Ministry of Finance instant transfers.

Default per region:
- KSA: HyperPay primary, Checkout fallback, STC Pay for wallet.
- Jordan: Checkout primary, CliQ for local transfers.

---

## 4. Insurer Adapters

`payments/insurers/base.py`:
```python
class BaseInsurer(ABC):
    code: str
    country: str                                         # 'SA', 'JO'
    def eligibility(self, policy: InsurancePolicy, service_code: str,
                    provider_tenant_id: UUID) -> EligibilityResult: ...
    def preauth_submit(self, policy, service_code, justification) -> PreAuthResult: ...
    def preauth_status(self, reference) -> PreAuthResult: ...
    def claim_submit(self, bill: UnifiedBill) -> ClaimResult: ...
```

Concrete adapters:
- `insurers/nphies.py` — routes to Saudi NPHIES for BUPA, Tawuniya, MedGulf, Walaa, Malath, Arabia.
- `insurers/jofotara.py` — Jordan clearinghouse (NSSF + private).
- `insurers/direct_bupa.py`, `direct_tawuniya.py`, `direct_medgulf.py` — direct API when available (bypass clearing).
- `insurers/manual.py` — fallback for smaller insurers; queues human review.

Registry pattern in `payments/insurers/__init__.py`:
```python
INSURERS = {
    'BUPA': DirectBupaInsurer(),
    'TAWUNIYA': DirectTawuniyaInsurer(),
    'MEDGULF': DirectMedGulfInsurer(),
    'NSSF': JoFotaraInsurer(),
    '_default_sa': NphiesInsurer(),
    '_default_jo': JoFotaraInsurer(),
}
```

---

## 5. Delegated-Pay Flow (the "moat" sequence)

```
1. Mother's bill created for surgery. UnifiedBill.patient_due = 800 SAR.
2. Mother opens app → sees bill → taps "Ask Ahmad to Pay".
   POST /billing/bills/{id}/payment-request {payer_phone: '+9665...', amount: 800}
   → server creates PaymentRequest with 64-char token, expiry 48h.
   → SMS via cyintegrationhub: "Your mother requests SAR 800 for her hospital bill.
      Pay: https://p.cymed.sa/pay/{token}"
3. Ahmad taps link → app deep-link opens PaymentRequest confirmation screen.
   If Ahmad not logged in → OTP.
4. Ahmad selects PaymentMethod → confirms.
   POST /billing/payment-requests/{token}/pay {method_id: '...'}
   → gateway.charge() → PaymentTransaction created with payer=Ahmad, payee=Mother.
   → bill.status → paid, patient_due → 0.
5. Both parties notified via push + SMS.
6. Optional: Ahmad sees receipt in his 'Payments Made' list; mother sees 'Paid by Ahmad'.
```

Delegated payment via existing DelegatedAccess (P0-1):
- If Ahmad already has DelegatedAccess {subject=Mother, scope_pay_bills=True, max_amount=5000},
  skip PaymentRequest → Ahmad's app shows Mother's bills directly under "Family bills" → one-tap pay.

---

## 6. OpenAPI Endpoints (Payments API)

Base: `/api/v1/patient-app/billing/` (extends P0-1 stubs).

### Bills
```
GET    /bills                       ?scope=own|delegated|all  → [UnifiedBill]
GET    /bills/{id}                  → UnifiedBill + line_items
POST   /bills/{id}/pay              { method_id, amount?, on_behalf_of? }
POST   /bills/{id}/payment-request  { payer_phone|payer_email, amount, note? } → link
POST   /bills/{id}/installments     { provider, number_of_installments }
GET    /bills/{id}/receipt          → signed PDF url (ZATCA / JoFotara stamped)
```

### Payment requests (public — no auth required for the payer)
```
GET    /payment-requests/{token}                     → { bill_summary, amount, requester_name }
POST   /payment-requests/{token}/pay {method_id}     → PaymentTransaction
```

### Payment methods
```
GET    /payment-methods            → [PaymentMethod]
POST   /payment-methods            { gateway_token, type, ... } → PaymentMethod
DELETE /payment-methods/{id}
POST   /payment-methods/{id}/default
```

### Wallet
```
GET    /wallet                     → PatientWallet
POST   /wallet/top-up              { method_id, amount }
GET    /wallet/transactions        → [PaymentTransaction]
POST   /wallet/transfer            { recipient_profile_id, amount, note }
```

### Insurance
```
GET    /insurance                  → [InsurancePolicy]
POST   /insurance                  { insurer_code, policy_number, member_no, card_image? }
POST   /insurance/{id}/verify      → triggers verified_via check → InsurancePolicy
POST   /insurance/{id}/eligibility { service_code, provider_tenant_id? } → EligibilityCheck
POST   /insurance/{id}/preauth     { service_code, provider_tenant_id, justification } → PreAuthorization
GET    /insurance/{id}/preauth/{preauth_id} → PreAuthorization status
GET    /insurance/{id}/coverage    ?search=knee_arthroplasty → [ServiceCoverage] (encyclopedia)
```

### Webhooks (public — signature verified)
```
POST   /webhooks/hyperpay
POST   /webhooks/checkout
POST   /webhooks/stripe
POST   /webhooks/stc-pay
POST   /webhooks/cliq
POST   /webhooks/tabby
POST   /webhooks/tamara
```

---

## 7. ZATCA / JoFotara Integration
Reuse existing `products.cymed.integrations.zakata` and `products.cymed.integrations.jofawtra`. When a `UnifiedBill.status` transitions to `paid`:

1. Serialise bill to XML (UBL 2.1 or ZATCA XML depending on country).
2. Call existing `zakata.client.submit_invoice()` / `jofawtra.client.submit_invoice()`.
3. Store returned QR + UUID on the bill.
4. Async retry queue (Celery) on failure with exponential back-off.

Signals in `payments/signals.py`:
```python
@receiver(post_save, sender=UnifiedBill)
def stamp_invoice_after_payment(sender, instance, **kwargs):
    if instance.status == 'paid' and not (instance.zatca_uuid or instance.jofotara_uuid):
        stamp_bill.delay(instance.id)
```

---

## 8. Compliance
- PCI DSS: never persist PAN; gateways return tokens only. Cardholder data flow diagrammed at `docs/security/PCI_DSS_scope.md`.
- SAMA Open Banking: for aggregator model (Phase 2) — separate spec P0-2b.
- CBJ / JoMoPay: for Jordan wallets — via CliQ adapter.
- Consent audit: every delegated payment logs `payer_profile`, `payee_profile`, `delegation_id`.
- AML: PaymentTransaction > SAR 5,000 (from delegate ≠ family relation) queued for KYC review.

---

## 9. Rollout

**Sprint 3** — models + migrations + gateway registry + HyperPay adapter + StripeChecking adapter.
**Sprint 4** — insurance registry + NPHIES + JoFotara insurer adapters + eligibility + pre-auth endpoints.
**Sprint 5** — UnifiedBill CRUD + line-item aggregation cron + ZATCA/JoFotara stamping.
**Sprint 6** — delegated pay flows + PaymentRequest + wallet + Tabby/Tamara.

---

## 10. Next artifact
`docs/specs/openapi/payments.yaml` — full OpenAPI schema for §6 endpoints.
Then P0-2 CODE: create `products/cymed/payments/` app, models, migrations, gateway registry, HyperPay skeleton.
