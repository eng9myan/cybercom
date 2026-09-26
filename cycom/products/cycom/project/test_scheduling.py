"""
Critical path / Gantt scheduling tests.

The arithmetic is the whole value here, so these assert real dates on a
known graph rather than just "an endpoint returned 200".
"""

import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cycom.project.models import Project, Task
from products.cycom.project.scheduling import DependencyCycle, compute_schedule

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "pm@cybercom.io",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["tenant_admin"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def project(tenant_id):
    return Project.objects.create(tenant_id=tenant_id, name="Fit-out")


def mk(tenant_id, project, name, days, start=None, deps=()):
    t = Task.objects.create(
        tenant_id=tenant_id, project=project, name=name,
        duration_days=days, start_date=start,
    )
    if deps:
        t.depends_on.set(deps)
    return t


def _by_name(result):
    return {r["name"]: r for r in result["tasks"]}


def test_linear_chain_schedules_back_to_back(tenant_id, project):
    """B starts the day after A finishes -- not the same day."""
    a = mk(tenant_id, project, "A", 3, date(2026, 3, 2))
    mk(tenant_id, project, "B", 2, deps=[a])

    rows = _by_name(compute_schedule(Task.objects.filter(project=project).prefetch_related("depends_on")))
    assert rows["A"]["early_start"] == "2026-03-02"
    assert rows["A"]["early_finish"] == "2026-03-04"   # 3 days inclusive
    assert rows["B"]["early_start"] == "2026-03-05"
    assert rows["B"]["early_finish"] == "2026-03-06"


def test_everything_on_a_single_chain_is_critical(tenant_id, project):
    a = mk(tenant_id, project, "A", 3, date(2026, 3, 2))
    b = mk(tenant_id, project, "B", 2, deps=[a])
    mk(tenant_id, project, "C", 1, deps=[b])

    result = compute_schedule(Task.objects.filter(project=project).prefetch_related("depends_on"))
    assert all(r["is_critical"] for r in result["tasks"])
    assert result["critical_count"] == 3
    assert result["project_finish"] == "2026-03-07"
    assert result["duration_days"] == 6


def test_parallel_branch_with_slack_is_not_critical(tenant_id, project):
    """Long branch drives the finish date; the short parallel branch gets
    slack and must NOT be reported as critical."""
    start = mk(tenant_id, project, "Start", 1, date(2026, 3, 2))
    long_a = mk(tenant_id, project, "Long", 10, deps=[start])
    short = mk(tenant_id, project, "Short", 2, deps=[start])
    mk(tenant_id, project, "End", 1, deps=[long_a, short])

    rows = _by_name(compute_schedule(Task.objects.filter(project=project).prefetch_related("depends_on")))
    assert rows["Long"]["is_critical"] is True
    assert rows["Long"]["slack_days"] == 0
    assert rows["Short"]["is_critical"] is False
    assert rows["Short"]["slack_days"] == 8   # 10 - 2
    assert rows["End"]["early_start"] == "2026-03-13"


def test_converging_dependencies_wait_for_the_latest_predecessor(tenant_id, project):
    a = mk(tenant_id, project, "A", 5, date(2026, 3, 2))
    b = mk(tenant_id, project, "B", 2, date(2026, 3, 2))
    mk(tenant_id, project, "C", 1, deps=[a, b])

    rows = _by_name(compute_schedule(Task.objects.filter(project=project).prefetch_related("depends_on")))
    # A finishes 03-06, B finishes 03-03 -> C waits for A
    assert rows["C"]["early_start"] == "2026-03-07"


def test_explicit_later_start_is_respected_over_dependency_earliest(tenant_id, project):
    """A deliberately delayed task shouldn't be yanked earlier just because
    its predecessor finished."""
    a = mk(tenant_id, project, "A", 2, date(2026, 3, 2))
    mk(tenant_id, project, "B", 1, start=date(2026, 3, 20), deps=[a])

    rows = _by_name(compute_schedule(Task.objects.filter(project=project).prefetch_related("depends_on")))
    assert rows["B"]["early_start"] == "2026-03-20"


def test_overrun_against_due_date_is_flagged(tenant_id, project):
    a = mk(tenant_id, project, "A", 10, date(2026, 3, 2))
    a.due_date = date(2026, 3, 5)
    a.save()

    rows = _by_name(compute_schedule(Task.objects.filter(project=project).prefetch_related("depends_on")))
    assert rows["A"]["overruns_due_date"] is True


def test_cycle_raises_rather_than_looping_forever(tenant_id, project):
    a = mk(tenant_id, project, "A", 1, date(2026, 3, 2))
    b = mk(tenant_id, project, "B", 1, deps=[a])
    a.depends_on.set([b])   # forced directly, bypassing serializer validation

    with pytest.raises(DependencyCycle):
        compute_schedule(Task.objects.filter(project=project).prefetch_related("depends_on"))


def test_empty_project_returns_an_empty_schedule(tenant_id, project):
    result = compute_schedule(Task.objects.filter(project=project).prefetch_related("depends_on"))
    assert result["tasks"] == []
    assert result["duration_days"] == 0


def test_dependency_outside_the_project_is_ignored_not_fatal(tenant_id, project):
    """A stale cross-project link shouldn't take down the whole Gantt."""
    other = Project.objects.create(tenant_id=tenant_id, name="Other")
    outsider = mk(tenant_id, other, "Outsider", 3, date(2026, 1, 1))
    mk(tenant_id, project, "A", 2, date(2026, 3, 2), deps=[outsider])

    rows = _by_name(compute_schedule(Task.objects.filter(project=project).prefetch_related("depends_on")))
    assert rows["A"]["early_start"] == "2026-03-02"
    assert rows["A"]["depends_on"] == []


# ── API ────────────────────────────────────────────────────────────────────

def test_schedule_endpoint_returns_critical_path(admin_client, tenant_id, project):
    a = mk(tenant_id, project, "A", 3, date(2026, 3, 2))
    mk(tenant_id, project, "B", 2, deps=[a])

    resp = admin_client.get(f"/api/v1/project/projects/{project.pk}/schedule/")
    assert resp.status_code == 200
    assert resp.data["critical_count"] == 2
    assert resp.data["project_start"] == "2026-03-02"
    assert resp.data["project_finish"] == "2026-03-06"


def test_schedule_endpoint_reports_a_cycle_as_409_not_500(admin_client, tenant_id, project):
    a = mk(tenant_id, project, "A", 1, date(2026, 3, 2))
    b = mk(tenant_id, project, "B", 1, deps=[a])
    a.depends_on.set([b])

    resp = admin_client.get(f"/api/v1/project/projects/{project.pk}/schedule/")
    assert resp.status_code == 409
    assert "cycle" in resp.data["detail"].lower()


def test_api_refuses_a_dependency_that_would_create_a_cycle(admin_client, tenant_id, project):
    a = mk(tenant_id, project, "A", 1, date(2026, 3, 2))
    b = mk(tenant_id, project, "B", 1, deps=[a])

    resp = admin_client.patch(
        f"/api/v1/project/tasks/{a.pk}/", {"depends_on": [str(b.pk)]}, format="json",
    )
    assert resp.status_code == 400
    assert "cycle" in str(resp.data).lower()


def test_api_refuses_self_dependency(admin_client, tenant_id, project):
    a = mk(tenant_id, project, "A", 1, date(2026, 3, 2))
    resp = admin_client.patch(
        f"/api/v1/project/tasks/{a.pk}/", {"depends_on": [str(a.pk)]}, format="json",
    )
    assert resp.status_code == 400


def test_schedule_is_tenant_isolated(admin_client, tenant_id):
    other_tenant = uuid.uuid4()
    other_project = Project.objects.create(tenant_id=other_tenant, name="Theirs")
    resp = admin_client.get(f"/api/v1/project/projects/{other_project.pk}/schedule/")
    assert resp.status_code == 404
