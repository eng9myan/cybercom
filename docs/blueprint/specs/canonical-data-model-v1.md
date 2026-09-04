# Spec — Canonical Data Model v1

> Implementable field-level spec for the CyberCom canonical core. Turns `D` (the ERD
> brief) into something a backend engineer builds from. **Status:** draft for CDAC
> ratification (Phase 0 exit gate). Target: the `platform/` + `products/cycom/` schema.
> Django + PostgreSQL. Every deviation from this spec is an RFC to CDAC.

---

## 1. Model conventions

### 1.1 Base classes (`platform/common/models.py`)

Today's `BaseModel` = `UUIDPrimaryKeyMixin + TimestampMixin + TenantScopedMixin`. v1 extends it:

```python
class TenantScopedMixin(models.Model):
    tenant_id   = models.UUIDField(db_index=True, editable=False)
    objects     = TenantScopedManager()      # NEW — see §2.2
    all_tenants = models.Manager()           # NEW — explicit escape hatch, audited use only
    class Meta: abstract = True

class AttributesMixin(models.Model):         # NEW
    # flavor-specific fields live here, validated against a registered profile (§3)
    attributes  = models.JSONField(default=dict, blank=True)
    class Meta: abstract = True

class OptimisticLockMixin(models.Model):     # NEW
    row_version = models.PositiveBigIntegerField(default=0)   # bumped in save()
    class Meta: abstract = True

class BaseModel(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin,
                AttributesMixin, OptimisticLockMixin):
    created_by  = models.UUIDField(null=True, editable=False)   # NEW
    updated_by  = models.UUIDField(null=True, editable=False)   # NEW
    class Meta: abstract = True

class PlatformModel(UUIDPrimaryKeyMixin, TimestampMixin):
    """non-tenant-scoped: Tenant registry, identity config, system settings"""
```

`SoftDeleteMixin` unchanged (`is_deleted`, `deleted_at`, `soft_delete()`); add a
`SoftDeleteManager` default so `objects` hides deleted rows and `with_deleted` shows them.

### 1.2 Every tenant-scoped table has

| Column | Type | Rule |
|---|---|---|
| `id` | uuid pk | `uuid4`, immutable |
| `tenant_id` | uuid, indexed, **not null** | set by manager from context (§2.2); RLS-enforced |
| `created_at` / `updated_at` | timestamptz | `created_at` immutable + indexed; `updated_at` auto |
| `created_by` / `updated_by` | uuid null | actor user id from request context |
| `row_version` | bigint | optimistic lock; `UPDATE ... WHERE row_version = :expected` |
| `attributes` | jsonb | flavor fields, profile-validated |
| `is_deleted` / `deleted_at` | (if `SoftDeleteMixin`) | never hard-delete tenant data via the ORM |

### 1.3 Naming

- Table: `<product>_<entity_plural>` (e.g. `core_orders`, `core_journal_entries`). Existing
  cymed tables (`cymed_*`) keep their names through M4; new canonical tables use `core_*`.
- FK on-delete: `PROTECT` for financial/audit chains; `CASCADE` only for true children
  (order lines, journal lines); `SET_NULL` for optional refs.
- Money: `DecimalField(max_digits=18, decimal_places=4)` + a sibling `<field>_currency`
  `CharField(3)`. Never float. Store minor-unit-safe.
- Enums: `TextChoices` classes; the DB column is `varchar` + a `CHECK` where stable.

---

## 2. Tenant isolation — the four layers, concretely

### 2.1 Layer 1 — RLS (PostgreSQL) — **DDL + tooling shipped 2026-09-04**

Per tenant-scoped table:

```sql
ALTER TABLE "cycom_arap_invoices" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "cycom_arap_invoices" FORCE ROW LEVEL SECURITY;   -- binds the table owner too
CREATE POLICY tenant_isolation ON "cycom_arap_invoices"
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
```

