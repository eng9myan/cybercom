"""
School-Home Learning Bridge (docs/cyed/AUDIT_PROCUREMENT_AND_ST4S_2026-08-11.md
Tier 3 item #17).

Deliberately not a separate system: "learning targets and progress" are
derived directly from existing curriculum/gradebook/assessment data (see
services.py), not duplicated into a new goals model here. The two models in
this file are the genuinely new content types the feature needs — teacher-
curated family resources and offline activity packs — that had no home
anywhere else in the product.
"""
from django.db import models

from platform.common.models import BaseModel


class FamilyResource(BaseModel):
    """
    A culturally responsive micro-lesson or family resource, curated by
    staff and shown to families whose child's year level (and, when set,
    home language) matches.
    """

    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    # Markdown/plain text body — an in-app resource does not need a file.
    body = models.TextField(blank=True)
    # An external link is also valid (e.g. a video or a community org's page).
    external_url = models.URLField(blank=True)
    year_level_min = models.SmallIntegerField(default=0)
    year_level_max = models.SmallIntegerField(default=12)
    # Blank = suitable for any family. Set to prioritise a resource for
    # families whose Student.language_at_home matches (see services.py) —
    # never used to EXCLUDE a family, only to rank relevance.
    language = models.CharField(max_length=100, blank=True)
    is_published = models.BooleanField(default=False)
    created_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_learning_bridge_family_resources"
        ordering = ["title"]

    def __str__(self):
        return self.title


class OfflineActivityPack(BaseModel):
    """
    A teacher-approved, text-based activity pack a family can use without a
    live connection — the content itself (not a link, not a large binary)
    lives in `content`, because a low-connectivity household is exactly the
    audience this must not depend on a reliable download to reach once
    they've fetched this one small payload.
    """

    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    year_level_min = models.SmallIntegerField(default=0)
    year_level_max = models.SmallIntegerField(default=12)
    approved_by = models.CharField(max_length=255, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_learning_bridge_offline_packs"
        ordering = ["title"]

    def __str__(self):
        return self.title
