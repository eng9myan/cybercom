"""Bank reconciliation: import, auto-matching, exception report, finalise."""

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.finance.models import Account, BankStatement, BankStatementLine

CSV = (
    "date,description,amount,reference\n"
    "2026-03-02,Fee payment Smith,1500.00,INV-1001\n"
    "2026-03-05,Officeworks supplies,-250.00,PO-77\n"
    "2026-03-09,Fee payment Nguyen,900.00,INV-1002\n"
).encode()


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="fin@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.fixture
def books(tenant_id):
    cash = Account.objects.create(tenant_id=tenant_id, code="1000", name="Bank", account_type="asset")
    income = Account.objects.create(tenant_id=tenant_id, code="4000", name="Fees", account_type="income")
    expense = Account.objects.create(tenant_id=tenant_id, code="5000", name="Supplies", account_type="expense")
    return {"cash": cash, "income": income, "expense": expense}


def _statement(client, books, tenant_id, opening="0", closing="2150"):
    r = client.post("/api/v1/finance/bank-statements/", {
        "account": str(books["cash"].id), "reference": "MAR-2026",
        "period_start": "2026-03-01", "period_end": "2026-03-31",
        "opening_balance": opening, "closing_balance": closing,
    }, format="json")
    assert r.status_code == 201, r.data
    return r.data["id"]


def _post_entry(client, books, date, ref, amount, narration=""):
    """Money in when amount > 0 (Dr bank / Cr income), else Dr expense / Cr bank."""
    amt = abs(Decimal(amount))
    if Decimal(amount) > 0:
        lines = [{"account": str(books["cash"].id), "debit": str(amt), "credit": "0"},
                 {"account": str(books["income"].id), "debit": "0", "credit": str(amt)}]
    else:
        lines = [{"account": str(books["expense"].id), "debit": str(amt), "credit": "0"},
                 {"account": str(books["cash"].id), "debit": "0", "credit": str(amt)}]
    r = client.post("/api/v1/finance/journal-entries/",
                    {"date": date, "reference": ref, "narration": narration, "lines": lines},
                    format="json")
    assert r.status_code == 201, r.data
    return r.data["id"]


# ── Import ───────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_import_csv_and_reimport_is_idempotent(client_for, books, tenant_id):
    from django.core.files.uploadedfile import SimpleUploadedFile

    fin = client_for(["finance"])
    sid = _statement(fin, books, tenant_id)

    f = SimpleUploadedFile("mar.csv", CSV, content_type="text/csv")
    r = fin.post(f"/api/v1/finance/bank-statements/{sid}/import/", {"file": f}, format="multipart")
    assert r.status_code == 200, r.data
    assert r.data["created"] == 3

    # Re-uploading the same file must not duplicate — double-importing is the
    # fastest way to make a reconciliation lie.
    f2 = SimpleUploadedFile("mar.csv", CSV, content_type="text/csv")
    r2 = fin.post(f"/api/v1/finance/bank-statements/{sid}/import/", {"file": f2}, format="multipart")
    assert r2.data["created"] == 0
    assert r2.data["duplicates_skipped"] == 3
    assert BankStatementLine.objects.filter(tenant_id=tenant_id).count() == 3


@pytest.mark.django_db
def test_debit_credit_columns_are_supported(client_for, books, tenant_id):
    """Some AU bank exports use separate debit/credit columns, not a signed amount."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    csv2 = b"date,description,debit,credit\n2026-03-02,Fee,,1500.00\n2026-03-03,Rent,800.00,\n"
    fin = client_for(["finance"])
    sid = _statement(fin, books, tenant_id)
    f = SimpleUploadedFile("b.csv", csv2, content_type="text/csv")
    fin.post(f"/api/v1/finance/bank-statements/{sid}/import/", {"file": f}, format="multipart")
    amounts = sorted(Decimal(str(l.amount)) for l in BankStatementLine.objects.filter(tenant_id=tenant_id))
    assert amounts == [Decimal("-800.00"), Decimal("1500.00")]


@pytest.mark.django_db
def test_statement_arithmetic_is_checked(client_for, books, tenant_id):
    """Opening + lines must equal the declared closing, or the import is short."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    fin = client_for(["finance"])
    sid = _statement(fin, books, tenant_id, opening="0", closing="9999")  # wrong on purpose
    f = SimpleUploadedFile("mar.csv", CSV, content_type="text/csv")
    r = fin.post(f"/api/v1/finance/bank-statements/{sid}/import/", {"file": f}, format="multipart")
    assert r.data["statement_balances"] is False
    assert r.data["expected_closing"] == "2150.00"