`current_setting(..., true)` (missing_ok) → an **unset GUC yields NULL**, and `tenant_id = NULL`
is false, so a connection with no tenant context sees **no rows** (fail-closed).

Shipped (`platform/security/`):
- `rls_ddl.py` — `rls_statements()` / `rls_teardown_statements()` iterate every model with a
  `UUID tenant_id` and emit the DDL above, honouring `settings.TENANT_GUC_SETTING`.
- `management/commands/apply_rls.py` — `manage.py apply_rls [--dry-run] [--teardown] [--force]`.
  Idempotent; PostgreSQL-only (hard-errors on SQLite, never a silent no-op); refuses unless
  `RLS_ENFORCED` or `--force`.
- `management/commands/verify_rls.py` — `manage.py verify_rls [--table <t>]`. Live isolation
  check: in one rolled-back transaction it inserts a probe row for two throwaway tenant
  UUIDs, then asserts each tenant sees only its own, an unset GUC sees none (fail-closed),
  and a cross-tenant UPDATE affects 0 rows. Exit 0 = isolated; `CommandError` = broken or
  the role has `BYPASSRLS`/superuser. Writes nothing. **Run right after `apply_rls` in staging.**
- `TenantContextMiddleware` now also sets the GUC **session-scoped** (`set_config(guc, tid, false)`)
  when `RLS_ENFORCED` — Django autocommit discards a `SET LOCAL`, so `SET LOCAL` in the product
  middleware isn't enough on its own. Reset in `finally`.
- `RLS_ENFORCED` setting (env `CYCOM_RLS_ENFORCED` / `CYMED_RLS_ENFORCED`), default **off**.

**Deploy prerequisites:** the app DB role must NOT be a superuser and must NOT have
`BYPASSRLS`. `FORCE ROW LEVEL SECURITY` covers the case where the app role owns the tables.
A migration / cross-tenant job that must bypass uses `set_session_replication_role('replica')`
(superuser, audit-logged) or a dedicated unrestricted role.

**Rollout:** on the staging box, as the **app DB role** (non-superuser, no `BYPASSRLS`):
1. `export CYCOM_RLS_ENFORCED=1` (and `CYMED_RLS_ENFORCED=1`), restart the app.
2. `python manage.py migrate --noinput`
3. `python manage.py apply_rls` — applies ENABLE + FORCE + policy to every tenant-scoped table.
4. `python manage.py verify_rls` — must print `RLS VERIFY OK`. If it errors, **stop** and
   check the app role's privileges (`\du` — no `Superuser`, no `Bypass RLS`).
5. Smoke: log in as tenant A, confirm the app works; confirm tenant B's data never appears.
6. Promote the same steps to production.

Table-by-table is possible by editing the `tenant_scoped_models()` filter, but all-at-once is
fine given the defence-in-depth already in place (queryset scoping + `save()` autofill).

### 2.2 Layer 2 — app-layer context + save() auto-fill — **IMPLEMENTED 2026-09-04**

Shipped (`platform/common/`):

- `tenant_context.py` — a `ContextVar` with `set_/get_/clear_current_tenant()`, a
  `tenant_context(tid)` context manager, and `TenantContextMissing`.
- `models.py` `TenantScopedMixin.save()` — fills `tenant_id` from the ambient context
  when not passed explicitly; raises `TenantContextMissing` (not a bare `IntegrityError`)
  when there's no context. **Pure Python, no migration; works with every custom manager.**
- `middleware.py` `TenantContextMiddleware` — publishes `request.tenant_id` for the request,
  resets in `finally`. Wired into cycom + cymed after their `TenantIsolationMiddleware`.

> Chosen over the `TenantScopedManager.create()` override in the original draft: `save()`
> is inherited unconditionally, so it can't be bypassed by a model defining its own manager,
> and it also covers `Model(...).save()`, `obj.save()` in a signal, etc. — not just
> `.objects.create()`. The `get_queryset()` filtering from the draft was **deliberately not
> shipped** (too risky to change read scoping across ~1000 models at once; RLS + explicit
> `TenantScopedModelViewSet` scoping stays the read guard).

