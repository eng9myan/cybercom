from django.db import models
from platform.common.models import BaseModel


DEMO_TYPE_CHOICES = [
    ("full_platform", "Full Platform Demo"),
    ("cymed_hospital", "CyMed Hospital Edition"),
    ("cymed_clinic", "CyMed Clinic Edition"),
    ("cymed_lab", "CyMed Laboratory Edition"),
    ("cymed_imaging", "CyMed Imaging Edition"),
    ("cymed_pharmacy", "CyMed Pharmacy Edition"),
    ("cymed_patient_portal", "CyMed Patient Portal"),
    ("cymed_provider_portal", "CyMed Provider Portal"),
    ("rcm", "Revenue Cycle Management"),
    ("population_health", "Population Health"),
    ("workforce", "Workforce Management"),
    ("cycom_erp", "CyCom ERP"),
    ("cygov", "CyGov Government Platform"),
    ("cycitizen", "CyCitizen Services"),
    ("cyai", "CyAI Platform"),
]

DEMO_STATUS_CHOICES = [
    ("provisioning", "Provisioning"),
    ("active", "Active"),
    ("paused", "Paused"),
    ("resetting", "Resetting"),
    ("expired", "Expired"),
    ("archived", "Archived"),
]

SCENARIO_TYPE_CHOICES = [
    ("patient_admission", "Patient Admission Flow"),
    ("emergency_triage", "Emergency Department Triage"),
    ("surgical_workflow", "Surgical Workflow"),
    ("lab_order_result", "Lab Order to Result"),
    ("imaging_workflow", "Imaging Workflow"),
    ("pharmacy_dispensing", "Pharmacy Dispensing"),
    ("patient_portal_journey", "Patient Portal Journey"),
    ("provider_portal_workflow", "Provider Portal Workflow"),
    ("rcm_claims_cycle", "RCM Claims Cycle"),
    ("ai_clinical_decision", "AI Clinical Decision Support"),
    ("government_citizen", "Government Citizen Services"),
    ("workforce_scheduling", "Workforce Scheduling"),
    ("custom", "Custom Scenario"),
]


class DemoEnvironment(BaseModel):
    class Meta:
        app_label = "cybercom_demo"
        db_table = "cybercom_demo_environment"

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    demo_type = models.CharField(max_length=40, choices=DEMO_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=DEMO_STATUS_CHOICES, default="provisioning")

    # The prospect / lead associated with this demo
    prospect_name = models.CharField(max_length=200, blank=True)
    prospect_organization = models.CharField(max_length=200, blank=True)
    prospect_email = models.EmailField(blank=True)
    assigned_ae_id = models.UUIDField(null=True, blank=True)

    # Environment config
    base_url = models.URLField(max_length=500, blank=True)
    admin_username = models.CharField(max_length=100, blank=True)
    # Hashed — never stored plaintext
    admin_password_hash = models.CharField(max_length=200, blank=True)
    product_edition = models.CharField(max_length=50, default="enterprise")
    country_config = models.CharField(max_length=10, default="USA")
    language_code = models.CharField(max_length=10, default="en")

    # Lifecycle
    expires_at = models.DateTimeField(null=True, blank=True)
    last_reset_at = models.DateTimeField(null=True, blank=True)
    reset_count = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"Demo: {self.name} ({self.demo_type})"


class DemoTenant(BaseModel):
    class Meta:
        app_label = "cybercom_demo"
        db_table = "cybercom_demo_tenant"

    environment = models.ForeignKey(
        DemoEnvironment,
        on_delete=models.CASCADE,
        related_name="tenants",
    )
    tenant_name = models.CharField(max_length=200)
    tenant_type = models.CharField(max_length=50)
    platform_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    seed_dataset = models.CharField(max_length=100, default="standard")
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.tenant_name} in {self.environment.code}"


class DemoScenario(BaseModel):
    class Meta:
        app_label = "cybercom_demo"
        db_table = "cybercom_demo_scenario"

    environment = models.ForeignKey(
        DemoEnvironment,
        on_delete=models.CASCADE,
        related_name="scenarios",
    )
    scenario_type = models.CharField(max_length=40, choices=SCENARIO_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    step_count = models.PositiveSmallIntegerField(default=0)
    steps = models.JSONField(default=list)
    estimated_duration_minutes = models.PositiveSmallIntegerField(default=15)
    is_interactive = models.BooleanField(default=True)
    ai_narration_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.scenario_type})"


class DemoSession(BaseModel):
    class Meta:
        app_label = "cybercom_demo"
        db_table = "cybercom_demo_session"

    environment = models.ForeignKey(
        DemoEnvironment,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    scenario = models.ForeignKey(
        DemoScenario,
        on_delete=models.PROTECT,
        related_name="sessions",
        null=True,
        blank=True,
    )
    presenter_id = models.UUIDField(null=True, blank=True)
    attendee_names = models.JSONField(default=list)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    steps_completed = models.PositiveSmallIntegerField(default=0)
    feedback_score = models.PositiveSmallIntegerField(null=True, blank=True)
    feedback_notes = models.TextField(blank=True)
    follow_up_action = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Session in {self.environment.code} ({self.started_at})"


class DemoResetRequest(BaseModel):
    class Meta:
        app_label = "cybercom_demo"
        db_table = "cybercom_demo_reset_request"

    environment = models.ForeignKey(
        DemoEnvironment,
        on_delete=models.CASCADE,
        related_name="reset_requests",
    )
    requested_by_id = models.UUIDField(db_index=True)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed"), ("failed", "Failed")],
        default="pending",
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Reset request for {self.environment.code} ({self.status})"


class ProductTour(BaseModel):
    class Meta:
        app_label = "cybercom_demo"
        db_table = "cybercom_demo_product_tour"

    product_code = models.CharField(max_length=50, db_index=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=500, blank=True)
    tour_steps = models.JSONField(default=list)
    estimated_minutes = models.PositiveSmallIntegerField(default=5)
    language_code = models.CharField(max_length=10, default="en")
    is_published = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Tour: {self.title} ({self.product_code})"
