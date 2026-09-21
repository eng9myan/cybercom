import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Partner
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.procurement.models import (
    PurchaseRequest,
    PurchaseRequestLine,
    RequestForQuotation,
    VendorBid,
    VendorBidLine,
)


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


@pytest.fixture
def rfq_setup(db, tenant_id):
    inv_acct = Account.objects.create(
        tenant_id=tenant_id, code="1140", name="Inventory", account_type="asset"
    )
    grni = Account.objects.create(
        tenant_id=tenant_id, code="2115", name="GRNI", account_type="liability"
    )
    warehouse = Warehouse.objects.create(tenant_id=tenant_id, code="WH-MAIN", name="Main")
    product = Product.objects.create(
        tenant_id=tenant_id, internal_ref="RB-12", name="Rebar 12mm", inventory_account=inv_acct
    )
    vendor_a = Partner.objects.create(tenant_id=tenant_id, name="Vendor A", partner_type="vendor")
    vendor_b = Partner.objects.create(tenant_id=tenant_id, name="Vendor B", partner_type="vendor")

    pr = PurchaseRequest.objects.create(tenant_id=tenant_id, status="approved")
    PurchaseRequestLine.objects.create(
        tenant_id=tenant_id, request=pr, product=product, quantity=Decimal("100"), estimated_unit_cost=5
    )
    rfq = RequestForQuotation.objects.create(tenant_id=tenant_id, source_request=pr)

    bid_a = VendorBid.objects.create(tenant_id=tenant_id, rfq=rfq, vendor=vendor_a)
    VendorBidLine.objects.create(
        tenant_id=tenant_id, bid=bid_a, product=product, quantity=Decimal("100"), unit_cost=Decimal("4.50")
    )
    bid_b = VendorBid.objects.create(tenant_id=tenant_id, rfq=rfq, vendor=vendor_b)
    VendorBidLine.objects.create(
        tenant_id=tenant_id, bid=bid_b, product=product, quantity=Decimal("100"), unit_cost=Decimal("5.25")
    )

    return {
        "rfq": rfq, "bid_a": bid_a, "bid_b": bid_b, "warehouse": warehouse,
        "grni": grni, "product": product, "pr": pr,
    }


@pytest.mark.django_db
def test_submit_bid_requires_positive_unit_cost(platform_admin_client, tenant_id):
    inv_acct = Account.objects.create(tenant_id=tenant_id, code="1140", name="Inv", account_type="asset")
    vendor = Partner.objects.create(tenant_id=tenant_id, name="V", partner_type="vendor")
    product = Product.objects.create(tenant_id=tenant_id, internal_ref="P1", name="P1", inventory_account=inv_acct)
    pr = PurchaseRequest.objects.create(tenant_id=tenant_id, status="approved")
    rfq = RequestForQuotation.objects.create(tenant_id=tenant_id, source_request=pr)
    bid = VendorBid.objects.create(tenant_id=tenant_id, rfq=rfq, vendor=vendor)
    VendorBidLine.objects.create(tenant_id=tenant_id, bid=bid, product=product, quantity=1, unit_cost=0)

    resp = platform_admin_client.post(f"/api/v1/procurement/bids/{bid.id}/submit/")
    assert resp.status_code == 400

    bid.lines.update(unit_cost=Decimal("2.00"))
    resp = platform_admin_client.post(f"/api/v1/procurement/bids/{bid.id}/submit/")
    assert resp.status_code == 200
    assert resp.data["status"] == "submitted"


@pytest.mark.django_db
def test_award_requires_submitted_bid(platform_admin_client, tenant_id, rfq_setup):
    resp = platform_admin_client.post(
        f"/api/v1/procurement/rfqs/{rfq_setup['rfq'].id}/award/",
        {
            "bid_id": str(rfq_setup["bid_a"].id),
            "warehouse": str(rfq_setup["warehouse"].id),
            "offset_account": str(rfq_setup["grni"].id),
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_award_creates_po_and_marks_other_bids_lost(platform_admin_client, tenant_id, rfq_setup):
    for bid in (rfq_setup["bid_a"], rfq_setup["bid_b"]):
        bid.status = "submitted"
        bid.save(update_fields=["status"])

    resp = platform_admin_client.post(
        f"/api/v1/procurement/rfqs/{rfq_setup['rfq'].id}/award/",
        {
            "bid_id": str(rfq_setup["bid_a"].id),
            "warehouse": str(rfq_setup["warehouse"].id),
            "offset_account": str(rfq_setup["grni"].id),
        },
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert str(resp.data["vendor"]) == str(rfq_setup["bid_a"].vendor_id)
    assert len(resp.data["lines"]) == 1
    assert Decimal(resp.data["lines"][0]["unit_cost"]) == Decimal("4.50")

    rfq_setup["bid_a"].refresh_from_db()
    rfq_setup["bid_b"].refresh_from_db()
    rfq_setup["rfq"].refresh_from_db()
    rfq_setup["pr"].refresh_from_db()
    assert rfq_setup["bid_a"].status == "won"
    assert rfq_setup["bid_b"].status == "lost"
    assert rfq_setup["rfq"].status == "awarded"
    assert rfq_setup["pr"].status == "converted"


@pytest.mark.django_db
def test_cannot_award_twice(platform_admin_client, tenant_id, rfq_setup):
    for bid in (rfq_setup["bid_a"], rfq_setup["bid_b"]):
        bid.status = "submitted"
        bid.save(update_fields=["status"])
    body = {
        "bid_id": str(rfq_setup["bid_a"].id),
        "warehouse": str(rfq_setup["warehouse"].id),
        "offset_account": str(rfq_setup["grni"].id),
    }
    resp = platform_admin_client.post(
        f"/api/v1/procurement/rfqs/{rfq_setup['rfq'].id}/award/", body, format="json"
    )
    assert resp.status_code == 201

    resp = platform_admin_client.post(
        f"/api/v1/procurement/rfqs/{rfq_setup['rfq'].id}/award/", body, format="json"
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_award_rejects_bid_from_another_rfq(platform_admin_client, tenant_id, rfq_setup):
    other_pr = PurchaseRequest.objects.create(tenant_id=tenant_id, status="approved")
    other_rfq = RequestForQuotation.objects.create(tenant_id=tenant_id, source_request=other_pr)
    resp = platform_admin_client.post(
        f"/api/v1/procurement/rfqs/{other_rfq.id}/award/",
        {
            "bid_id": str(rfq_setup["bid_a"].id),
            "warehouse": str(rfq_setup["warehouse"].id),
            "offset_account": str(rfq_setup["grni"].id),
        },
        format="json",
    )
    assert resp.status_code == 400