- Celery: a `@tenant_task` decorator that restores context from a message header — **still to build** (Phase 1).
- **Closed the class of bug found in CyMed** (`pay_bill`, the NPHIES client, etc. creating a
  `BaseModel` row with no `tenant_id`). CyMed suite went 510/5 → **515/0** as a result.

### 2.3 Layer 3 — per-tenant encryption — **shipped 2026-09-04**

Shipped (`platform/security/crypto.py`, `platform/common/fields.py`, `pii_registry.py`):
- **DEK derivation** — `HKDF-SHA256(master_key, salt=tenant_id)`. Every tenant's ciphertext is
  under a distinct key; no per-tenant DEK to store or wrap (rotation = rotate the master +
  re-encrypt). `MASTER_KEY_PROVIDER` swappable for a KMS-per-tenant-key path later
  (`Tenant.encryption_key_ref` reserved for it).
- **Cipher** — AES-256-GCM, random 96-bit nonce per value. Wire: `b"cc1" + nonce(12) + ct+tag`,
  stored as `bytea`.
- **`EncryptedText(classification=..., blind_index=...)`** field — encrypts on write with the
  DEK from the ambient tenant context (raises `TenantContextMissing` if none); decrypts on read
  when context is present, else yields the mask `••••` (never leaks, never crashes a list).
  Tolerates legacy plaintext rows (returns them decoded) so a field can be flipped to encrypted
  without a same-deploy backfill. `blind_index=True` adds a `<name>_bidx` HMAC column for
  exact-match lookup: `.filter(national_id_bidx=blind_index(value))`.
- **Registry** — every `EncryptedText` self-registers `model.field → {pii|phi|financial_id|national_id}`.
  `manage.py dump_pii_map [--json]` prints the data map for the DPIA / residency lint / DSAR.
- **`FIELD_ENCRYPTION_KEY`** setting (env), 32 bytes base64/hex. Prod value from the secret manager.

**Not yet done:** converting the actual columns (`Employee.national_id`/`iqama`/`iban`,
`Patient` demographics, clinical `notes`). Each is a per-model reviewed migration (change the
field + a data migration to encrypt existing rows + populate blind indexes). The field's
legacy-plaintext tolerance makes a phased rollout safe.

### 2.4 Layer 4 — object storage

CyVault keys are `t/<tenant_id>/<collection>/<uuid>`; signed URLs scoped to the prefix; the
bucket/region is chosen from `Tenant.residency_region`.

### 2.5 Test enforcement

`tests/isolation/` — for every `TenantScopedMixin` model: create rows under tenant A, switch
context to tenant B, assert `.objects.all()` returns none, `.get(pk=a_row)` raises, a
cross-tenant FK write is rejected. Runs every CI build; any pass = merge blocked (`H` SEC4).

---

## 3. The `attributes` profile registry (flavor fields without forks)

```python
# platform/common/attribute_profiles.py
@register_profile("order", "service_ticket", version=1)
class ServiceTicketProfile(AttributeProfile):
    bay_id        = fields.UUID(required=True)
    odometer_km   = fields.Integer(min=0)
    complaint     = fields.Text(max_length=2000)
    labour_lines  = fields.List(of=LabourLineSchema)
```

- A flavor's `flavor.yaml` declares `entity_attribute_profiles: { order: "order/service_ticket@1" }`.
- On write, `attributes` is validated against the active profile for that entity in that
  tenant's flavor set; unknown keys rejected (strict).
- Profiles are versioned; a profile bump is an additive migration of the validator, not a schema change.
- Reporting/GraphQL can project `attributes ->> 'odometer_km'` with a GIN index where a flavor needs it.
- **Rule (ADR-0003):** a need that can't be a profile field — it needs its own lifecycle,
  FKs, or heavy querying — goes to CDAC as a `[core+]` primitive, not a bigger JSON blob.

