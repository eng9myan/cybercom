from django.db import models

from platform.common.models import BaseModel

SERVICE_CATEGORY_CHOICES = [
    ("hospital", "Hospital"),
    ("clinic", "Clinic"),
    ("laboratory", "Laboratory"),
    ("imaging", "Imaging"),
    ("pharmacy", "Pharmacy"),
    ("emergency", "Emergency"),
    ("package", "Package"),
]


class PriceList(BaseModel):
    list_name = models.CharField(max_length=200)
    list_code = models.CharField(max_length=50, unique=True)
    facility_id = models.UUIDField(null=True, blank=True)
    service_category = models.CharField(max_length=30, choices=SERVICE_CATEGORY_CHOICES)
    currency = models.CharField(max_length=3, default="SAR")
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        app_label = "cymed_rcm_pricing"
        db_table = "cymed_rcm_price_lists"
        ordering = ["-effective_date"]
        indexes = [
            models.Index(fields=["tenant_id", "service_category", "is_active"]),
            models.Index(fields=["tenant_id", "facility_id"]),
        ]

    def __str__(self):
        return f"PriceList({self.list_code} | {self.service_category})"


class ServicePrice(BaseModel):
    price_list = models.ForeignKey(
        PriceList, on_delete=models.PROTECT, related_name="service_prices"
    )
    service_code = models.CharField(max_length=50)
    service_description = models.CharField(max_length=500)
    service_category = models.CharField(max_length=30, choices=SERVICE_CATEGORY_CHOICES)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    vat_applicable = models.BooleanField(default=True)
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    price_includes_vat = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "cymed_rcm_pricing"
        db_table = "cymed_rcm_price_service_prices"
        ordering = ["service_code"]
        unique_together = [["tenant_id", "price_list", "service_code"]]
        indexes = [models.Index(fields=["tenant_id", "price_list_id", "service_code"])]

    def __str__(self):
        return f"ServicePrice({self.service_code} | {self.unit_price})"


class PackagePrice(BaseModel):
    PACKAGE_TYPE_CHOICES = [
        ("surgical", "Surgical"),
        ("maternity", "Maternity"),
        ("oncology", "Oncology"),
        ("cardiac", "Cardiac"),
        ("orthopedic", "Orthopedic"),
        ("wellness", "Wellness"),
        ("screening", "Screening"),
        ("chronic_disease", "Chronic Disease"),
        ("other", "Other"),
    ]

    price_list = models.ForeignKey(
        PriceList, on_delete=models.PROTECT, related_name="package_prices"
    )
    package_name = models.CharField(max_length=200)
    package_code = models.CharField(max_length=50)
    package_type = models.CharField(max_length=30, choices=PACKAGE_TYPE_CHOICES)
    package_description = models.TextField(blank=True)
    package_price = models.DecimalField(max_digits=12, decimal_places=2)
    services_included = models.JSONField(default=list)
    valid_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "cymed_rcm_pricing"
        db_table = "cymed_rcm_price_packages"
        ordering = ["package_name"]
        indexes = [models.Index(fields=["tenant_id", "price_list_id", "package_type"])]

    def __str__(self):
        return f"PackagePrice({self.package_code} | {self.package_price})"


class DiscountRule(BaseModel):
    DISCOUNT_TYPE_CHOICES = [
        ("percentage", "Percentage"),
        ("fixed_amount", "Fixed Amount"),
        ("waiver", "Waiver"),
    ]
    APPLIES_TO_CHOICES = [
        ("patient_type", "Patient Type"),
        ("insurance", "Insurance"),
        ("corporate", "Corporate"),
        ("staff", "Staff"),
        ("government", "Government"),
        ("senior", "Senior"),
        ("other", "Other"),
    ]

    rule_name = models.CharField(max_length=200)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    applies_to = models.CharField(max_length=30, choices=APPLIES_TO_CHOICES)
    condition_description = models.TextField(blank=True)
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    max_discount_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "cymed_rcm_pricing"
        db_table = "cymed_rcm_price_discount_rules"
        ordering = ["rule_name"]
        indexes = [models.Index(fields=["tenant_id", "discount_type", "is_active"])]

    def __str__(self):
        return f"DiscountRule({self.rule_name} | {self.discount_type} | {self.discount_value})"
