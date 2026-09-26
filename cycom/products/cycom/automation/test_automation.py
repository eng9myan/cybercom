"""
Automation engine tests.

Covers what actually makes this safe rather than just working: the
whitelist can't be escaped, a rule that writes a watched field can't
retrigger itself forever, and an action that blows up doesn't roll back
the business write that triggered it.
"""

import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cycom.automation.models import AutomationRule, AutomationRun
from products.cycom.crm.models import Lead
from products.cycom.project.models import Task as ProjectTask
from products.cycom.sales.models import SalesOrder
from products.cycom.todo.models import Task as TodoItem

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "ops@cybercom.io",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["tenant_admin"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def _rule(tenant_id, **kw):
    defaults = dict(
        tenant_id=tenant_id,
        name="Rule",
        trigger_source="lead",
        trigger_event="created_or_updated",
        conditions=[],
        actions=[],
        is_active=True,
    )
    defaults.update(kw)
    return AutomationRule.objects.create(**defaults)


def test_rule_fires_and_sets_a_writable_field(tenant_id):
    _rule(
        tenant_id,
        conditions=[{"field": "estimated_value", "operator": "gt", "value": 1000}],
        actions=[{"type": "set_field", "field": "stage", "value": "qualified"}],
    )
    lead = Lead.objects.create(tenant_id=tenant_id, name="Big deal", estimated_value=5000)
    lead.refresh_from_db()
    assert lead.stage == "qualified"
    assert AutomationRun.objects.filter(status="matched").count() == 1


def test_rule_skips_when_condition_not_met(tenant_id):
    _rule(
        tenant_id,
        conditions=[{"field": "estimated_value", "operator": "gt", "value": 1000}],
        actions=[{"type": "set_field", "field": "stage", "value": "qualified"}],
    )
    lead = Lead.objects.create(tenant_id=tenant_id, name="Small deal", estimated_value=10)
    lead.refresh_from_db()
    assert lead.stage == "new"
    assert AutomationRun.objects.filter(status="skipped").count() == 1


def test_setting_a_watched_field_does_not_loop(tenant_id):
    """The rule's own write must not retrigger the rule -- without the
    suppression guard this recurses until the stack blows."""
    _rule(
        tenant_id,
        conditions=[{"field": "stage", "operator": "eq", "value": "new"}],
        actions=[{"type": "set_field", "field": "stage", "value": "new"}],
    )
    lead = Lead.objects.create(tenant_id=tenant_id, name="Loopy")
    lead.refresh_from_db()
    assert lead.stage == "new"
    assert AutomationRun.objects.filter(status="matched").count() == 1


def test_create_todo_action_links_back_to_the_record(tenant_id):
    _rule(
        tenant_id,
        actions=[{"type": "create_todo", "title": "Follow up on {name}", "assignee": "sam"}],
    )
    lead = Lead.objects.create(tenant_id=tenant_id, name="Acme")
    todo = TodoItem.objects.get(tenant_id=tenant_id)
    assert todo.title == "Follow up on Acme"
    assert todo.assignee == "sam"
    assert todo.linked_id == lead.pk
    assert todo.linked_model == "Lead"


def test_create_task_action(tenant_id):
    _rule(tenant_id, actions=[{"type": "create_task", "name": "Review {name}"}])
    Lead.objects.create(tenant_id=tenant_id, name="Globex")
    assert ProjectTask.objects.filter(tenant_id=tenant_id, name="Review Globex").exists()


def test_action_targeting_a_non_writable_field_is_refused_not_applied(tenant_id):
    """estimated_value is readable but NOT writable -- the action must be
    skipped and said so, not quietly write anyway."""
    _rule(tenant_id, actions=[{"type": "set_field", "field": "estimated_value", "value": 999}])
    lead = Lead.objects.create(tenant_id=tenant_id, name="Nope", estimated_value=1)
    lead.refresh_from_db()
    assert lead.estimated_value == 1
    run = AutomationRun.objects.get(status="matched")
    assert "not a writable field" in run.detail


def test_unknown_action_type_is_logged_not_raised(tenant_id):
    _rule(tenant_id, actions=[{"type": "launch_missiles"}])
    Lead.objects.create(tenant_id=tenant_id, name="Safe")
    run = AutomationRun.objects.get(status="matched")
    assert "unknown action type" in run.detail


def test_failing_action_does_not_roll_back_the_business_write(tenant_id):
    """An automation blowing up must never cost the user their record."""
    _rule(tenant_id, actions=[{"type": "send_email", "to": "ops@x.io", "subject": "hi"}])
    with pytest.MonkeyPatch().context() as mp:
        def boom(*a, **k):
            raise RuntimeError("smtp down")
        mp.setattr("products.cycom.automation.actions.send_mail", boom)
        lead = Lead.objects.create(tenant_id=tenant_id, name="Survivor")
    assert Lead.objects.filter(pk=lead.pk).exists()
    assert AutomationRun.objects.filter(status="failed").count() == 1


def test_changed_to_only_fires_on_the_transition(tenant_id):
    _rule(
        tenant_id,
        trigger_event="updated",
        conditions=[{"field": "stage", "operator": "changed_to", "value": "won"}],
        actions=[{"type": "create_todo", "title": "Celebrate"}],
    )
    lead = Lead.objects.create(tenant_id=tenant_id, name="Deal", stage="new")
    assert not TodoItem.objects.filter(tenant_id=tenant_id).exists()

    lead.stage = "won"
    lead.save()
    assert TodoItem.objects.filter(tenant_id=tenant_id, title="Celebrate").count() == 1

    lead.save()  # saving again at the same stage is not a transition
    assert TodoItem.objects.filter(tenant_id=tenant_id, title="Celebrate").count() == 1


def test_inactive_rule_never_runs(tenant_id):
    _rule(tenant_id, is_active=False, actions=[{"type": "create_todo", "title": "x"}])
    Lead.objects.create(tenant_id=tenant_id, name="Quiet")
    assert not TodoItem.objects.filter(tenant_id=tenant_id).exists()


def test_rules_are_tenant_isolated(tenant_id):
    other = uuid.uuid4()
    _rule(other, actions=[{"type": "create_todo", "title": "other tenant"}])
    Lead.objects.create(tenant_id=tenant_id, name="Mine")
    assert not TodoItem.objects.filter(title="other tenant").exists()


def test_rule_only_fires_for_its_own_source(tenant_id):
    _rule(tenant_id, trigger_source="ticket", actions=[{"type": "create_todo", "title": "ticket only"}])
    Lead.objects.create(tenant_id=tenant_id, name="Not a ticket")
    assert not TodoItem.objects.filter(title="ticket only").exists()


def test_sales_order_source_works_too(tenant_id):
    _rule(
        tenant_id,
        trigger_source="sales_order",
        conditions=[{"field": "amount_total", "operator": "gte", "value": 500}],
        actions=[{"type": "create_todo", "title": "Big order {number}"}],
    )
    SalesOrder.objects.create(
        tenant_id=tenant_id, number="SO-1", customer_name="Acme",
        order_date=date(2026, 1, 1), amount_total=900,
    )
    assert TodoItem.objects.filter(tenant_id=tenant_id, title="Big order SO-1").exists()


# ── API-level validation: a bad rule must be rejected at save time ──────────

def test_api_rejects_unknown_field(admin_client, tenant_id):
    resp = admin_client.post("/api/v1/automation/rules/", {
        "name": "bad", "trigger_source": "lead", "trigger_event": "created",
        "conditions": [{"field": "secret_column", "operator": "eq", "value": "x"}],
        "actions": [],
    }, format="json")
    assert resp.status_code == 400
    assert "not a readable field" in str(resp.data)


def test_api_rejects_numeric_operator_on_string_field(admin_client, tenant_id):
    resp = admin_client.post("/api/v1/automation/rules/", {
        "name": "bad", "trigger_source": "lead", "trigger_event": "created",
        "conditions": [{"field": "name", "operator": "gt", "value": 5}],
        "actions": [],
    }, format="json")
    assert resp.status_code == 400
    assert "numeric field" in str(resp.data)


def test_api_rejects_write_to_non_writable_field(admin_client, tenant_id):
    resp = admin_client.post("/api/v1/automation/rules/", {
        "name": "bad", "trigger_source": "lead", "trigger_event": "created",
        "conditions": [],
        "actions": [{"type": "set_field", "field": "estimated_value", "value": 1}],
    }, format="json")
    assert resp.status_code == 400
    assert "not a writable field" in str(resp.data)


def test_api_accepts_a_valid_rule_and_catalog_lists_sources(admin_client, tenant_id):
    resp = admin_client.post("/api/v1/automation/rules/", {
        "name": "good", "trigger_source": "lead", "trigger_event": "created",
        "conditions": [{"field": "estimated_value", "operator": "gt", "value": 100}],
        "actions": [{"type": "set_field", "field": "stage", "value": "qualified"}],
    }, format="json")
    assert resp.status_code == 201, resp.data

    cat = admin_client.get("/api/v1/automation/catalog/")
    assert cat.status_code == 200
    assert any(s["key"] == "lead" for s in cat.data["sources"])


def test_dry_run_reports_match_without_touching_the_record(admin_client, tenant_id):
    rule = _rule(
        tenant_id,
        conditions=[{"field": "estimated_value", "operator": "gt", "value": 100}],
        actions=[{"type": "set_field", "field": "stage", "value": "qualified"}],
        is_active=False,
    )
    lead = Lead.objects.create(tenant_id=tenant_id, name="Dry", estimated_value=500)
    resp = admin_client.post(
        f"/api/v1/automation/rules/{rule.pk}/dry-run/", {"record_id": str(lead.pk)}, format="json",
    )
    assert resp.status_code == 200
    assert resp.data["matched"] is True
    lead.refresh_from_db()
    assert lead.stage == "new"  # dry run must not mutate


def test_automation_requires_auth():
    assert APIClient().get("/api/v1/automation/rules/").status_code == 401
