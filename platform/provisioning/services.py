"""
ProvisioningService — turns a CompanyBlueprint into a configured ERP.

Composes: CountryPack (localization + CoA seed) + IndustryTemplate (which
department packs + approval matrix + industry config) + the selected
DepartmentPacks (roles/modules/dashboards). Generates REAL rows in the
existing product models (accounting.Account, access.Role) plus the new
approval tables, then records a summary the Review screen reads back.

Idempotent: every generator uses get_or_create keyed on (tenant_id, natural
key), so re-running "Create My Company" never duplicates. Runs in one
transaction — a partial failure rolls the whole provisioning back.
"""

from __future__ import annotations

from decimal import Decimal

from django.apps import apps
from django.db import transaction
from django.utils import timezone

from platform.provisioning.models import (
    ApprovalPolicy,
    ApprovalTier,
    BlueprintStatus,
    CompanyBlueprint,
    CountryPack,
    DepartmentPack,
    IndustryTemplate,
)


class ProvisioningError(Exception):
    pass


# Size scales the value-based approval thresholds: a micro shop and an
# enterprise group should not share the same 5,000-JOD ceiling.
SIZE_THRESHOLD_MULTIPLIER = {
    "micro": Decimal("0.25"),
    "small": Decimal("0.5"),
    "medium": Decimal("1.0"),
    "large": Decimal("3.0"),
    "enterprise": Decimal("10.0"),
}


class ProvisioningService:
    def __init__(self, blueprint: CompanyBlueprint):
        self.blueprint = blueprint
        self.tenant_id = blueprint.tenant_id

    # -- catalog resolution --------------------------------------------------

    def _country(self) -> CountryPack:
        try:
            return CountryPack.objects.get(code=self.blueprint.country_code, is_active=True)
        except CountryPack.DoesNotExist:
            raise ProvisioningError(f"No active CountryPack for '{self.blueprint.country_code}'.")

    def _industry(self) -> IndustryTemplate:
        qs = IndustryTemplate.objects.filter(key=self.blueprint.industry_key, is_active=True)
        template = qs.order_by("-version").first()
        if not template:
            raise ProvisioningError(f"No active IndustryTemplate for '{self.blueprint.industry_key}'.")
        return template

    def _department_packs(self, industry: IndustryTemplate) -> list[DepartmentPack]:
        keys = list(dict.fromkeys(  # de-dup, preserve order
            list(industry.department_pack_keys) + list(self.blueprint.selected_department_packs)
        ))
        packs = list(DepartmentPack.objects.filter(key__in=keys, is_active=True))
        found = {p.key for p in packs}
        missing = [k for k in keys if k not in found]
        if missing:
            raise ProvisioningError(f"Missing DepartmentPacks: {missing}")
        # keep the requested order
        by_key = {p.key: p for p in packs}
        return [by_key[k] for k in keys if k in by_key]

    # -- generators ----------------------------------------------------------

    def _generate_coa(self, country: CountryPack, industry: IndustryTemplate) -> int:
        Account = apps.get_model("cycom_accounting", "Account")
        # Country CoA first (parents before children — template is ordered so
        # a parent code always precedes its children).
        rows = list(country.coa_template)
        # Industry may add its own accounts (e.g. construction WIP, retention).
        rows += list(industry.accounting_mappings.get("extra_accounts", []))

        code_to_obj: dict[str, object] = {}
        created = 0
        for row in rows:
            parent_obj = code_to_obj.get(row.get("parent")) if row.get("parent") else None
            obj, was_created = Account.objects.get_or_create(
                tenant_id=self.tenant_id,
                code=row["code"],
                defaults={
                    "name": row["name"],
                    "account_type": row["account_type"],
                    "parent": parent_obj,
                    "currency": country.currency,
                },
            )
            code_to_obj[row["code"]] = obj
            created += int(was_created)
        return created

    def _generate_roles(self, packs: list[DepartmentPack], industry: IndustryTemplate) -> list[str]:
        Role = apps.get_model("cycom_access", "Role")
        role_defs: dict[str, str] = {}
        for pack in packs:
            for r in pack.roles:
                role_defs.setdefault(r["name"], r.get("description", ""))
        for r in industry.default_config.get("roles", []):
            role_defs.setdefault(r["name"], r.get("description", ""))

        created = []
        for name, description in role_defs.items():
            _, was_created = Role.objects.get_or_create(
                tenant_id=self.tenant_id,
                name=name,
                defaults={"description": description},
            )
            if was_created:
                created.append(name)
        return sorted(role_defs.keys()), created

    def _generate_approvals(self, industry: IndustryTemplate, currency: str) -> list[str]:
        mult = SIZE_THRESHOLD_MULTIPLIER.get(self.blueprint.size, Decimal("1.0"))
        policies = []
        for spec in industry.approval_matrix:
            policy, _ = ApprovalPolicy.objects.update_or_create(
                tenant_id=self.tenant_id,
                document_type=spec["document_type"],
                defaults={
                    "name": spec.get("name", spec["document_type"].replace("_", " ").title()),
                    "currency": currency,
                    "generated_by_blueprint": self.blueprint,
                    "is_active": True,
                },
            )
            # Rebuild tiers deterministically.
            policy.tiers.all().delete()
            for i, tier in enumerate(spec["tiers"], start=1):
                tmin = Decimal(str(tier.get("min", 0))) * mult
                tmax = tier.get("max")
                tmax = (Decimal(str(tmax)) * mult) if tmax is not None else None
                ApprovalTier.objects.create(
                    tenant_id=self.tenant_id,
                    policy=policy,
                    sequence=i,
                    threshold_min=tmin,
                    threshold_max=tmax,
                    approver_role=tier["role"],
                )
            policies.append(policy.document_type)
        return policies

    # -- orchestration -------------------------------------------------------

    @transaction.atomic
    def build(self) -> CompanyBlueprint:
        bp = self.blueprint
        bp.status = BlueprintStatus.PROVISIONING
        bp.save(update_fields=["status", "updated_at"])

        country = self._country()
        industry = self._industry()
        packs = self._department_packs(industry)

        accounts_created = self._generate_coa(country, industry)
        all_roles, roles_created = self._generate_roles(packs, industry)
        approval_docs = self._generate_approvals(industry, country.currency)

        enabled_modules = sorted({m for p in packs for m in p.modules})
        dashboards = [d for p in packs for d in p.dashboards] + list(industry.dashboards)
        reports = [r for p in packs for r in p.reports] + list(industry.reports)

        bp.template_version_used = industry.version
        bp.status = BlueprintStatus.PROVISIONED
        bp.provisioned_at = timezone.now()
        bp.summary = {
            "localization": {
                "country": country.code,
                "currency": country.currency,
                "languages": country.languages,
                "einvoicing": country.einvoicing,
                "fiscal_year_start_month": country.fiscal_year_start_month,
            },
            "enabled_modules": enabled_modules,
            "department_packs": [p.key for p in packs],
            "roles": all_roles,
            "roles_created": roles_created,
            "accounts_created": accounts_created,
            "approval_policies": approval_docs,
            "dashboards": dashboards,
            "reports": reports,
            "import_templates": industry.import_templates,
            "industry_fields": industry.industry_fields,
            "terminology": industry.terminology,
            "ai_knowledge": industry.ai_knowledge,
            "structure": {
                "companies": bp.companies,
                "branches": bp.branches,
                "warehouses": bp.warehouses,
                "factories": bp.factories,
                "projects": bp.projects,
                "departments": bp.departments,
                "cost_centers": bp.cost_centers,
            },
        }
        bp.save()
        return bp
