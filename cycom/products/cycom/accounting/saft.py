"""
Ledger -> Norwegian SAF-T Financial (platform.einvoicing.periodic.saft_no).

Collects one tenant's posted general ledger for a date range and resolves
everything the audit file needs that the ledger itself doesn't carry:

- each GL account's mandatory GroupingCategory/GroupingCode (stored on
  Account.attributes["saft"], validated against Skatteetaten's official
  list);
- VAT information per revenue/expense line, recovered from the invoice
  the journal entry was posted from (the entry's lines are matched back to
  that invoice's lines by account and amount), with the standard tax code
  derived from the rate where that's unambiguous and from the tenant's
  configured default for 0% lines otherwise;
- customer/supplier master data and per-party AR/AP balances, from the
  invoice and payment entries' control-account lines.

Anything that can't be resolved is collected into one EInvoiceDataMissing
(mode "no_saft") so the user sees the complete to-do list at once.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from decimal import Decimal

from platform.einvoicing.models import EInvoiceProfile
from platform.einvoicing.national import EInvoiceDataMissing
from platform.einvoicing.periodic.saft_no import (
    PURCHASE_CODE_BY_RATE,
    PURCHASE_ZERO_CODES,
    SALES_CODE_BY_RATE,
    SALES_ZERO_CODES,
    SaftAccount,
    SaftAddress,
    SaftCompany,
    SaftInput,
    SaftLine,
    SaftParty,
    SaftTax,
    SaftTransaction,
    grouping_codes,
)
from platform.tenant.models import Tenant, TenantProfile
from products.cycom.accounting.models import Account, JournalLine
from products.cycom.ar_ap.models import Invoice, Payment

MODE = "no_saft"
SAFT_ATTR = "saft"
# Tenant-level SAF-T settings live in EInvoiceProfile.national under these keys.
SETTING_KEYS = ("saft_contact_first_name", "saft_contact_last_name", "saft_contact_phone",
                "saft_sales_zero_code", "saft_purchase_zero_code")


def _problem(scope, key, label, message):
    return {"scope": scope, "key": key, "label": label, "message": message}


def _company(tenant_id, problems) -> SaftCompany:
    ep = EInvoiceProfile.objects.filter(tenant_id=tenant_id).first()
    tp = TenantProfile.objects.filter(tenant_id=tenant_id).first()
    tenant = Tenant.objects.filter(id=tenant_id).first()
    national = (ep.national if ep else {}) or {}
    org = re.sub(r"\D", "", (ep.tax_id if ep and ep.tax_id else getattr(tp, "vat_number", "")) or "")[:9]
    if not re.fullmatch(r"\d{9}", org):
        problems.append(_problem("company", "tax_id", "Organisasjonsnummer",
                                 "a 9-digit organisation number is required (E-Invoicing settings: tax id)"))
    name = ((ep.legal_name if ep else "") or getattr(tp, "legal_name", "") or getattr(tenant, "name", "")).strip()
    for key, label in (("saft_contact_first_name", "Contact first name"),
                       ("saft_contact_last_name", "Contact last name"),
                       ("saft_contact_phone", "Contact telephone")):
        if not (national.get(key) or "").strip():
            problems.append(_problem("company", key, label, "required in the SAF-T header"))
    return SaftCompany(
        registration_number=org, name=name or "-",
        contact_first_name=national.get("saft_contact_first_name", ""),
        contact_last_name=national.get("saft_contact_last_name", ""),
        telephone=national.get("saft_contact_phone", ""),
        email=(ep.email if ep else "") or "",
        address=SaftAddress(street=ep.street if ep else "", number=ep.building_number if ep else "",
                            city=ep.city if ep else "", postal_code=ep.postal_code if ep else ""),
    )


def _net(lines):
    return sum((ln.debit - ln.credit for ln in lines), Decimal("0"))


def collect(tenant_id, date_from: date, date_to: date, currency: str = "NOK") -> SaftInput:
    problems: list[dict] = []
    company = _company(tenant_id, problems)
    national = (getattr(EInvoiceProfile.objects.filter(tenant_id=tenant_id).first(), "national", None) or {})

    posted = (JournalLine.objects.filter(tenant_id=tenant_id, entry__status="posted", entry__date__lte=date_to)
              .select_related("entry", "account"))
    all_lines = list(posted)

    # -- accounts: every account with a balance or movement up to date_to ----
    by_account = defaultdict(list)
    for ln in all_lines:
        by_account[ln.account_id].append(ln)
    codes = grouping_codes()
    accounts = []
    for acc in Account.objects.filter(tenant_id=tenant_id, id__in=by_account.keys()).order_by("code"):
        lines = by_account[acc.id]
        opening = _net([l for l in lines if l.entry.date < date_from])
        closing = opening + _net([l for l in lines if l.entry.date >= date_from])
        mapping = (acc.attributes or {}).get(SAFT_ATTR, {})
        cat, code = mapping.get("grouping_category", ""), mapping.get("grouping_code", "")
        if not cat or not code:
            problems.append(_problem(f"account:{acc.code}", "grouping", f"{acc.code} {acc.name}",
                                     "map this account to a Skatteetaten grouping category and code"))
        elif code not in codes.get(cat, {}):
            problems.append(_problem(f"account:{acc.code}", "grouping", f"{acc.code} {acc.name}",
                                     f"'{cat}/{code}' is not in the official grouping code list"))
        accounts.append(SaftAccount(acc.code, acc.name, cat, code, opening, closing))

    # -- documents behind the entries --------------------------------------------
    je_ids = {ln.entry_id for ln in all_lines}
    invoices = {inv.journal_entry_id: inv for inv in Invoice.objects.filter(
        tenant_id=tenant_id, journal_entry_id__in=je_ids).select_related("partner", "control_account")
        .prefetch_related("lines")}
    payments = {p.journal_entry_id: p for p in Payment.objects.filter(
        tenant_id=tenant_id, journal_entry_id__in=je_ids).select_related("partner", "invoice")}

    def party_of(je_id):
        """(partner, role, control_account_id) for invoice/payment entries."""
        inv = invoices.get(je_id)
        if inv:
            role = "customer" if Invoice.BASE_SIDE.get(inv.invoice_type) == "customer" else "supplier"
            return inv.partner, role, inv.control_account_id
        pay = payments.get(je_id)
        if pay:
            role = "customer" if Invoice.BASE_SIDE.get(pay.invoice.invoice_type) == "customer" else "supplier"
            return pay.partner, role, pay.invoice.control_account_id
        return None

    # -- party balances from control-account lines ---------------------------
    party_lines = defaultdict(list)
    parties = {}
    for ln in all_lines:
        info = party_of(ln.entry_id)
        if info and ln.account_id == info[2]:
            partner, role, _ctrl = info
            key = (role, partner.id)
            party_lines[key].append(ln)
            parties[key] = (partner, ln.account.code)

    customers, suppliers = [], []
    for (role, pid), lines in sorted(party_lines.items(), key=lambda kv: parties[kv[0]][0].name):
        partner, acc_code = parties[(role, pid)]
        opening = _net([l for l in lines if l.entry.date < date_from])
        closing = opening + _net([l for l in lines if l.entry.date >= date_from])
        p = SaftParty(str(partner.id)[:35], partner.name, registration_number=(partner.tax_id or "")[:35],
                      balance_account_id=acc_code, opening=opening, closing=closing)
        (customers if role == "customer" else suppliers).append(p)

    # -- transactions ---------------------------------------------------------------
    period_lines = defaultdict(list)
    for ln in all_lines:
        if ln.entry.date >= date_from:
            period_lines[ln.entry_id].append(ln)
    transactions = []
    for je_id, lines in sorted(period_lines.items(), key=lambda kv: (kv[1][0].entry.date, str(kv[0]))):
        entry = lines[0].entry
        if (entry.currency or currency).upper() != currency.upper():
            problems.append(_problem(f"entry:{entry.reference or entry.id}", "currency", "Currency",
                                     f"entry is in {entry.currency}; this export covers {currency} books only"))
        info = party_of(je_id)
        tax_by_line = _tax_for_entry(invoices.get(je_id), lines, national, problems)
        saft_lines = []
        for ln in lines:
            sl = SaftLine(ln.account.code, ln.description or entry.narration or entry.reference,
                          debit=ln.debit, credit=ln.credit, tax=tax_by_line.get(ln.id))
            if info and ln.account_id == info[2]:
                if info[1] == "customer":
                    sl.customer_id = str(info[0].id)[:35]
                else:
                    sl.supplier_id = str(info[0].id)[:35]
            saft_lines.append(sl)
        voucher = ("Invoice" if je_id in invoices else "Payment" if je_id in payments else "Journal")
        transactions.append(SaftTransaction(
            transaction_id=(entry.reference or str(entry.id))[:70], date=entry.date,
            description=entry.narration or entry.reference or "Journal entry",
            system_entry_date=entry.created_at.date(), lines=saft_lines,
            source_id=(entry.created_by or "")[:35], voucher_type=voucher))

    if problems:
        raise EInvoiceDataMissing(MODE, problems)
    return SaftInput(company=company, period_start=date_from, period_end=date_to, currency=currency,
                     accounts=accounts, customers=customers, suppliers=suppliers, transactions=transactions)


def _tax_for_entry(invoice, lines, national, problems) -> dict:
    """Attach TaxInformation to the revenue/expense lines of an invoice's
    entry by matching them to the invoice's own lines (account + amount)."""
    if invoice is None:
        return {}
    sales = Invoice.BASE_SIDE.get(invoice.invoice_type) == "customer"
    credit_note = invoice.invoice_type in Invoice.CREDIT_NOTE_TYPES
    # a sale credits revenue (debits on a credit note); a purchase the reverse
    revenue_is_credit = sales != credit_note
    unused = [ln for ln in lines if ln.account_id not in (invoice.control_account_id, invoice.tax_account_id)]
    out = {}
    for il in invoice.lines.all():
        base = il.subtotal.quantize(Decimal("0.01"))
        match = next((ln for ln in unused if ln.account_id == il.account_id
                      and (ln.credit if revenue_is_credit else ln.debit) == base), None)
        if match is None:
            continue
        unused.remove(match)
        rate = Decimal(il.tax_percent).normalize()
        override = ((il.attributes or {}).get("saft", {}) or {}).get("tax_code")
        if override:
            code = override
        elif rate == 0:
            code = national.get("saft_sales_zero_code" if sales else "saft_purchase_zero_code", "")
            allowed = SALES_ZERO_CODES if sales else PURCHASE_ZERO_CODES
            if code not in allowed:
                problems.append(_problem(f"invoice:{invoice.number}", "tax_code", "0% VAT code",
                                         "set the default standard tax code for 0% "
                                         + ("sales" if sales else "purchases")
                                         + f" ({', '.join(allowed)}) in SAF-T settings"))
                continue
        else:
            code = (SALES_CODE_BY_RATE if sales else PURCHASE_CODE_BY_RATE).get(rate)
            if code is None:
                problems.append(_problem(f"invoice:{invoice.number}", "tax_percent", "VAT rate",
                                         f"{rate}% is not a Norwegian VAT rate (25/15/12/11.11/0)"))
                continue
        out[match.id] = SaftTax(code=code, percentage=rate, base=base, amount=il.tax_amount,
                                debit=not revenue_is_credit)
    return out
