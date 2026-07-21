"""
CyID ecosystem, Phase 6 — multi-country billing core. Platform-wide
reference catalogs (currency codes, tax jurisdictions), not tenant-scoped
— every tenant reads the same catalog, so these extend PlatformModel
(no tenant_id) rather than BaseModel, same as platform.tenant.IdentityRealm.

Deliberately does NOT change Invoice.currency (still a free CharField) or
add a new field to Invoice/InvoiceLine — a tenant's jurisdiction is
derived from its own platform.tenant.Tenant.country_code (already a real,
existing field) rather than duplicating country data onto every invoice.
This also sidesteps a much larger, disproportionate blast radius: Invoice.currency
feeds directly into accounting.services.post_journal_entry(), which every
other Cycom subsystem's GL posting also calls — converting it to a hard FK
would ripple into JournalEntry/JournalLine's own currency handling too.
"""

from django.db import models

from platform.common.models import PlatformModel


class Currency(PlatformModel):
    code = models.CharField(max_length=3, unique=True)  # ISO 4217
    name = models.CharField(max_length=100)
    decimal_places = models.PositiveSmallIntegerField(default=2)

    class Meta:
        db_table = "cycom_localization_currencies"
        ordering = ["code"]
        verbose_name_plural = "currencies"

    def __str__(self):
        return self.code


class Jurisdiction(PlatformModel):
    """One row per country this billing core knows how to invoice for.
    `compliance_region` is the exact key compliance-gateway/main.py's
    process_fiscal_compliance() switches on (JO/SA/US/EU/GB)."""

    country_code = models.CharField(max_length=2, unique=True)  # ISO 3166-1 alpha-2
    name = models.CharField(max_length=100)
    default_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="jurisdictions")
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    compliance_region = models.CharField(max_length=10)

    class Meta:
        db_table = "cycom_localization_jurisdictions"
        ordering = ["country_code"]

    def __str__(self):
        return f"{self.country_code} ({self.compliance_region})"
