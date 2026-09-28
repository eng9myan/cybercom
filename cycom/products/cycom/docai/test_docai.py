"""
AI document parsing tests.

No real Anthropic API key exists in the test environment, so the
"not configured" path (extraction.py's actual, honest behavior with no key
set) is exercised for free and asserted directly -- exactly what a real
deployment sees before ANTHROPIC_API_KEY is provisioned. The "parsing
succeeded" path is tested by monkeypatching the extract() call the view
makes, not by hitting the network.
"""

import uuid
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Invoice, Partner
from products.cycom.docai import extraction
from products.cycom.docai.models import ParsedDocument
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.procurement.models import PurchaseOrder

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


def _pdf():
    return SimpleUploadedFile("invoice.pdf", b"%PDF-1.4 fake bytes", content_type="application/pdf")


def test_upload_with_no_api_key_configured_fails_honestly_not_silently(admin_client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    resp = admin_client.post(
        "/api/v1/docai/documents/",
        {"document_type": "invoice", "file": _pdf()},
        format="multipart",
    )
    assert resp.status_code == 201, resp.content
    assert resp.data["status"] == "failed"
    assert "ANTHROPIC_API_KEY" in resp.data["error_message"]
    assert resp.data["extracted_data"] == {}


def test_upload_with_extraction_succeeding_stores_the_result(admin_client, monkeypatch):
    fake_result = {"vendor_name": "Acme Co", "invoice_number": "INV-1", "total_amount": 500.0}
    monkeypatch.setattr("products.cycom.docai.views.extract", lambda **kw: fake_result)

    resp = admin_client.post(
        "/api/v1/docai/documents/",
        {"document_type": "invoice", "file": _pdf()},
        format="multipart",
    )
    assert resp.status_code == 201, resp.content
    assert resp.data["status"] == "parsed"
    assert resp.data["extracted_data"] == fake_result
    assert resp.data["original_filename"] == "invoice.pdf"


def test_review_records_human_corrected_data_without_touching_extracted_data(admin_client, tenant_id):
    doc = ParsedDocument.objects.create(
        tenant_id=tenant_id, document_type="invoice", file=_pdf(),
        status="parsed", extracted_data={"total_amount": 500.0},
    )
    resp = admin_client.post(
        f"/api/v1/docai/documents/{doc.pk}/review/",
        {"reviewed_data": {"total_amount": 550.0}},
        format="json",
    )
    assert resp.status_code == 200
    doc.refresh_from_db()
    assert doc.status == "reviewed"
    assert doc.reviewed_data == {"total_amount": 550.0}
    assert doc.extracted_data == {"total_amount": 500.0}  # the AI's original output is preserved


def test_documents_list_returns_bare_array_not_paginated_envelope(admin_client, tenant_id):
    ParsedDocument.objects.create(tenant_id=tenant_id, document_type="invoice", file=_pdf())
    resp = admin_client.get("/api/v1/docai/documents/")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)


def test_documents_are_tenant_isolated(admin_client):
    other_tenant = uuid.uuid4()
    theirs = ParsedDocument.objects.create(tenant_id=other_tenant, document_type="invoice", file=_pdf())
    resp = admin_client.get(f"/api/v1/docai/documents/{theirs.pk}/")
    assert resp.status_code == 404


def test_docai_endpoints_require_auth():
    anon = APIClient()
    assert anon.get("/api/v1/docai/documents/").status_code == 401


# -- apply: reviewed data -> real draft Invoice / PurchaseOrder ---------------

