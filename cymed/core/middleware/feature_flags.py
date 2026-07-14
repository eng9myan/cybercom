"""
Feature-flag middleware: attaches enabled feature codes to request.enabled_features
so any view can call request.feature_enabled("FLAG_CODE") without extra DB hits.
"""

from django.core.cache import cache


class FeatureFlagMiddleware:
    CACHE_TTL = 60  # seconds — short enough to pick up flag changes quickly

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        if tenant_id:
            request.enabled_features = self._load_features(tenant_id)
        else:
            request.enabled_features = set()
        request.feature_enabled = lambda code: code in request.enabled_features
        return self.get_response(request)

    def _load_features(self, tenant_id):
        cache_key = f"features:{tenant_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            from products.cymed.commercial.feature_flags.models import FeatureFlag, TenantFeature

            # Start with globally-default-enabled flags
            enabled = set(
                FeatureFlag.objects.filter(default_enabled=True).values_list("code", flat=True)
            )
            # Apply tenant overrides
            overrides = (
                TenantFeature.objects.filter(tenant_id=tenant_id)
                .select_related("feature")
                .values_list("feature__code", "is_enabled")
            )
            for code, is_on in overrides:
                if is_on:
                    enabled.add(code)
                else:
                    enabled.discard(code)
            cache.set(cache_key, enabled, self.CACHE_TTL)
            return enabled
        except Exception:
            return set()
