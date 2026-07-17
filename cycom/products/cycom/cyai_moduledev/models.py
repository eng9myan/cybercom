from django.db import models

from platform.common.models import BaseModel


class ModuleDevRequest(BaseModel):
    """
    One full journey through the safe module-development workflow:
    study existing functionality -> requirements draft -> user confirms ->
    technical design -> admin approves design -> code generated in isolated
    workspace -> lint/build/test -> diff presented -> staging deploy -> UAT
    -> production approval -> deploy -> rollback package. Every step here is
    a real, separately-recorded state transition — nothing skips a gate.
    """

    STATUS_CHOICES = [
        ("studying", "Studying Existing Functionality"),
        ("requirements_gathering", "Gathering Requirements"),
        ("requirements_confirmed", "Requirements Confirmed"),
        ("technical_design", "Technical Design Drafted"),
        ("design_approved", "Design Approved"),
        ("generating", "Generating Code"),
        ("code_generated", "Code Generated — Isolated Workspace"),
        ("testing", "Running Lint/Build/Tests"),
        ("diff_ready", "Diff Ready For Review"),
        ("staging_deployed", "Deployed To Staging"),
        ("uat", "User Acceptance Testing"),
        ("production_approved", "Production Deployment Approved"),
        ("deployed", "Deployed To Production"),
        ("rejected", "Rejected"),
        ("rolled_back", "Rolled Back"),
    ]

    product_description = models.TextField()
    requested_by = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="studying")

    discovery_results = models.JSONField(default=list, blank=True)
    messages = models.JSONField(default=list, blank=True)  # requirements-gathering conversation

    functional_spec = models.TextField(blank=True)
    functional_spec_confirmed_by = models.CharField(max_length=255, blank=True)
    functional_spec_confirmed_at = models.DateTimeField(null=True, blank=True)

    technical_design = models.TextField(blank=True)
    technical_design_approved_by = models.CharField(max_length=255, blank=True)
    technical_design_approved_at = models.DateTimeField(null=True, blank=True)

    module_name = models.CharField(max_length=100, blank=True)
    workspace_path = models.CharField(max_length=500, blank=True)
    generated_files = models.JSONField(default=list, blank=True)  # [{path, content}]

    lint_results = models.JSONField(null=True, blank=True)
    build_results = models.JSONField(null=True, blank=True)
    test_results = models.JSONField(null=True, blank=True)
    diff_text = models.TextField(blank=True)

    staging_deployed_at = models.DateTimeField(null=True, blank=True)

    production_approved_by = models.CharField(max_length=255, blank=True)
    production_approved_at = models.DateTimeField(null=True, blank=True)
    deployed_at = models.DateTimeField(null=True, blank=True)
    deploy_commit_sha = models.CharField(max_length=100, blank=True)

    rollback_manifest = models.JSONField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_cyai_moduledev_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.module_name or self.product_description[:40]} ({self.status})"
