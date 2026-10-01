"""Read-side helpers over the local merchant catalog — used by the
agent's search_catalog tool so a search result carries everything
add_to_cart needs (store_id, tenant_id, unit_price), not just a name."""

from __future__ import annotations

from .models import Merchant, MerchantKind, Product


class CatalogSearch:
    def search(self, query: str, kind: str | None = None, limit: int = 8) -> list[dict]:
        q = (query or "").strip().lower()
        products = Product.objects.filter(is_active=True).select_related("merchant")
        if kind:
            products = products.filter(merchant__kind=kind)
        if q:
            products = [
                p for p in products
                if q in p.name.lower() or q in p.merchant.name.lower() or q in (p.category or "").lower()
            ]
        else:
            products = list(products)
        return [
            {
                "product_id": p.id,
                "name": p.name,
                "price": p.price,
                "unit": p.unit,
                "merchant_id": p.merchant_id,
                "merchant_name": p.merchant.name,
                "merchant_kind": p.merchant.kind,
                "store_id": p.merchant_id,
                "tenant_id": p.merchant.tenant_id,
            }
            for p in products[:limit]
        ]

    def nearby_merchants(self, kind: str | None = None) -> list[Merchant]:
        qs = Merchant.objects.filter(is_active=True)
        if kind:
            qs = qs.filter(kind=kind)
        return list(qs)
