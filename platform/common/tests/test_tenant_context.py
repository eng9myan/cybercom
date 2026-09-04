"""
Ambient tenant context + TenantScopedMixin.save() auto-fill.

Uses an ar_ap Account (a real BaseModel) as the concrete model under test so
this exercises the actual save() path, not a synthetic one.
"""
import uuid

import pytest

from platform.common.middleware import TenantContextMiddleware
from platform.common.tenant_context import (
    TenantContextMissing,
    clear_current_tenant,
    get_current_tenant,
    set_current_tenant,
    tenant_context,
)
from products.cycom.accounting.models import Account


@pytest.fixture(autouse=True)
def _reset_ctx():
    clear_current_tenant()
    yield
    clear_current_tenant()


def test_context_var_set_get_clear():
    assert get_current_tenant() is None
    tid = uuid.uuid4()
    set_current_tenant(tid)
    assert get_current_tenant() == tid
    clear_current_tenant()
    assert get_current_tenant() is None


def test_tenant_context_manager_restores_previous():
    outer = uuid.uuid4()
    set_current_tenant(outer)
    with tenant_context(uuid.uuid4()):
        assert get_current_tenant() != outer
    assert get_current_tenant() == outer


@pytest.mark.django_db
def test_save_fills_tenant_id_from_context():
    tid = uuid.uuid4()
    with tenant_context(tid):
        acct = Account.objects.create(code="1000", name="Cash", account_type="asset")
    acct.refresh_from_db()
    assert acct.tenant_id == tid


@pytest.mark.django_db
def test_explicit_tenant_id_is_not_overridden_by_context():
    explicit = uuid.uuid4()
    with tenant_context(uuid.uuid4()):
        acct = Account.objects.create(
            tenant_id=explicit, code="1001", name="Bank", account_type="asset"
        )
    assert acct.tenant_id == explicit


@pytest.mark.django_db
def test_save_without_tenant_or_context_raises_clear_error():
    with pytest.raises(TenantContextMissing):
        Account.objects.create(code="1002", name="X", account_type="asset")


@pytest.mark.django_db
def test_middleware_sets_and_resets_context():
    seen = {}

    def view(request):
        seen["during"] = get_current_tenant()
        return "ok"

    mw = TenantContextMiddleware(view)

    class _Req:
        tenant_id = uuid.uuid4()

    req = _Req()
    assert mw(req) == "ok"
    assert seen["during"] == req.tenant_id
    assert get_current_tenant() is None          # reset in finally
