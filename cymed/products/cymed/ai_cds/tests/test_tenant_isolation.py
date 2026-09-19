"""
CDSAlertViewSet/RiskScoreViewSet/ICDSuggestionViewSet shipped with
`queryset = Model.objects.all()` and no get_queryset() tenant filter —
a cross-tenant PHI read risk (patient risk scores and clinical alerts).
"""
import uuid

import pytest
from rest_framework.test import APIClient

from products.cymed.ai_cds.models import CDSAlert, ICDCodeSuggestion, RiskScore


def _auth_client(tenant_id, mint_token, mock_jwks):
    client = APIClient()
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "doctor@cymed.io",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["platform_admin"]},
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    })
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant_id))
    return client


@pytest.mark.django_db
def test_alerts_are_tenant_isolated(mint_token, mock_jwks):
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    CDSAlert.objects.create(
        tenant_id=tenant_a, patient_id=uuid.uuid4(), kind="drug_allergy",
        severity="high", title="A", detail="",
    )
    CDSAlert.objects.create(
        tenant_id=tenant_b, patient_id=uuid.uuid4(), kind="drug_allergy",
        severity="high", title="B", detail="",
    )

    resp = _auth_client(tenant_a, mint_token, mock_jwks).get("/api/v1/ai-cds/alerts/")
    assert resp.status_code == 200
    rows = resp.data.get("results", resp.data)
    assert len(rows) == 1
    assert rows[0]["title"] == "A"


@pytest.mark.django_db
def test_alert_detail_404s_across_tenants(mint_token, mock_jwks):
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    alert_b = CDSAlert.objects.create(
        tenant_id=tenant_b, patient_id=uuid.uuid4(), kind="fall_risk",
        severity="medium", title="B", detail="",
    )

    resp = _auth_client(tenant_a, mint_token, mock_jwks).get(f"/api/v1/ai-cds/alerts/{alert_b.id}/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_risk_scores_are_tenant_isolated(mint_token, mock_jwks):
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    RiskScore.objects.create(
        tenant_id=tenant_a, patient_id=uuid.uuid4(), score_type="news2",
        value="3", band="low",
    )
    RiskScore.objects.create(
        tenant_id=tenant_b, patient_id=uuid.uuid4(), score_type="news2",
        value="9", band="high",
    )

    resp = _auth_client(tenant_a, mint_token, mock_jwks).get("/api/v1/ai-cds/scores/")
    assert resp.status_code == 200
    rows = resp.data.get("results", resp.data)
    assert len(rows) == 1
    assert rows[0]["band"] == "low"


@pytest.mark.django_db
def test_icd_suggestions_are_tenant_isolated(mint_token, mock_jwks):
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    ICDCodeSuggestion.objects.create(
        tenant_id=tenant_a, encounter_id=uuid.uuid4(), source_text="a",
        suggestions=[{"icd11": "A00", "label": "x", "confidence": 0.9}],
    )
    ICDCodeSuggestion.objects.create(
        tenant_id=tenant_b, encounter_id=uuid.uuid4(), source_text="b",
        suggestions=[{"icd11": "B00", "label": "y", "confidence": 0.9}],
    )

    resp = _auth_client(tenant_a, mint_token, mock_jwks).get("/api/v1/ai-cds/icd/suggestions/")
    assert resp.status_code == 200
    rows = resp.data.get("results", resp.data)
    assert len(rows) == 1
    assert rows[0]["source_text"] == "a"