# ── Matching ─────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_auto_match_pairs_by_amount_and_reference(client_for, books, tenant_id):
    from django.core.files.uploadedfile import SimpleUploadedFile

    fin = client_for(["finance"])
    sid = _statement(fin, books, tenant_id)
    f = SimpleUploadedFile("mar.csv", CSV, content_type="text/csv")
    fin.post(f"/api/v1/finance/bank-statements/{sid}/import/", {"file": f}, format="multipart")

    _post_entry(fin, books, "2026-03-02", "INV-1001", "1500")
    _post_entry(fin, books, "2026-03-05", "PO-77", "-250")
    _post_entry(fin, books, "2026-03-09", "INV-1002", "900")

    r = fin.post(f"/api/v1/finance/bank-statements/{sid}/auto-match/")
    assert r.status_code == 200, r.data
    assert r.data["matched"] == 3
    assert r.data["remaining"] == 0


@pytest.mark.django_db
def test_ambiguous_matches_are_left_for_a_human(client_for, books, tenant_id):
    """
    Two identical payments on the same day must NOT be auto-paired — silently
    picking one would conceal a duplicate payment.
    """
    fin = client_for(["finance"])
    sid = _statement(fin, books, tenant_id, closing="500")
    BankStatementLine.objects.create(tenant_id=tenant_id, statement_id=sid,
                                     date="2026-03-04", description="Payment", amount=Decimal("500"))
    _post_entry(fin, books, "2026-03-04", "", "500")
    _post_entry(fin, books, "2026-03-04", "", "500")

    r = fin.post(f"/api/v1/finance/bank-statements/{sid}/auto-match/")
    assert r.data["matched"] == 0
    assert r.data["ambiguous"] == 1
    assert r.data["needs_review"]


@pytest.mark.django_db
def test_date_tolerance_allows_late_settlement(client_for, books, tenant_id):
    fin = client_for(["finance"])
    sid = _statement(fin, books, tenant_id, closing="300")
    BankStatementLine.objects.create(tenant_id=tenant_id, statement_id=sid, date="2026-03-10",
                                     description="Fee", amount=Decimal("300"), bank_reference="INV-9")
    _post_entry(fin, books, "2026-03-08", "INV-9", "300")  # booked 2 days earlier
    r = fin.post(f"/api/v1/finance/bank-statements/{sid}/auto-match/")
    assert r.data["matched"] == 1


# ── Exception report + finalise ──────────────────────────────────────────────
@pytest.mark.django_db
def test_report_flags_both_directions(client_for, books, tenant_id):
    """
    The direction naive implementations forget: a ledger entry the bank never
    saw (unpresented cheque, duplicate, or something that should not exist).
    """
    fin = client_for(["finance"])
    sid = _statement(fin, books, tenant_id, closing="100")
    BankStatementLine.objects.create(tenant_id=tenant_id, statement_id=sid, date="2026-03-04",
                                     description="Unbooked deposit", amount=Decimal("100"))
    _post_entry(fin, books, "2026-03-06", "GHOST", "-4000", "Never cleared the bank")

    r = fin.get(f"/api/v1/finance/bank-statements/{sid}/report/")
    assert r.status_code == 200
    assert len(r.data["bank_lines_without_ledger_entry"]) == 1
    assert len(r.data["ledger_entries_without_bank_line"]) == 1
    assert r.data["fully_reconciled"] is False


@pytest.mark.django_db
def test_finalise_refuses_while_anything_is_unexplained(client_for, books, tenant_id):
    fin = client_for(["finance"])
    sid = _statement(fin, books, tenant_id, closing="100")
    BankStatementLine.objects.create(tenant_id=tenant_id, statement_id=sid, date="2026-03-04",
                                     description="Unmatched", amount=Decimal("100"))
    r = fin.post(f"/api/v1/finance/bank-statements/{sid}/finalise/")
    assert r.status_code == 400
    assert r.data["problems"]


@pytest.mark.django_db
def test_finalise_succeeds_when_everything_reconciles(client_for, books, tenant_id):
    fin = client_for(["finance"])
    sid = _statement(fin, books, tenant_id, closing="700")
    BankStatementLine.objects.create(tenant_id=tenant_id, statement_id=sid, date="2026-03-04",
                                     description="Fee", amount=Decimal("700"), bank_reference="INV-7")
    _post_entry(fin, books, "2026-03-04", "INV-7", "700")
    fin.post(f"/api/v1/finance/bank-statements/{sid}/auto-match/")

    r = fin.post(f"/api/v1/finance/bank-statements/{sid}/finalise/")
    assert r.status_code == 200, r.data
    assert r.data["status"] == "reconciled"