---

## 4. Data residency

- `Tenant.residency_region` (enum: `me-central-1`, `me-south-1`, `ksa-sovereign`, …), set at
  onboarding, immutable without a migration project.
- Enforcement points: DB shard/cluster selection (router), CyVault bucket region, analytics
  warehouse partition, backup target, and log sink. A single `residency.region_for(tenant_id)`
  helper is the only place the mapping lives.
- Regulated categories (PHI, national-identity, financial-identity) **must not** appear in
  cross-region replicas, the global analytics store, or logs — enforced by the PII registry +
  a CI data-flow lint (`H` C1).

---

## 5. Core entities

Legend: `PK` uuid always; `T` = tenant-scoped (`BaseModel`); `P` = platform (`PlatformModel`).
`→` FK. `⇒` FK `PROTECT`. Money fields imply a `_currency` sibling.

### 5.1 Platform & tenancy

#### `Tenant` (P) — `platform_tenants`
| field | type | notes |
|---|---|---|
| legal_name | varchar(255) | |
| slug | varchar(63) unique | subdomain / routing key |
| status | enum(trial, active, suspended, closed) | |
| residency_region | enum | §4, immutable |
| flavor_set | uuid[] → VerticalFlavor | composed flavors (N.1) |
| subscription_id | → Subscription | |
| encryption_key_ref | varchar | KMS key id |
| compliance_flags | jsonb | `{zatca_csid: "...", pdpl_dpia: true, ...}` |
| primary_locale | → Localization | |
| created_at / activated_at / closed_at | timestamptz | |

#### `Organization` (T) — `core_organizations`
A legal/operating entity within a tenant (multi-company). `name`, `country`, `vat_number`,
`cr_number` (commercial registration), `base_currency`, `fiscal_year_start` (month/day),
`chart_of_accounts_id` ⇒ its own COA. A tenant has ≥ 1.

#### `Branch` (T) — `core_branches`
`organization` ⇒ Organization, `name`, `code`, `type` (store, clinic, warehouse, bay,
kitchen, pump_island, office), `address` (jsonb), `timezone`, `geo` (point, nullable),
`is_active`. POS terminals, stock, staff, schedules attach here.

#### `User` (P) — identity lives in Keycloak/CyIdentity; `platform_users` is a local projection
`external_id` (Keycloak sub), `email`, `name`, `phone`, `status`, `mfa_enrolled`. Never stores a password.

#### `Membership` (T) — `core_memberships`
`user_id` → User, `role` ⇒ Role, optional `organization`/`branch` scope, `status`,
`invited_at`, `accepted_at`. The access-granting join.

#### `Role` (T, or P for system roles) — `core_roles`
`name`, `is_system`, `permissions` (varchar[] of permission keys). Permission keys are a
static registry (`platform/security/permissions.py`), e.g. `order.refund`, `payroll.run`,
`phi.export`.

#### `Policy` (T) — `core_policies`
ABAC rule for cross-tenant access + step-up-auth requirements. `subject` (jsonb condition),
`resource` (pattern), `effect` (allow/deny), `obligations` (jsonb, e.g. `{step_up: "webauthn"}`),
`priority`. Default-deny evaluation.

#### `Subscription` (P) — `platform_subscriptions`
`tenant_id`, `tier` (starter/professional/enterprise), `entitlements` (jsonb: caps on
locations/terminals/providers/users/api_rate), `billing_cycle`, `psp_customer_ref`,
`current_period_end`, `status`.

#### `VerticalFlavor` (P) — `platform_vertical_flavors`
`key`, `name`, `version` (semver), `definition` (jsonb — the validated `flavor.yaml`),
`status` (engine-only/community/verified/certified/ga), `feature_flag`, `owner`,
`certified_at`. Registry maintained per `schemas/flavor-registry.yaml`.

