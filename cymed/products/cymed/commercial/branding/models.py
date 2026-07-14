from django.db import models

from platform.common.models import BaseModel


class Brand(BaseModel):
    """White-label brand definition per tenant/customer."""

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    customer_id = models.UUIDField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_commercial_brands"

    def __str__(self):
        return self.name


class BrandTheme(BaseModel):
    """Visual theme overrides for a brand (colors, fonts, spacing)."""

    brand = models.OneToOneField(Brand, on_delete=models.CASCADE, related_name="theme")
    primary_color = models.CharField(max_length=20, default="#0062CC")
    secondary_color = models.CharField(max_length=20, default="#6C757D")
    accent_color = models.CharField(max_length=20, default="#28A745")
    background_color = models.CharField(max_length=20, default="#FFFFFF")
    surface_color = models.CharField(max_length=20, default="#F8F9FA")
    text_primary_color = models.CharField(max_length=20, default="#212529")
    heading_font = models.CharField(max_length=100, default="Inter")
    body_font = models.CharField(max_length=100, default="Inter")
    border_radius = models.CharField(max_length=20, default="8px")
    custom_css = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_commercial_brand_themes"


class BrandAsset(BaseModel):
    """Stored branding assets (logos, icons, splash screens)."""

    ASSET_TYPES = [
        ("logo_light", "Logo (Light Background)"),
        ("logo_dark", "Logo (Dark Background)"),
        ("logo_icon", "Icon/Favicon"),
        ("splash_screen", "Splash Screen"),
        ("login_background", "Login Background"),
        ("email_header", "Email Header"),
    ]

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="assets")
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPES)
    asset_url = models.URLField(max_length=1000)
    alt_text = models.CharField(max_length=255, blank=True)
    language_code = models.CharField(max_length=10, default="en")  # "en", "ar"

    class Meta:
        db_table = "cymed_commercial_brand_assets"
        unique_together = [("brand", "asset_type", "language_code")]


class BrandDomain(BaseModel):
    """Custom domain mapping for white-label deployments."""

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="domains")
    domain = models.CharField(max_length=255, unique=True)
    is_primary = models.BooleanField(default=False)
    ssl_certificate_status = models.CharField(max_length=50, default="pending")
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_commercial_brand_domains"


class BrandLocalization(BaseModel):
    """Localized brand strings (app name, tagline, login messages)."""

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="localizations")
    language_code = models.CharField(max_length=10)  # "en", "ar"
    app_name = models.CharField(max_length=255)
    tagline = models.CharField(max_length=500, blank=True)
    login_title = models.CharField(max_length=255, blank=True)
    login_message = models.TextField(blank=True)
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=50, blank=True)
    footer_text = models.TextField(blank=True)
    is_rtl = models.BooleanField(default=False)  # Arabic = True

    class Meta:
        db_table = "cymed_commercial_brand_localizations"
        unique_together = [("brand", "language_code")]