# ── Guards ───────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_statement_must_use_an_asset_account(client_for, books, tenant_id):
    fin = client_for(["finance"])
    r = fin.post("/api/v1/finance/bank-statements/", {
        "account": str(books["income"].id), "period_start": "2026-03-01",
        "period_end": "2026-03-31", "opening_balance": "0", "closing_balance": "0",
    }, format="json")
    assert r.status_code == 400
    assert "asset" in str(r.data).lower()


@pytest.mark.django_db
def test_bank_reconciliation_is_finance_only(client_for, books, tenant_id):
    teacher = client_for(["teacher"], email="t@cyed.edu.au")
    assert teacher.get("/api/v1/finance/bank-statements/").status_code == 403


# ── GST / BAS + debtor aging ─────────────────────────────────────────────────
@pytest.mark.django_db
def test_gst_split_is_inclusive_by_default():
    """AU prices are quoted GST-inclusive: $110 contains $10 GST, not $11."""
    from products.cyed.finance.services import split_gst

    inc = split_gst("110.00")
    assert inc["gst"] == Decimal("10.00")
    assert inc["net"] == Decimal("100.00")

    exc = split_gst("100.00", inclusive=False)
    assert exc["gst"] == Decimal("10.00")
    assert exc["gross"] == Decimal("110.00")


@pytest.mark.django_db
def test_bas_report_derives_from_the_ledger(client_for, books, tenant_id):
    from products.cyed.finance.services import gst_accounts

    collected, paid = gst_accounts(tenant_id)
    fin = client_for(["finance"])

    # Uniform-shop sale of $110 incl GST: Dr bank 110 / Cr income 100 / Cr GST 10
    fin.post("/api/v1/finance/journal-entries/", {
        "date": "2026-03-02", "reference": "SALE",
        "lines": [{"account": str(books["cash"].id), "debit": "110", "credit": "0"},
                  {"account": str(books["income"].id), "debit": "0", "credit": "100"},
                  {"account": str(collected.id), "debit": "0", "credit": "10"}],
    }, format="json")
    # Purchase of $55 incl GST: Dr expense 50 / Dr GST paid 5 / Cr bank 55
    fin.post("/api/v1/finance/journal-entries/", {
        "date": "2026-03-06", "reference": "BUY",
        "lines": [{"account": str(books["expense"].id), "debit": "50", "credit": "0"},
                  {"account": str(paid.id), "debit": "5", "credit": "0"},
                  {"account": str(books["cash"].id), "debit": "0", "credit": "55"}],
    }, format="json")

    r = fin.get("/api/v1/finance/bas/?from=2026-01-01&to=2026-12-31")
    assert r.status_code == 200, r.data
    assert Decimal(r.data["1A_gst_on_sales"]) == Decimal("10.00")
    assert Decimal(r.data["1B_gst_on_purchases"]) == Decimal("5.00")
    assert Decimal(r.data["net_gst"]) == Decimal("5.00")
    assert r.data["position"] == "payable to ATO"


@pytest.mark.django_db
def test_ar_aging_buckets_overdue_debt(client_for, books, tenant_id):
    from datetime import date, timedelta

    from products.cyed.billing.models import Installment, StudentBill
    from products.cyed.sis.models import Student

    s = Student.objects.create(tenant_id=tenant_id, first_name="Ada", last_name="L", year_level=8)
    bill = StudentBill.objects.create(tenant_id=tenant_id, student=s)
    today = date.today()
    Installment.objects.create(tenant_id=tenant_id, bill=bill, installment_no=1,
                               due_date=today - timedelta(days=45), amount_due=Decimal("500"))
    Installment.objects.create(tenant_id=tenant_id, bill=bill, installment_no=2,
                               due_date=today + timedelta(days=20), amount_due=Decimal("300"))

    fin = client_for(["finance"])
    r = fin.get("/api/v1/finance/ar-aging/")
    assert r.status_code == 200, r.data
    assert Decimal(r.data["buckets"]["31-60"]) == Decimal("500")
    assert Decimal(r.data["buckets"]["not_yet_due"]) == Decimal("300")
    assert Decimal(r.data["total_outstanding"]) == Decimal("800")


@pytest.mark.django_db
def test_bas_and_aging_are_finance_only(client_for, books, tenant_id):
    teacher = client_for(["teacher"], email="t@cyed.edu.au")
    assert teacher.get("/api/v1/finance/bas/").status_code == 403
    assert teacher.get("/api/v1/finance/ar-aging/").status_code == 403
