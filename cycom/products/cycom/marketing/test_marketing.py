import uuid

import pytest
from django.core import mail
from rest_framework.test import APIClient

from products.cycom.marketing.models import Campaign, MarketingRecipient
from products.cycom.marketing.services import send_campaign


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_create_and_list_campaign(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/marketing/campaigns/",
        {"name": "Summer Sale", "campaign_type": "email", "target": "All Customers"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["state"] == "draft"

    resp = platform_admin_client.get("/api/v1/marketing/campaigns/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert any(r["name"] == "Summer Sale" for r in rows)


@pytest.mark.django_db
def test_campaign_tenant_isolation(platform_admin_client, tenant_id):
    Campaign.objects.create(tenant_id=uuid.uuid4(), name="Foreign Campaign")
    resp = platform_admin_client.get("/api/v1/marketing/campaigns/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "Foreign Campaign" for r in rows)


@pytest.mark.django_db
def test_add_recipients_deduplicates(platform_admin_client, tenant_id):
    campaign = Campaign.objects.create(tenant_id=tenant_id, name="Newsletter", campaign_type="email")
    resp = platform_admin_client.post(
        f"/api/v1/marketing/campaigns/{campaign.id}/recipients/",
        {"contacts": ["a@x.com", "b@x.com", "a@x.com"]},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["added"] == 2
    assert resp.data["total_recipients"] == 2


@pytest.mark.django_db
def test_send_email_campaign_uses_real_send_mail(tenant_id):
    campaign = Campaign.objects.create(
        tenant_id=tenant_id, name="Summer Sale", campaign_type="email", body="Hello!"
    )
    MarketingRecipient.objects.create(tenant_id=tenant_id, campaign=campaign, contact="a@x.com")
    MarketingRecipient.objects.create(tenant_id=tenant_id, campaign=campaign, contact="b@x.com")

    send_campaign(campaign)
    campaign.refresh_from_db()

    assert campaign.state == "done"
    assert campaign.sent == 2
    assert campaign.failed == 0
    assert len(mail.outbox) == 2
    assert mail.outbox[0].subject == "Summer Sale"
    assert mail.outbox[0].body == "Hello!"


@pytest.mark.django_db
def test_send_sms_campaign_uses_console_backend(tenant_id, caplog):
    campaign = Campaign.objects.create(
        tenant_id=tenant_id, name="Flash Sale", campaign_type="sms", body="50% off today"
    )
    MarketingRecipient.objects.create(tenant_id=tenant_id, campaign=campaign, contact="+15551234567")

    send_campaign(campaign)
    campaign.refresh_from_db()

    assert campaign.state == "done"
    assert campaign.sent == 1
    recipient = campaign.recipients.get()
    assert recipient.status == "sent"
    assert recipient.sent_at is not None


@pytest.mark.django_db
def test_send_campaign_requires_pending_recipients(tenant_id):
    from rest_framework.exceptions import ValidationError

    campaign = Campaign.objects.create(tenant_id=tenant_id, name="Empty", campaign_type="email")
    with pytest.raises(ValidationError):
        send_campaign(campaign)


@pytest.mark.django_db
def test_cannot_resend_a_done_campaign(tenant_id):
    from rest_framework.exceptions import ValidationError

    campaign = Campaign.objects.create(tenant_id=tenant_id, name="X", campaign_type="email", state="done")
    MarketingRecipient.objects.create(tenant_id=tenant_id, campaign=campaign, contact="a@x.com")
    with pytest.raises(ValidationError):
        send_campaign(campaign)


@pytest.mark.django_db
def test_campaign_state_not_writable_via_api(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/marketing/campaigns/",
        {"name": "X", "campaign_type": "email", "state": "done", "sent": 999},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["state"] == "draft"
    assert resp.data["sent"] == 0