#### `LayoutTemplate` (P) — `platform_layout_templates`
`flavor_key`, `name`, `route`, `slots` (jsonb: slot → design-system component id), `roles`,
`device`. No raw markup — component ids only.

#### `Integration` (T) — `core_integrations`
`type` (psp, delivery_aggregator, fatoora, jofotara, nphies, wps_bank, whatsapp, …),
`provider`, `status`, `credential_ref` (→ credential vault, never inline), `config` (jsonb),
`sync_cursor` (jsonb), `last_ok_at`, `last_error`.

#### `APIKey` / `OAuthClient` (T) — `core_api_clients`
`name`, `client_type` (api_key | oauth2), `hashed_secret`, `scopes` (varchar[]),
`rate_tier`, `created_by`, `last_used_at`, `rotated_at`, `revoked_at`.

#### `ConsentGrant` (T) — `core_consent_grants`
`grantor_tenant_id`, `grantee_tenant_id` (or `grantee_user_id`), `scope` (jsonb: entities +
fields + purpose), `expires_at`, `status`, `granted_by`, `revoked_at`. The lawful basis for
every cross-domain / cross-tenant read.

#### `AuditEvent` (T, append-only) — `core_audit_events`
`actor_user_id`, `actor_ip`, `action`, `resource_type`, `resource_id`, `before_hash`,
`after_hash`, `prev_event_hash` (chain), `trace_id`, `occurred_at`. No update/delete. Written
via a dedicated append path, not the ORM `save()`.

#### `DomainEvent` (T, outbox) — `core_domain_events`
`event_type`, `aggregate_type`, `aggregate_id`, `payload` (jsonb, schema-versioned),
`schema_version`, `occurred_at`, `published_at` (null until relayed), `attempts`. The relay
worker moves rows → broker; consumers = analytics, audit, integration hub, flavors.

### 5.2 Catalog & pricing

#### `Catalog` (T) — `core_catalogs`
`organization` ⇒, `name`, `catalog_profile` (retail/auto_parts/jewelry/grocery/pharmacy/
service/fuel/government), `is_default`.

#### `Product` (T, `AttributesMixin`) — `core_products`
`catalog` ⇒, `name`, `slug`, `category` → Category, `type` (good, service, kit, digital),
`tax_class` → TaxClass, `base_uom`, `status`. Profile attributes: fitment[], oe_numbers[],
karat, purity, making_charge_rule, plin/atc_code, etc.

#### `Category` (T) — `core_categories` — self-FK tree (`parent`), `name`, `path` (ltree/text), `sort`.

#### `Variant` (T, `AttributesMixin`) — `core_variants`
`product` ⇒, `name`, `sku_code` (unique per org), `barcodes` (varchar[]), `pack_size`,
`attributes` (size/colour/…), `weight`, `dimensions`.

#### `SKU` (T) — `core_skus`
`variant` ⇒, `branch` → Branch (null = org-wide), `status`. The inventory + costing unit.
Unique (`variant_id`, `branch_id`).

#### `PriceList` (T) — `core_price_lists`
`name`, `currency`, `customer_segment` (null = all), `valid_from`/`valid_to`, `precedence`.
`PriceListEntry`: `price_list` ⇒, `variant` → , `unit_price`, `min_qty`, `rule_type`
(fixed, formula, rate_based, weight_based, tiered), `rule` (jsonb — e.g. live-gold formula).

#### `Promotion` (T) — `core_promotions`
`name`, `kind` (basket, item, bogo, threshold, member_price, markdown), `conditions`
(jsonb), `benefit` (jsonb), `stackable`, `valid_from`/`to`, `budget`, `redemptions`.

### 5.3 Inventory

