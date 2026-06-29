"""
Branding Service — resolves active brand for a tenant/domain.
"""

from products.cymed.commercial.branding.models import Brand, BrandLocalization, BrandTheme


class BrandingService:
    @staticmethod
    def get_brand_for_domain(domain: str) -> Brand | None:
        from products.cymed.commercial.branding.models import BrandDomain

        bd = BrandDomain.objects.filter(domain=domain).select_related("brand").first()
        return bd.brand if bd else None

    @staticmethod
    def get_brand_theme(brand: Brand) -> dict | None:
        try:
            theme = brand.theme
            return {
                "primary_color": theme.primary_color,
                "secondary_color": theme.secondary_color,
                "accent_color": theme.accent_color,
                "background_color": theme.background_color,
                "surface_color": theme.surface_color,
                "text_primary_color": theme.text_primary_color,
                "heading_font": theme.heading_font,
                "body_font": theme.body_font,
                "border_radius": theme.border_radius,
                "custom_css": theme.custom_css,
            }
        except BrandTheme.DoesNotExist:
            return None

    @staticmethod
    def get_localization(brand: Brand, language_code: str = "en") -> dict | None:
        loc = BrandLocalization.objects.filter(brand=brand, language_code=language_code).first()
        if not loc:
            return None
        return {
            "app_name": loc.app_name,
            "tagline": loc.tagline,
            "login_title": loc.login_title,
            "login_message": loc.login_message,
            "support_email": loc.support_email,
            "support_phone": loc.support_phone,
            "footer_text": loc.footer_text,
            "is_rtl": loc.is_rtl,
        }

    @classmethod
    def get_full_brand_config(cls, brand: Brand, language_code: str = "en") -> dict:
        return {
            "brand_code": brand.code,
            "brand_name": brand.name,
            "theme": cls.get_brand_theme(brand),
            "localization": cls.get_localization(brand, language_code),
            "assets": {
                a.asset_type: {"url": a.asset_url, "alt": a.alt_text}
                for a in brand.assets.filter(language_code=language_code)
            },
        }
