"""
Cycom Ready-ERP — provisioning catalog + blueprints.

Design (per the "one core + reusable department packs + industry templates +
country localization packs" model):

  * Catalog models (CountryPack / DepartmentPack / IndustryTemplate) are
    GLOBAL reference data — `PlatformModel`, not tenant-scoped. They are the
    versioned, shareable building blocks, seeded from JSON under
    `platform/provisioning/packs/` via `manage.py seed_packs`.
  * CompanyBlueprint + the generated approval models are TENANT-scoped
    (`BaseModel`) — they belong to one customer's provisioned ERP.

Templates are DATA, not code: adding an industry = adding a JSON pack + rows,
never a new codebase. Versioning fields let a template evolve (1.0 -> 1.1 ->
2.0) without destroying a customer's provisioned config.
"""

from django.db import models

from platform.common.models import BaseModel, PlatformModel


# ---------------------------------------------------------------------------
# CATALOG (global, versioned building blocks)
# ---------------------------------------------------------------------------


class CountryPack(PlatformModel):
    """Localization pack: currency, tax, payroll, CoA seed, e-invoicing."""

    code = models.CharField(max_length=2, unique=True)  # ISO-3166 alpha-2, e.g. "JO"
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=10, default="JOD")
    languages = models.JSONField(default=list)          # ["ar", "en"]
    default_locale = models.CharField(max_length=10, default="en")
    fiscal_year_start_month = models.PositiveSmallIntegerField(default=1)
    tax_config = models.JSONField(default=dict)          # VAT/sales-tax rules
    payroll_config = models.JSONField(default=dict)      # social security, brackets
    coa_template = models.JSONField(default=list)        # [{code,name,account_type,parent}]
    einvoicing = models.JSONField(default=dict)          # {system: "jofotara", ...}
    public_holidays = models.JSONField(default=list)
    version = models.CharField(max_length=20, default="1.0")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "provisioning_country_packs"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name} v{self.version}"


class DepartmentPack(PlatformModel):
    """A reusable department: its modules, roles, workflows, KPIs, dashboards."""

    key = models.CharField(max_length=50, unique=True)   # "finance", "hr", ...
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    modules = models.JSONField(default=list)             # backend module keys enabled
    roles = models.JSONField(default=list)               # [{name, description}]
    permissions = models.JSONField(default=dict)         # role -> [perm]
    menus = models.JSONField(default=list)
    workflows = models.JSONField(default=list)
    kpis = models.JSONField(default=list)
    dashboards = models.JSONField(default=list)
    reports = models.JSONField(default=list)
    version = models.CharField(max_length=20, default="1.0")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "provisioning_department_packs"
        ordering = ["key"]

    def __str__(self):
        return f"{self.key} v{self.version}"


class IndustryTemplate(PlatformModel):
    """A ready company: which department packs + industry-specific config."""

    key = models.CharField(max_length=50)                # "construction", "trading"
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    department_pack_keys = models.JSONField(default=list)  # ["finance","procurement",...]
    terminology = models.JSONField(default=dict)         # label overrides
    default_config = models.JSONField(default=dict)
    approval_matrix = models.JSONField(default=list)     # [{document_type,tiers:[...]}]
    categories = models.JSONField(default=list)          # product/service categories
    accounting_mappings = models.JSONField(default=dict)
    dashboards = models.JSONField(default=list)
    reports = models.JSONField(default=list)
    doc_templates = models.JSONField(default=list)
    import_templates = models.JSONField(default=list)    # [{entity, columns:[...]}]
    industry_fields = models.JSONField(default=dict)     # model -> [extra fields]
    ai_knowledge = models.JSONField(default=dict)        # prompts + domain notes
    recommended_ops = models.JSONField(default=list)     # matches Step-5 answers
    version = models.CharField(max_length=20, default="1.0")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "provisioning_industry_templates"
        unique_together = [("key", "version")]
        ordering = ["key", "-version"]

    def __str__(self):
        return f"{self.key} v{self.version}"