@pytest.fixture
def books(tenant_id):
    return {
        "vendor": Partner.objects.create(tenant_id=tenant_id, name="Acme Supplies", partner_type="vendor"),
        "ap": Account.objects.create(tenant_id=tenant_id, code="2100", name="AP", account_type="liability"),
        "vat": Account.objects.create(tenant_id=tenant_id, code="2200", name="Input VAT", account_type="asset"),
        "expense": Account.objects.create(tenant_id=tenant_id, code="6100", name="Supplies", account_type="expense"),
        "grni": Account.objects.create(tenant_id=tenant_id, code="2115", name="GRNI", account_type="liability"),
        "wh": Warehouse.objects.create(tenant_id=tenant_id, code="WH-MAIN", name="Main"),
        "paper": Product.objects.create(tenant_id=tenant_id, internal_ref="P-1", name="Paper"),
        "toner": Product.objects.create(tenant_id=tenant_id, internal_ref="T-1", name="Toner"),
    }


def _reviewed(tenant_id, document_type, data, status="reviewed"):
    return ParsedDocument.objects.create(
        tenant_id=tenant_id, document_type=document_type, file=_pdf(),
        status=status, extracted_data=data, reviewed_data=data,
    )


INVOICE_DATA = {
    "vendor_name": "Acme Supplies", "invoice_number": "ACME-77",
    "invoice_date": "2026-09-01", "due_date": "2026-10-01", "currency": "JOD",
    "line_items": [
        {"description": "Paper", "quantity": "10", "unit_price": "2.50", "amount": "25"},
        # amount-only line (services): qty defaults to 1, price from amount
        {"description": "Delivery", "quantity": None, "unit_price": None, "amount": 5},
    ],
}


def _invoice_params(books, **overrides):
    params = {
        "partner": str(books["vendor"].pk), "control_account": str(books["ap"].pk),
        "line_account": str(books["expense"].pk), "tax_account": str(books["vat"].pk),
        "tax_percent": "16",
    }
    params.update(overrides)
    return params


def test_apply_invoice_creates_a_real_draft_vendor_bill(admin_client, tenant_id, books):
    doc = _reviewed(tenant_id, "invoice", INVOICE_DATA)
    resp = admin_client.post(f"/api/v1/docai/documents/{doc.pk}/apply/", _invoice_params(books), format="json")
    assert resp.status_code == 200, resp.content
    assert resp.data["status"] == "applied"
    assert resp.data["applied_record_type"] == "invoice"

    invoice = Invoice.objects.get(pk=resp.data["applied_record_id"])
    assert invoice.tenant_id == tenant_id
    assert invoice.status == "draft"  # never auto-posted
    assert invoice.invoice_type == "vendor"
    assert invoice.partner == books["vendor"]
    assert str(invoice.date) == "2026-09-01"
    assert invoice.number and invoice.number != "ACME-77"  # tenant's own sequence
    lines = list(invoice.lines.order_by("description"))
    assert [(l.description, l.quantity, l.unit_price) for l in lines] == [
        ("Delivery", Decimal("1"), Decimal("5.00")),
        ("Paper", Decimal("10"), Decimal("2.50")),
    ]
    assert invoice.amount_subtotal == Decimal("30.00")
    assert invoice.amount_tax == Decimal("4.80")


def test_apply_purchase_order_maps_each_line_to_a_picked_product(admin_client, tenant_id, books):
    data = {
        "vendor_name": "Acme Supplies", "currency": "JOD",
        "line_items": [
            {"description": "A4 paper", "quantity": 20, "unit_price": 3.25, "amount": 65},
            {"description": "Toner", "quantity": 2, "unit_price": None, "amount": 90},
        ],
    }
    doc = _reviewed(tenant_id, "purchase_order", data)
    resp = admin_client.post(f"/api/v1/docai/documents/{doc.pk}/apply/", {
        "vendor": str(books["vendor"].pk), "warehouse": str(books["wh"].pk),
        "offset_account": str(books["grni"].pk),
        "line_products": [str(books["paper"].pk), str(books["toner"].pk)],
    }, format="json")
    assert resp.status_code == 200, resp.content
    po = PurchaseOrder.objects.get(pk=resp.data["applied_record_id"])
    assert po.status == "draft"  # still has to go through approval
    lines = sorted(po.lines.all(), key=lambda l: l.product.name)
    assert [(l.product, l.quantity, l.unit_cost) for l in lines] == [
        (books["paper"], Decimal("20"), Decimal("3.25")),
        (books["toner"], Decimal("2"), Decimal("45")),
    ]