#### `InventoryLocation` (T) — `core_inventory_locations`
`branch` ⇒, `name`, `type` (warehouse, backroom, shelf, fridge, bay, van), `parent` (self-FK), `is_sellable`.

#### `StockItem` (T) — `core_stock_items`
`sku` ⇒, `location` ⇒, `on_hand` (decimal), `reserved` (decimal), `valuation_method`
(FIFO/AVCO), `avg_cost`. Unique (`sku_id`, `location_id`). Sub-rows for lot/serial/expiry:
`StockLot` (`stock_item` ⇒, `lot_code`, `expiry_date`, `qty`, `unit_cost`), `StockSerial`
(`stock_item` ⇒, `serial`, `status`).

#### `StockMove` (T, append-only-ish) — `core_stock_moves`
`sku` ⇒, `from_location` / `to_location` (nullable), `qty`, `unit_cost`, `move_type`
(receipt, sale, transfer, adjustment, return, production_in, production_out, wastage),
`reason`, `ref_type` / `ref_id` (source doc), `lot_id` / `serial_id` (nullable),
`occurred_at`. Immutable once posted; corrections are new moves.

### 5.4 Orders / POS / fulfilment

#### `Order` (T, `AttributesMixin`) — `core_orders`
The universal transaction aggregate.
| field | type | notes |
|---|---|---|
| number | varchar unique per org | |
| branch ⇒ | Branch | |
| channel | enum(pos, online, b2b, marketplace, service, appointment) | |
| type | enum(sale, quote, return, service_ticket, subscription_order) | |
| customer → | Customer (null for anonymous walk-in) | |
| status | enum(draft, confirmed, fulfilled, invoiced, closed, cancelled) — state machine | |
| appointment_id → | Appointment (nullable) | |
| currency, subtotal, discount_total, tax_total, charge_total, grand_total | | recomputed from lines |
| placed_at, confirmed_at, closed_at | timestamptz | |

`OrderLine` (`core_order_lines`): `order` ⇒ CASCADE, `sku` → , `description`, `qty`,
`unit_price`, `discount`, `tax_rule` → TaxRule, `tax_amount`, `line_total`, `attributes`
(e.g. kitchen mods, prescription link). Invariant: `Σ line_total + tax_total + charge_total − discount_total = grand_total`.

`Fulfilment` (`core_fulfilments`): `order` ⇒, `mode` (pickup, delivery, dine_in, ship,
handover), `status`, `address` (jsonb), `dispatch_provider`, `dispatch_ref`, `lines` (jsonb: order_line_id → qty).

`Payment` (`core_payments`): `order_id` / `invoice_id` (one set), `method` (cash, card,
wallet, insurance, credit, bank_transfer), `provider`, `provider_ref`, `amount`, `status`
(pending, captured, failed, refunded, partially_refunded), `instrument_token`, `captured_at`,
`refunded_amount`. Idempotency key stored.

`PosSession` (`core_pos_sessions`): `branch` ⇒, `terminal_id`, `opened_by`, `opened_at`,
`opening_float`, `closed_at`, `closing_count`, `expected_cash`, `variance`, `status`.

`KdsTicket` (`core_kds_tickets`): `order` ⇒, `station`, `status` (new, preparing, ready,
bumped), `items` (jsonb), `prep_started_at`, `bumped_at`. F&B flavors only.

### 5.5 Procurement

`Vendor` (T) `core_vendors` — `name`, `tax_id`, `payment_terms`, `currency`, `contacts` (jsonb), `rebate_agreements` (jsonb).
`PurchaseOrder` (T) `core_purchase_orders` — `vendor` ⇒, `branch` ⇒, `status`
(draft, approved, sent, partially_received, received, closed), lines mirror OrderLine, `expected_date`.
`GoodsReceipt` (T) `core_goods_receipts` — `purchase_order` ⇒, `received_at`, `lines`
(jsonb: po_line → qty, lot, expiry), generates `StockMove` receipts + landed-cost allocation.

