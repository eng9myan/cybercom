"""
White-label branding middleware: attaches brand config to request.brand
based on the request domain or X-Brand-Code header.
"""
from django.core.cache import cache


class BrandingMiddleware:
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.brand = self._resolve_brand(request)
        return self.get_response(request)

    def _resolve_brand(self, request):
        # Allow explicit override via header (used by white-label tenants)
        brand_code = request.headers.get("X-Brand-Code")
        if not brand_code:
            host = request.get_host().split(":")[0]
            cache_key = f"brand_domain:{host}"
            brand_code = cache.get(cache_key)
            if brand_code is None:
                brand_code = self._lookup_domain(host)
                cache.set(cache_key, brand_code or "", self.CACHE_TTL)
        if not brand_code:
            return None
        return self._load_brand(brand_code)

    def _lookup_domain(self, host):
        try:
            from products.cymed.commercial.branding.models import BrandDomain
            domain_obj = BrandDomain.objects.select_related("brand").filter(domain=host).first()
            return domain_obj.brand.code if domain_obj else None
        except Exception:
            return None

    def _load_brand(self, code):
        cache_key = f"brand:{code}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            from products.cymed.commercial.branding.models import Brand
            brand = (
                Brand.objects.select_related("theme")
                .prefetch_related("localizations", "assets")
                .filter(code=code, is_active=True)
                .first()
            )
            if brand:
                cache.set(cache_key, brand, self.CACHE_TTL)
            return brand
        except Exception:
            return None
