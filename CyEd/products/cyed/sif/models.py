from django.db import models

from platform.common.models import BaseModel


class SifRefId(BaseModel):
    """
    The RefId registry: ``(tenant_id, object_type, local_id) -> refid``.

    SIF requires every object instance to carry a 128-bit RefId that is minted
    once and never changes, because consumers key their own records off it. A
    RefId that changes is worse than no RefId — the consumer sees a delete and
    a create, and any history attached to the old identifier is orphaned.

    Kept as a side table rather than a column on every domain model. The
    reasoning is in the package docstring; the short version is that SIF
    objects are not 1:1 with tables (``StudentSchoolEnrollment`` and
    ``StudentAttendance`` are derived views over several), so several of them
    have no single row to hang a column on.
    """

    object_type = models.CharField(
        max_length=60, help_text="SIF object name, e.g. StudentPersonal."
    )
    # The CyEd-side identity. A real primary key for direct objects; a
    # deterministic UUIDv5 for derived ones (see refids.synthetic_local_id).
    local_id = models.CharField(max_length=64)
    refid = models.UUIDField()
    # The CyEd row this object was derived from. For direct objects it equals
    # `local_id`; for derived ones (StudentAttendance, StudentSchoolEnrollment)
    # `local_id` is a hash, and without this a RefId lookup would have to scan
    # every candidate row re-deriving hashes until one matched.
    source_local_id = models.CharField(max_length=64, blank=True)
    # Kept for support: when a consumer asks "what is this RefId?", the answer
    # should not require reconstructing the derivation.
    source_description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_sif_refids"
        ordering = ["object_type", "local_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "object_type", "local_id"],
                name="uniq_sif_refid_per_object",
            ),
            # A RefId identifies exactly one object. Reusing one across two
            # objects would make a consumer's records collide.
            models.UniqueConstraint(
                fields=["tenant_id", "refid"], name="uniq_sif_refid_value"
            ),
        ]
        indexes = [
            models.Index(fields=["tenant_id", "refid"], name="idx_sif_refid_lookup"),
        ]

    def __str__(self):
        return f"{self.object_type}/{self.local_id} → {self.refid}"
