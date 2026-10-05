"""
Edition Service — resolves edition entitlements, limits, and module access.
"""

from products.cymed.commercial.editions.models import (
    EditionFeature,
    EditionLimit,
    EditionModule,
    ProductCatalogEntry,
    ProductEdition,
    TenantProductSubscription,
)


class EditionService:
    @staticmethod
    def get_edition(product_code: str, edition_code: str) -> ProductEdition | None:
        try:
            product = ProductCatalogEntry.objects.get(code=product_code, is_active=True)
            return ProductEdition.objects.get(product=product, code=edition_code, is_active=True)
        except (ProductCatalogEntry.DoesNotExist, ProductEdition.DoesNotExist):
            return None

    @staticmethod
    def get_edition_features(edition: ProductEdition) -> dict:
        """Returns {feature_code: bool} for all edition feature entitlements."""
        return {
            ef.feature_code: ef.is_enabled for ef in EditionFeature.objects.filter(edition=edition)
        }

    @staticmethod
    def get_edition_limits(edition: ProductEdition) -> dict:
        """Returns {resource_name: max_value} for all edition limits."""
        return {
            el.resource_name: el.max_value for el in EditionLimit.objects.filter(edition=edition)
        }

    @staticmethod
    def get_edition_modules(edition: ProductEdition) -> list:
        """Returns list of included module codes."""
        return [
            em.module_code for em in EditionModule.objects.filter(edition=edition, is_included=True)
        ]

    @classmethod
    def is_module_included(cls, product_code: str, edition_code: str, module_code: str) -> bool:
        edition = cls.get_edition(product_code, edition_code)
        if not edition:
            return False
        return EditionModule.objects.filter(
            edition=edition, module_code=module_code, is_included=True
        ).exists()

    @classmethod
    def is_within_bed_limit(cls, edition: ProductEdition, current_beds: int) -> bool:
        if edition.max_beds == 0:
            return True
        return current_beds <= edition.max_beds

    @classmethod
    def is_within_user_limit(cls, edition: ProductEdition, current_users: int) -> bool:
        if edition.max_users == 0:
            return True
        return current_users <= edition.max_users

    @classmethod
    def provision_edition(cls, product_code: str, edition_code: str) -> ProductEdition | None:
        """Ensure product and edition exist in catalog; return the edition."""
        return cls.get_edition(product_code, edition_code)

    @staticmethod
    def tenant_has_product(tenant_id, product_code: str) -> bool:
        """
        Entitlement check for ProductEntitlementMiddleware. A tenant with NO
        subscription rows AT ALL (active or not) is legacy/unconfigured and
        always passes — gating only activates once a tenant has been given
        at least one subscription row, so existing tenants aren't locked out
        the moment this ships. A tenant with rows but none active/matching
        (e.g. churned) is correctly blocked, not treated as legacy.
        """
        all_subs = TenantProductSubscription.objects.filter(tenant_id=tenant_id)
        if not all_subs.exists():
            return True
        return all_subs.filter(product__code=product_code, is_active=True).exists()

    @staticmethod
    def tenant_entitled_products(tenant_id) -> list[str]:
        """Product codes this tenant is actively subscribed to (for a nav/UI to consume)."""
        return list(
            TenantProductSubscription.objects.filter(tenant_id=tenant_id, is_active=True)
            .values_list("product__code", flat=True)
        )