# ---------------------------------------------------------------------------
# BLUEPRINT (tenant-scoped: one customer's answers + provisioning result)
# ---------------------------------------------------------------------------


class SetupLevel(models.TextChoices):
    EXPRESS = "express", "Express"
    PROFESSIONAL = "professional", "Professional"
    ENTERPRISE = "enterprise", "Enterprise"


class CompanySize(models.TextChoices):
    MICRO = "micro", "Micro"
    SMALL = "small", "Small"
    MEDIUM = "medium", "Medium"
    LARGE = "large", "Large"
    ENTERPRISE = "enterprise", "Enterprise Group"


class BlueprintStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PROVISIONING = "provisioning", "Provisioning"
    PROVISIONED = "provisioned", "Provisioned"
    FAILED = "failed", "Failed"


class CompanyBlueprint(BaseModel):
    """The wizard answers for one tenant + a summary of what got generated."""

    company_name = models.CharField(max_length=200)
    country_code = models.CharField(max_length=2, default="JO")
    industry_key = models.CharField(max_length=50)
    size = models.CharField(max_length=20, choices=CompanySize.choices, default=CompanySize.SMALL)
    setup_level = models.CharField(
        max_length=20, choices=SetupLevel.choices, default=SetupLevel.EXPRESS
    )
    business_ops = models.JSONField(default=list)        # Step-5 selections
    selected_department_packs = models.JSONField(default=list)

    companies = models.PositiveIntegerField(default=1)
    branches = models.PositiveIntegerField(default=1)
    warehouses = models.PositiveIntegerField(default=1)
    factories = models.PositiveIntegerField(default=0)
    projects = models.PositiveIntegerField(default=0)
    departments = models.JSONField(default=list)
    cost_centers = models.JSONField(default=list)

    template_version_used = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=20, choices=BlueprintStatus.choices, default=BlueprintStatus.DRAFT
    )
    summary = models.JSONField(default=dict)             # what was created, for Review
    provisioned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "provisioning_company_blueprints"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company_name} [{self.industry_key}/{self.status}]"


# ---------------------------------------------------------------------------
# GENERATED APPROVAL ENGINE (tenant-scoped) — no approval model existed before
# ---------------------------------------------------------------------------


class ApprovalPolicy(BaseModel):
    """Value-based approval chain for one document type (e.g. purchase_request)."""

    document_type = models.CharField(max_length=50)      # purchase_request, payment, ...
    name = models.CharField(max_length=150)
    currency = models.CharField(max_length=10, default="JOD")
    is_active = models.BooleanField(default=True)
    generated_by_blueprint = models.ForeignKey(
        CompanyBlueprint, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approval_policies",
    )

    class Meta:
        db_table = "provisioning_approval_policies"
        unique_together = [("tenant_id", "document_type")]
        ordering = ["document_type"]

    def __str__(self):
        return f"{self.document_type} ({self.name})"


class TenantConfigParameter(BaseModel):
    """
    Tenant-scoped key/value config — the real backing for the legacy UI's
    `ir.config_parameter` set_param/get_param calls (setup wizards persist
    choices like `cycom.tenant.*` here for later wizards to read).
    """

    key = models.CharField(max_length=200)
    value = models.TextField(blank=True)

    class Meta:
        db_table = "provisioning_config_parameters"
        unique_together = [("tenant_id", "key")]
        ordering = ["key"]

    def __str__(self):
        return f"{self.key}={self.value[:40]}"


class ApprovalTier(BaseModel):
    """One amount band -> approver role, within an ApprovalPolicy."""

    policy = models.ForeignKey(ApprovalPolicy, on_delete=models.CASCADE, related_name="tiers")
    sequence = models.PositiveSmallIntegerField(default=1)
    threshold_min = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    threshold_max = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    approver_role = models.CharField(max_length=150)

    class Meta:
        db_table = "provisioning_approval_tiers"
        ordering = ["policy", "sequence"]

    def __str__(self):
        cap = self.threshold_max if self.threshold_max is not None else "∞"
        return f"{self.approver_role} [{self.threshold_min}-{cap}]"
