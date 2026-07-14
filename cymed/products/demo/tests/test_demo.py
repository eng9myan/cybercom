import uuid

from django.test import TestCase

from products.demo.models import (
    DemoEnvironment,
    DemoResetRequest,
    DemoScenario,
    DemoSession,
    DemoTenant,
    ProductTour,
)

TENANT_ID = uuid.uuid4()
PRESENTER_ID = uuid.uuid4()


def make_environment(**kwargs):
    defaults = {
        "tenant_id": TENANT_ID,
        "name": "CyMed Hospital Demo",
        "code": f"demo-{uuid.uuid4().hex[:8]}",
        "demo_type": "cymed_hospital",
        "status": "active",
        "prospect_name": "Test Prospect",
        "prospect_organization": "Acme Health",
        "prospect_email": "prospect@example.com",
        "product_edition": "enterprise",
        "country_config": "USA",
        "language_code": "en",
    }
    defaults.update(kwargs)
    return DemoEnvironment.objects.create(**defaults)


class DemoEnvironmentModelTest(TestCase):
    def test_create_environment(self):
        env = make_environment()
        self.assertEqual(env.status, "active")
        self.assertEqual(env.product_edition, "enterprise")
        self.assertEqual(env.tenant_id, TENANT_ID)

    def test_str_representation(self):
        env = make_environment(name="Clinic Demo")
        self.assertIn("Clinic Demo", str(env))

    def test_unique_code(self):
        code = f"unique-{uuid.uuid4().hex[:8]}"
        make_environment(code=code)
        with self.assertRaises(Exception):
            make_environment(code=code)

    def test_default_reset_count(self):
        env = make_environment()
        self.assertEqual(env.reset_count, 0)


class DemoTenantModelTest(TestCase):
    def setUp(self):
        self.env = make_environment()

    def test_create_tenant(self):
        tenant = DemoTenant.objects.create(
            tenant_id=TENANT_ID,
            environment=self.env,
            tenant_name="Demo Hospital A",
            tenant_type="hospital",
            seed_dataset="hospital_medium",
            is_primary=True,
        )
        self.assertTrue(tenant.is_primary)
        self.assertEqual(tenant.environment, self.env)


class DemoScenarioModelTest(TestCase):
    def setUp(self):
        self.env = make_environment()

    def test_create_scenario(self):
        scenario = DemoScenario.objects.create(
            tenant_id=TENANT_ID,
            environment=self.env,
            scenario_type="patient_journey",
            title="ER to Admission Flow",
            description="Demonstrates full ED to inpatient journey",
            step_count=5,
            steps=[{"order": 1, "action": "register_patient"}],
            estimated_duration_minutes=20,
            is_interactive=True,
            ai_narration_enabled=True,
            is_active=True,
        )
        self.assertEqual(scenario.scenario_type, "patient_journey")
        self.assertTrue(scenario.is_active)

    def test_inactive_scenario(self):
        s = DemoScenario.objects.create(
            tenant_id=TENANT_ID,
            environment=self.env,
            scenario_type="billing_cycle",
            title="RCM Billing Demo",
            step_count=3,
            steps=[],
            is_active=False,
        )
        self.assertFalse(s.is_active)


class DemoSessionModelTest(TestCase):
    def setUp(self):
        self.env = make_environment()
        self.scenario = DemoScenario.objects.create(
            tenant_id=TENANT_ID,
            environment=self.env,
            scenario_type="pharmacy",
            title="Pharmacy Workflow",
            step_count=4,
            steps=[],
            is_active=True,
        )

    def test_create_session(self):
        session = DemoSession.objects.create(
            tenant_id=TENANT_ID,
            environment=self.env,
            scenario=self.scenario,
            presenter_id=PRESENTER_ID,
            attendee_names=["Alice", "Bob"],
            steps_completed=0,
        )
        self.assertIsNone(session.ended_at)
        self.assertIsNone(session.feedback_score)

    def test_session_without_scenario(self):
        session = DemoSession.objects.create(
            tenant_id=TENANT_ID,
            environment=self.env,
            presenter_id=PRESENTER_ID,
            attendee_names=[],
            steps_completed=0,
        )
        self.assertIsNone(session.scenario)


class DemoResetRequestModelTest(TestCase):
    def setUp(self):
        self.env = make_environment()

    def test_create_reset_request(self):
        req = DemoResetRequest.objects.create(
            tenant_id=TENANT_ID,
            environment=self.env,
            requested_by_id=PRESENTER_ID,
            reason="Prospect needs fresh data",
            status="pending",
        )
        self.assertEqual(req.status, "pending")

    def test_status_transitions(self):
        req = DemoResetRequest.objects.create(
            tenant_id=TENANT_ID,
            environment=self.env,
            requested_by_id=PRESENTER_ID,
            reason="Demo day reset",
            status="pending",
        )
        req.status = "in_progress"
        req.save()
        req.refresh_from_db()
        self.assertEqual(req.status, "in_progress")


class ProductTourModelTest(TestCase):
    def test_create_product_tour(self):
        tour = ProductTour.objects.create(
            tenant_id=TENANT_ID,
            product_code="cymed",
            title="CyMed Hospital Tour",
            subtitle="Discover the full hospital platform",
            tour_steps=[
                {"step": 1, "title": "Dashboard", "description": "Overview"},
                {"step": 2, "title": "Patients", "description": "Patient management"},
            ],
            estimated_minutes=10,
            language_code="en",
            is_published=True,
        )
        self.assertEqual(tour.view_count, 0)
        self.assertTrue(tour.is_published)

    def test_view_count_increment(self):
        tour = ProductTour.objects.create(
            tenant_id=TENANT_ID,
            product_code="cycom",
            title="CyCom ERP Tour",
            subtitle="HR and Finance demo",
            tour_steps=[],
            estimated_minutes=8,
            language_code="en",
            is_published=True,
            view_count=5,
        )
        tour.view_count += 1
        tour.save()
        tour.refresh_from_db()
        self.assertEqual(tour.view_count, 6)

    def test_unpublished_tour(self):
        tour = ProductTour.objects.create(
            tenant_id=TENANT_ID,
            product_code="cygov",
            title="CyGov Tour (Draft)",
            subtitle="",
            tour_steps=[],
            estimated_minutes=5,
            language_code="ar",
            is_published=False,
        )
        self.assertFalse(tour.is_published)
