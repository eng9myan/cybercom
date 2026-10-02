"""
Tenant isolation across the whole CyMed API surface.

Regression cover for the 2026-10-02 audit, which found:
  * 210 routed viewsets serving `Model.objects.all()` with no tenant filter;
  * ~130 custom detail actions that look rows up by `pk` without get_object();
  * TenantIsolationMiddleware trusting X-Tenant-ID over the token's tenant;
  * the FHIR R4 API with no role check and no tenant filter at all;
  * commercial endpoints (licences, catalog) writable by any staff member.

The sweep test is the important one: it walks every routed DRF view, so a
view added later without scoping fails here rather than in production.
"""
import uuid
from datetime import date

import pytest
from django.urls import get_resolver
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory

from platform.api.tenancy import PLATFORM_TENANT_ID, is_tenant_model
from platform.common.tenant_context import tenant_context
from products.cymed.rcm.models import Claim837


def _client(mint_token, tenant_id, roles=("physician",), header_tenant=None):
    c = APIClient()
    tok = mint_token({
        "sub": str(uuid.uuid4()), "email": "u@cymed.io", "tenant_id": str(tenant_id),
        "realm_access": {"roles": list(roles)}, "roles": list(roles),
    })
    c.credentials(
        HTTP_AUTHORIZATION=f"Bearer {tok}",
        HTTP_X_TENANT_ID=str(header_tenant or tenant_id),
    )
    return c


def _rows(resp):
    data = resp.data if hasattr(resp, "data") else resp.json()
    return data.get("results", data) if isinstance(data, dict) else data


def _claim(tenant_id):
    return Claim837.objects.create(
        tenant_id=tenant_id, bill_id=uuid.uuid4(), encounter_id=uuid.uuid4(),
        patient_profile_id=uuid.uuid4(), payer_code="BUPA",
    )


# ── Every routed viewset is scoped ───────────────────────────────────────

def _routed_view_classes():
    seen = {}

    def walk(patterns, prefix=""):
        for p in patterns:
            if hasattr(p, "url_patterns"):
                walk(p.url_patterns, prefix + str(p.pattern))
                continue
            cls = getattr(p.callback, "cls", None)
            if cls is not None:
                seen.setdefault(cls, prefix + str(p.pattern))

    walk(get_resolver().url_patterns)
    return seen


def test_every_routed_tenant_viewset_filters_by_tenant():
    tenant = "99999999-9999-9999-9999-999999999999"
    factory = APIRequestFactory()
    unscoped = []
    for cls, path in _routed_view_classes().items():
        if getattr(cls, "tenant_scope_exempt", False) or not hasattr(cls, "get_queryset"):
            continue
        model = getattr(getattr(cls, "queryset", None), "model", None)
        if not is_tenant_model(model):
            continue
        view = cls()
        django_request = factory.get("/")
        django_request.tenant_id = tenant
        request = Request(django_request)
        view.request, view.args, view.kwargs = request, (), {}
        view.action, view.format_kwarg = "list", None
        qs = view.filter_queryset(view.get_queryset())
        if tenant.replace("-", "") not in str(qs.query).replace("-", ""):
            unscoped.append(f"{cls.__module__}.{cls.__name__} /{path}")
    assert unscoped == [], "views serving every tenant's rows:\n" + "\n".join(unscoped)


# ── The tenant comes from the token, not a header ────────────────────────