def test_apply_requires_human_review_first(admin_client, tenant_id, books):
    doc = _reviewed(tenant_id, "invoice", INVOICE_DATA, status="parsed")
    resp = admin_client.post(f"/api/v1/docai/documents/{doc.pk}/apply/", _invoice_params(books), format="json")
    assert resp.status_code == 400
    assert Invoice.objects.count() == 0


def test_apply_twice_creates_only_one_record(admin_client, tenant_id, books):
    doc = _reviewed(tenant_id, "invoice", INVOICE_DATA)
    url = f"/api/v1/docai/documents/{doc.pk}/apply/"
    assert admin_client.post(url, _invoice_params(books), format="json").status_code == 200
    assert admin_client.post(url, _invoice_params(books), format="json").status_code == 409
    assert Invoice.objects.count() == 1
    # reviewed data is locked once applied, so it keeps matching the record
    resp = admin_client.post(f"/api/v1/docai/documents/{doc.pk}/review/", {"reviewed_data": {}}, format="json")
    assert resp.status_code == 409


def test_apply_rejects_missing_required_pick_and_creates_nothing(admin_client, tenant_id, books):
    doc = _reviewed(tenant_id, "invoice", INVOICE_DATA)
    resp = admin_client.post(
        f"/api/v1/docai/documents/{doc.pk}/apply/", _invoice_params(books, partner=""), format="json",
    )
    assert resp.status_code == 400
    assert "partner" in resp.data
    doc.refresh_from_db()
    assert doc.status == "reviewed" and doc.applied_record_id is None
    assert Invoice.objects.count() == 0


def test_apply_tax_percent_without_tax_account_is_rejected(admin_client, tenant_id, books):
    doc = _reviewed(tenant_id, "invoice", INVOICE_DATA)
    resp = admin_client.post(
        f"/api/v1/docai/documents/{doc.pk}/apply/", _invoice_params(books, tax_account=""), format="json",
    )
    assert resp.status_code == 400
    assert "tax_account" in resp.data


def test_apply_line_with_neither_price_nor_amount_is_rejected(admin_client, tenant_id, books):
    data = {**INVOICE_DATA, "line_items": [{"description": "?", "quantity": 1, "unit_price": None, "amount": None}]}
    doc = _reviewed(tenant_id, "invoice", data)
    resp = admin_client.post(f"/api/v1/docai/documents/{doc.pk}/apply/", _invoice_params(books), format="json")
    assert resp.status_code == 400
    assert Invoice.objects.count() == 0


def test_apply_purchase_order_needs_a_product_per_line(admin_client, tenant_id, books):
    data = {"line_items": [{"description": "a", "quantity": 1, "unit_price": 1}, {"description": "b", "quantity": 1, "unit_price": 1}]}
    doc = _reviewed(tenant_id, "purchase_order", data)
    resp = admin_client.post(f"/api/v1/docai/documents/{doc.pk}/apply/", {
        "vendor": str(books["vendor"].pk), "warehouse": str(books["wh"].pk),
        "offset_account": str(books["grni"].pk), "line_products": [str(books["paper"].pk)],
    }, format="json")
    assert resp.status_code == 400
    assert "line_products" in resp.data


