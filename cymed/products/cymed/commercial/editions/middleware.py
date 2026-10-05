"""
Runtime entitlement gating — Phase 1 of "standalone products" (each of
Hospital / Clinic / Pharmacy / Laboratory / Imaging must be sellable on its
own). Enforces at the product boundary: a tenant subscribed only to
cymed_pharmacy cannot reach /api/v1/hospital/, /api/v1/clinic/, /api/v1/lab/
or /api/v1/imaging/, and vice versa. The finer-grained EditionModule lists
(e.g. "pharmacy.clinical" vs "pharmacy.dispensing") remain catalog-only for
now — a later tier-feature pass, not this gate.

Deliberately NOT gated: products.cymed.core.* (patients/encounters/clinical/
etc — the shared clinical foundation every product needs), patient_portal,
provider_portal, payments, rcm, fhir, ai_cds, integrations, ecosystem, mrff,
commercial itself. Those are cross-cutting, not single-product.
"""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse

from products.cymed.commercial.editions.services import EditionService

_GATED_PREFIXES: tuple[tuple[str, str], ...] = (
    ("/api/v1/clinic/", "cymed_clinic"),
    ("/api/v1/hospital/", "cymed_hospital"),
    ("/api/v1/lab/", "cymed_laboratory"),
    ("/api/v1/imaging/", "cymed_imaging"),
    ("/api/v1/pharmacy/", "cymed_pharmacy"),
)


def _product_for_path(path: str) -> str | None:
    for prefix, product_code in _GATED_PREFIXES:
        if path.startswith(prefix):
            return product_code
    return None


class ProductEntitlementMiddleware:
    """Must run after TenantContextMiddleware (needs request.tenant_id)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        product_code = _product_for_path(request.path)
        tenant_id = getattr(request, "tenant_id", None)

        if product_code and tenant_id is not None:
            if not EditionService.tenant_has_product(tenant_id, product_code):
                return JsonResponse(
                    {
                        "type": "https://cybercom.io/errors/product_not_entitled",
                        "title": "Forbidden",
                        "status": 403,
                        "detail": (
                            f"This tenant is not subscribed to the "
                            f"'{product_code}' product."
                        ),
                        "instance": request.path,
                        "code": "product_not_entitled",
                    },
                    status=403,
                    content_type="application/problem+json",
                )

        return self.get_response(request)