@pytest.mark.django_db
def test_x_tenant_id_header_cannot_override_token_tenant(mint_token, mock_jwks):
    a, b = uuid.uuid4(), uuid.uuid4()
    _claim(b)
    resp = _client(mint_token, a, header_tenant=b).get("/api/v1/rcm/claims/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_platform_admin_may_select_a_tenant_by_header(mint_token, mock_jwks):
    a, b = uuid.uuid4(), uuid.uuid4()
    _claim(b)
    resp = _client(mint_token, a, roles=("platform_admin",), header_tenant=b).get("/api/v1/rcm/claims/")
    assert resp.status_code == 200
    assert len(_rows(resp)) == 1


# ── Previously-unscoped viewsets + actions that bypassed get_object ──────

@pytest.mark.django_db
def test_claims_list_detail_and_actions_are_tenant_isolated(mint_token, mock_jwks):
    a, b = uuid.uuid4(), uuid.uuid4()
    mine, theirs = _claim(a), _claim(b)
    c = _client(mint_token, a)

    ids = {r["id"] for r in _rows(c.get("/api/v1/rcm/claims/"))}
    assert ids == {str(mine.id)}
    assert c.get(f"/api/v1/rcm/claims/{theirs.id}/").status_code == 404
    # scrub/submit/appeal pass `pk` straight to a service — the object guard
    # must stop them before the service ever loads the row.
    for action in ("scrub", "submit", "appeal"):
        assert c.post(f"/api/v1/rcm/claims/{theirs.id}/{action}/", {}, format="json").status_code == 404
    theirs.refresh_from_db()
    assert theirs.status == "draft"


@pytest.mark.django_db
def test_rcm_kpis_and_denials_are_per_tenant(mint_token, mock_jwks):
    a, b = uuid.uuid4(), uuid.uuid4()
    other = _claim(b)
    Claim837.objects.filter(pk=other.pk).update(status="denied")
    c = _client(mint_token, a)
    assert c.get("/api/v1/rcm/kpis/").data["total_claims"] == 0
    assert c.get("/api/v1/rcm/denials/").data == []


@pytest.mark.django_db
def test_claim_cannot_be_built_from_another_tenants_bill(mint_token, mock_jwks):
    a = uuid.uuid4()
    resp = _client(mint_token, a).post("/api/v1/rcm/claims/build/", {
        "bill_id": str(uuid.uuid4()), "encounter_id": str(uuid.uuid4()), "payer_code": "BUPA",
    }, format="json")
    assert resp.status_code == 404


# ── Commercial: catalog readable by all, writable by platform admin only ─

@pytest.mark.django_db
def test_tenants_read_the_shared_catalog_but_cannot_edit_it(mint_token, mock_jwks):
    a = uuid.uuid4()
    c = _client(mint_token, a, roles=("tenant_admin",))
    editions = _rows(c.get("/api/v1/commercial/editions/editions/"))
    assert editions, "seeded PLATFORM_TENANT catalog should be visible to every tenant"
    assert c.patch(f"/api/v1/commercial/editions/editions/{editions[0]['id']}/",
                   {"code": "hacked"}, format="json").status_code in (403, 404)


@pytest.mark.django_db
def test_tenant_staff_cannot_issue_themselves_a_licence(mint_token, mock_jwks):
    a = uuid.uuid4()
    c = _client(mint_token, a, roles=("tenant_admin",))
    assert c.post("/api/v1/commercial/licensing/licenses/", {}, format="json").status_code == 403


@pytest.mark.django_db
def test_platform_admin_can_still_edit_the_catalog(mint_token, mock_jwks):
    c = _client(mint_token, PLATFORM_TENANT_ID, roles=("platform_admin",))
    editions = _rows(c.get("/api/v1/commercial/editions/editions/"))
    resp = c.patch(f"/api/v1/commercial/editions/editions/{editions[0]['id']}/",
                   {"name": "Renamed"}, format="json")
    assert resp.status_code == 200, resp.data


# ── FHIR R4 ──────────────────────────────────────────────────────────────

def _patient(tenant_id):
    from django.apps import apps

    Patient = apps.get_model("cymed_patients", "Patient")
    with tenant_context(tenant_id):
        return Patient.objects.create(
            tenant_id=tenant_id, first_name="Other", last_name="Tenant",
            mrn=f"MRN-{uuid.uuid4().hex[:6]}", dob=date(1990, 1, 1),
        )


@pytest.mark.django_db
def test_fhir_is_tenant_scoped(mint_token, mock_jwks):
    a, b = uuid.uuid4(), uuid.uuid4()
    theirs = _patient(b)
    c = _client(mint_token, a)
    assert c.get(f"/fhir/R4/Patient/{theirs.id}").status_code == 404
    assert c.get("/fhir/R4/Patient").json()["entry"] == []
    assert c.delete(f"/fhir/R4/Patient/{theirs.id}").status_code == 404
    owner = _client(mint_token, b)
    assert owner.get(f"/fhir/R4/Patient/{theirs.id}").status_code == 200
    # names are encrypted: search is an exact blind-index match
    assert len(owner.get("/fhir/R4/Patient?family=Tenant").json()["entry"]) == 1


@pytest.mark.django_db
def test_fhir_requires_a_staff_role(mint_token, mock_jwks):
    a = uuid.uuid4()
    c = _client(mint_token, a, roles=("patient",))
    assert c.get("/fhir/R4/Patient").status_code == 403
