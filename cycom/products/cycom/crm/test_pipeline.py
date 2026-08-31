"""CRM pipeline aggregation + activity tests."""

import uuid
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from products.cycom.crm.models import Activity, Lead
from products.cycom.crm.views import LeadViewSet

T = uuid.uuid4()


def _req(path):
    r = APIRequestFactory().get(path)
    r.tenant_id = T
    r.auth_claims = {"sub": "tester"}
    return r


class PipelineTests(TestCase):
    def setUp(self):
        def lead(stage, value, prob):
            return Lead.objects.create(
                tenant_id=T, name=f"{stage}-deal", stage=stage,
                estimated_value=Decimal(value), probability=Decimal(prob),
            )
        lead("new", "1000", "10")        # weighted 100
        lead("qualified", "2000", "50")  # weighted 1000
        lead("proposal", "5000", "80")   # weighted 4000
        lead("won", "3000", "100")       # weighted 3000 (closed, not open pipeline)

    def test_pipeline_weighted_values_and_open_total(self):
        resp = LeadViewSet.as_view({"get": "pipeline"})(_req("/crm/leads/pipeline/"))
        data = resp.data
        by = {s["stage"]: s for s in data["stages"]}
        self.assertEqual(by["new"]["count"], 1)
        self.assertEqual(by["proposal"]["weighted_value"], "4000.00")
        self.assertEqual(by["won"]["weighted_value"], "3000.00")
        # open = new + contacted + qualified + proposal = 100 + 0 + 1000 + 4000
        self.assertEqual(data["open_weighted_pipeline"], "5100.00")

    def test_tenant_isolation(self):
        # A lead in another tenant must not appear in this tenant's pipeline.
        Lead.objects.create(tenant_id=uuid.uuid4(), name="other", stage="new",
                            estimated_value=Decimal("9999"), probability=Decimal("100"))
        resp = LeadViewSet.as_view({"get": "pipeline"})(_req("/crm/leads/pipeline/"))
        by = {s["stage"]: s for s in resp.data["stages"]}
        self.assertEqual(by["new"]["count"], 1)  # still just our one "new" lead


class ActivityTests(TestCase):
    def test_open_activity_count(self):
        lead = Lead.objects.create(tenant_id=T, name="deal", stage="new")
        Activity.objects.create(tenant_id=T, lead=lead, subject="Call back", activity_type="call")
        Activity.objects.create(tenant_id=T, lead=lead, subject="Sent quote", activity_type="email", done=True)
        self.assertEqual(lead.activities.filter(done=False).count(), 1)
