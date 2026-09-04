"""@tenant_task establishes the tenant context for the task body."""
import uuid

import pytest
from django.test import override_settings

from platform.common.celery import tenant_task
from platform.common.tenant_context import (
    TenantContextMissing,
    clear_current_tenant,
    get_current_tenant,
)
from products.cycom.accounting.models import Account


@pytest.fixture(autouse=True)
def _clean():
    clear_current_tenant()
    yield
    clear_current_tenant()


@tenant_task()
def _capture(tenant_id, marker):
    return {"ctx": str(get_current_tenant()), "marker": marker}


@tenant_task(bind=True)
def _capture_bound(self, tenant_id, marker):
    return {"ctx": str(get_current_tenant()), "marker": marker, "name": self.name}


@tenant_task()
def _make_account(tenant_id, code):
    # no tenant_id= kwarg on create — must be filled from the context @tenant_task set
    return str(Account.objects.create(code=code, name="x", account_type="asset").tenant_id)


def test_context_set_from_positional_tenant_id():
    tid = str(uuid.uuid4())
    with override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True):
        r = _capture.apply(args=(tid, "m1")).get()
    assert r == {"ctx": tid, "marker": "m1"}


def test_context_set_from_kwarg_and_bound():
    tid = str(uuid.uuid4())
    with override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True):
        r = _capture_bound.apply(kwargs={"tenant_id": tid, "marker": "m2"}).get()
    assert r["ctx"] == tid and r["marker"] == "m2"


def test_missing_tenant_id_raises():
    with override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True):
        with pytest.raises(TenantContextMissing):
            _capture.apply(args=(), kwargs={}).get()


@pytest.mark.django_db
def test_task_body_write_gets_tenant_from_context():
    tid = str(uuid.uuid4())
    with override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True):
        got = _make_account.apply(args=(tid, "9001")).get()
    assert got == tid
    clear_current_tenant()
    # context is torn down after the task
    assert get_current_tenant() is None