### 5.6 Finance

#### `LedgerAccount` (T) — `core_ledger_accounts`
`organization` ⇒, `code`, `name`, `type` (asset, liability, equity, income, expense),
`parent` (self-FK), `is_postable`, `currency` (null = org base). Seeded from the flavor's COA preset.

#### `JournalEntry` (T, immutable once posted) — `core_journal_entries`
`organization` ⇒, `date`, `narration`, `source_type` / `source_id` (sale, payment, payroll,
receipt, manual), `status` (draft, posted, reversed), `posted_at`, `reversal_of` (self-FK).
`JournalLine` (`core_journal_lines`): `entry` ⇒ CASCADE, `account` ⇒, `debit`, `credit`,
`currency`, `fx_rate`, `base_debit`, `base_credit`, `dimension` (jsonb: branch, project, …).
**Invariant:** `Σ base_debit = Σ base_credit` per entry (property-tested, `H` Q8).

#### `Invoice` (T) — `core_invoices`
| field | type | notes |
|---|---|---|
| kind | enum(ar, ap) | |
| number | varchar unique per org per kind | statutory sequence, gap-flagged |
| organization ⇒, party → (Customer or Vendor) | | |
| status | enum(draft, issued, cleared, reported, paid, void) | |
| issue_date, due_date | date | |
| currency, subtotal, tax_total, total, fx_rate | | |
| **einvoice_uuid** | uuid | per e-invoicing spec |
| **einvoice_hash** / **einvoice_prev_hash** | varchar | unbroken chain (`H` C4) |
| **einvoice_qr** | text | base64 TLV |
| **einvoice_mode** | enum(sa_zatca, jo_jofotara, ae_peppol, none) | from Organization country + flavor |
| **einvoice_status** | enum(pending, cleared, reported, rejected) | |
| **einvoice_cleared_ref** | → CyVault object (cleared XML) | |
`InvoiceLine`: mirrors OrderLine; `tax_rule` ⇒, `tax_treatment` (standard, zero, exempt, reverse_charge), `reporting_box`.

#### `TaxRule` (T, or P for shipped presets) — `core_tax_rules`
`country`, `region` (null), `product_class`, `transaction_type`, `rate`, `treatment`,
`reporting_box`, `valid_from`/`to`. Flavor tax presets seed these.

#### `FxRate` (P) — `platform_fx_rates` — `base`, `quote`, `rate`, `as_of`. Referenced by base-currency conversion.

### 5.7 People

`Employee` (T, `AttributesMixin`) `core_employees` — `organization` ⇒, `person` (name, dob),
`national_id` (**encrypted**), `iqama`/`residency_no` (**encrypted**), `iban` (**encrypted**),
`gosi_number`, `contract` (jsonb: type, grade, start, end, pay elements), `bank`,
`status`. Country payroll profile inferred from `organization.country`.

`PayrollBatch` (T) `core_payroll_batches` — `organization` ⇒, `period` (year, month),
`country_profile` (JO, SA_GOSI, AE_GRATUITY, …), `status` (draft, calculated, posted, paid),
`totals` (jsonb), `wps_file_ref` → CyVault.
`Payslip` (T) `core_payslips` — `batch` ⇒ CASCADE, `employee` ⇒, `gross`, `deductions`
(jsonb), `employer_contributions` (jsonb), `net`, `wps_line` (jsonb). Invariant:
`Σ payslip.net + Σ deductions + Σ employer_contributions = batch.totals.gross` (`H` Q8).

### 5.8 Scheduling

`Resource` (T) `core_resources` — `branch` ⇒, `kind` (provider, bay, room, table, chair,
equipment), `name`, `capacity`, `calendar_rules` (jsonb), `linked_employee_id` (nullable).
`Appointment` (T, `AttributesMixin`) `core_appointments` — `branch` ⇒, `resource` ⇒,
`customer` → , `service` → Product(type=service), `start`, `end`, `status` (booked,
checked_in, in_progress, completed, no_show, cancelled), `order_id` → (billing link),
`reminders` (jsonb).

