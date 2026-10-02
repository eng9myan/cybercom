"""Diet Shield — licensed partners (the paying customers of this
product: delivery platforms like Talabat, HungerStation, etc). A Partner
authenticates via API key, never a consumer login — there is no concept
of an end-customer account anywhere in this product; a partner sends its
own user/item data inline on every call (see engine.py)."""

import hashlib
import secrets
import uuid

from django.db import models


class Partner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    # Only the hash is stored — the raw key is shown once, at creation.
    api_key_hash = models.CharField(max_length=64, unique=True, db_index=True)
    key_prefix = models.CharField(max_length=16, help_text="First chars of the key, for display/audit.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_partner"

    def __str__(self):
        return self.name

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def create_with_key(cls, name: str) -> tuple["Partner", str]:
        """Returns (partner, raw_key) — the raw key is never persisted
        or retrievable again after this call returns."""
        raw_key = f"ds_live_{secrets.token_urlsafe(32)}"
        partner = cls.objects.create(
            name=name, api_key_hash=cls.hash_key(raw_key), key_prefix=raw_key[:12],
        )
        return partner, raw_key


class PartnerCallLog(models.Model):
    """Minimal usage metering — one row per evaluate call, enough to
    report monthly volume or bill per-call."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="calls")
    item_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_partner_call_log"
        indexes = [models.Index(fields=["partner", "created_at"])]
