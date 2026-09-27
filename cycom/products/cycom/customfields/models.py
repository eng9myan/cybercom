from django.db import models

from platform.common.models import BaseModel


class CustomFieldDefinition(BaseModel):
    """
    A tenant-declared extension field on one of the models in
    `customfields.registry.CUSTOMFIELD_MODELS`. Values are never stored here
    -- they live directly on the target record's own `attributes` JSONField
    (see registry.py), keyed by `field_key`. This row is only the schema:
    what the field is called, what type it is, and whether it's still active.
    """

    FIELD_TYPES = [
        ("text", "Text"),
        ("number", "Number"),
        ("date", "Date"),
        ("boolean", "Yes / No"),
        ("select", "Dropdown"),
    ]

    model_key = models.CharField(max_length=50, db_index=True)
    field_key = models.SlugField(max_length=50)
    label = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default="text")
    # Only meaningful (and required, enforced in the serializer) for "select".
    options = models.JSONField(default=list, blank=True)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "cycom_customfield_definitions"
        ordering = ["sort_order", "label"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "model_key", "field_key"],
                name="unique_customfield_key_per_model_per_tenant",
            )
        ]
        indexes = [models.Index(fields=["tenant_id", "model_key", "is_active"])]

    def __str__(self):
        return f"{self.model_key}.{self.field_key}"