def test_apply_rejects_another_tenants_records(admin_client, tenant_id, books):
    other = uuid.uuid4()
    foreign_ap = Account.objects.create(tenant_id=other, code="2100", name="AP", account_type="liability")
    foreign_partner = Partner.objects.create(tenant_id=other, name="Theirs", partner_type="vendor")
    doc = _reviewed(tenant_id, "invoice", INVOICE_DATA)
    url = f"/api/v1/docai/documents/{doc.pk}/apply/"
    resp = admin_client.post(url, _invoice_params(books, control_account=str(foreign_ap.pk)), format="json")
    assert resp.status_code == 400 and "control_account" in resp.data
    resp = admin_client.post(url, _invoice_params(books, partner=str(foreign_partner.pk)), format="json")
    assert resp.status_code == 400 and "partner" in resp.data
    assert Invoice.objects.count() == 0


def test_apply_rejects_a_group_header_account_and_hides_it_from_options(admin_client, tenant_id, books):
    # A child account makes 2100 a group/header (Account.save auto-flags it),
    # which the ledger refuses to post to -- so apply must refuse it up front.
    Account.objects.create(tenant_id=tenant_id, code="2101", name="AP Trade", account_type="liability", parent=books["ap"])
    books["ap"].refresh_from_db()
    assert books["ap"].is_postable is False

    doc = _reviewed(tenant_id, "invoice", INVOICE_DATA)
    resp = admin_client.post(f"/api/v1/docai/documents/{doc.pk}/apply/", _invoice_params(books), format="json")
    assert resp.status_code == 400 and "control_account" in resp.data
    assert Invoice.objects.count() == 0

    labels = {a["label"] for a in admin_client.get("/api/v1/docai/documents/apply-options/").data["accounts"]}
    assert "2100 AP" not in labels and "2101 AP Trade" in labels


def test_applied_invoice_can_be_posted_through_the_normal_flow(admin_client, tenant_id, books):
    doc = _reviewed(tenant_id, "invoice", INVOICE_DATA)
    resp = admin_client.post(f"/api/v1/docai/documents/{doc.pk}/apply/", _invoice_params(books), format="json")
    invoice_id = resp.data["applied_record_id"]
    resp = admin_client.post(f"/api/v1/ar-ap/invoices/{invoice_id}/post/", {}, format="json")
    assert resp.status_code == 200, resp.content
    assert resp.data["status"] == "posted"
    assert resp.data["journal_entry"]


def test_apply_bank_statement_is_not_supported(admin_client, tenant_id):
    doc = _reviewed(tenant_id, "bank_statement", {"transactions": []})
    resp = admin_client.post(f"/api/v1/docai/documents/{doc.pk}/apply/", {}, format="json")
    assert resp.status_code == 400


def test_apply_options_are_tenant_scoped_and_unpaginated(admin_client, tenant_id, books):
    for i in range(30):
        Product.objects.create(tenant_id=tenant_id, internal_ref=f"X-{i}", name=f"Extra {i}")
    Partner.objects.create(tenant_id=uuid.uuid4(), name="Other tenant's vendor", partner_type="vendor")
    resp = admin_client.get("/api/v1/docai/documents/apply-options/")
    assert resp.status_code == 200
    assert len(resp.data["products"]) == 32  # past the PAGE_SIZE=25 cap
    assert [p["label"] for p in resp.data["partners"]] == ["Acme Supplies"]
    assert {a["label"] for a in resp.data["accounts"]} >= {"2100 AP", "6100 Supplies"}


# -- extraction.py unit tests (no network) -----------------------------------

def test_extract_raises_not_configured_with_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(extraction.DocAIExtractionNotConfigured):
        extraction.extract(document_type="invoice", file_bytes=b"x", media_type="application/pdf")


def test_extract_rejects_an_unsupported_media_type(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with pytest.raises(extraction.DocAIExtractionError):
        extraction.extract(document_type="invoice", file_bytes=b"x", media_type="application/zip")


def test_extract_json_strips_a_markdown_fence():
    parsed = extraction._extract_json('```json\n{"a": 1}\n```')
    assert parsed == {"a": 1}


def test_extract_json_raises_on_no_json_found():
    with pytest.raises(extraction.DocAIExtractionError):
        extraction._extract_json("I could not read this document.")