### 5.9 Customer / party

`Customer` (T, `AttributesMixin`) `core_customers` — `kind` (individual, company),
`name`, `contacts` (jsonb), `tax_id`, `segment`, `credit_limit`, `credit_terms`,
`loyalty_balance`, `default_price_list` → . Health extends via `attributes` + the Patient relation (§6).

### 5.10 Health extensions (`products/cymed`, on the canonical core — §6)

`Patient` (T) `cymed_patients` → `Customer` (1:1) + `mrn` (unique per org), `demographics`
(**encrypted** subset), `coverages` (jsonb).
`Encounter` (T) `cymed_encounters` — `patient` ⇒, `appointment` → (1:1), `provider` ⇒
Resource, `diagnoses` (jsonb, ICD-11), `procedures` (jsonb), `notes` (**encrypted**),
`status`, `billable_items` (jsonb → generates Order/Invoice lines).
`ClinicalOrder` (T) `cymed_clinical_orders` — `encounter` ⇒, `kind` (lab, imaging, rx),
`details` (jsonb), `fulfilment_ref`, `status`.
`Claim` (T) `cymed_claims` — `encounter` ⇒, `invoice` → , `payer`, `bundle` (jsonb FHIR),
`nphies_status`, `submitted_at`, `remittance` (jsonb).

---

## 6. Migration mechanics

### 6.1 M1 additive migrations (Phase 1, no data move)

On the current `platform_tenant.Tenant`:
`+ residency_region`, `+ flavor_set`, `+ encryption_key_ref`, `+ compliance_flags`.
On `BaseModel` subclasses (data migration to backfill, then non-null):
`+ created_by`, `+ updated_by`, `+ row_version`, `+ attributes` (already on some).
New tables: `core_consent_grants`, `core_domain_events` (if not present), `platform_vertical_flavors`, `platform_layout_templates`, `platform_fx_rates`.
On `Invoice`: the `einvoice_*` columns (all nullable at M1).

### 6.2 Expand/contract (ADR-0013)

Never a breaking migration + the code that needs it in one deploy. Sequence per change:
`(1)` additive migration → `(2)` deploy code tolerant of old+new → `(3)` backfill job →
`(4)` contract migration next release. RLS rollout is per-table behind `RLS_ENFORCED`.

### 6.3 CyShop → canonical (per `D.3`)

CyShop's `Product/Variant/Order/StockItem/JournalEntry` map 1:1 to the above (schema already
ported into CyCom). `attributes.legacy_id` preserves source ids. Reconciliation gates in `D.3`.

### 6.4 CyMed re-home (M4)

`cymed_*` tables keep their names; the change is: (a) `tenant_id` now set via
`TenantScopedManager` context, not scattered `tenant_id=` kwargs (the pay_bill class of bug);
(b) `cymed` `Tenant`/billing point at `platform_tenants` + `core_subscriptions`;
(c) pharmacy dispensing writes a `core_orders` row (`channel=pos`, `catalog_profile=pharmacy`);
(d) `Patient` becomes a `Customer` + extension.

---

## 7. Open items for CDAC

1. Single-tenant-per-DB vs shared-schema-with-RLS for the Enterprise tier (affects the router).
2. `attributes` GIN indexing policy — per-flavor opt-in vs automatic.
3. Whether `AuditEvent` and `DomainEvent` live in the main DB or a dedicated store from day one.
4. Numbering sequences (`Invoice.number`, `Order.number`) — DB sequence vs a `NumberSeries` table per org (statutory gap-free requirement favours the latter).
5. `row_version` vs `updated_at`-based optimistic locking — pick one, enforce in `BaseModel.save()`.
6. Health `notes` encryption granularity — whole-field vs structured-field.
