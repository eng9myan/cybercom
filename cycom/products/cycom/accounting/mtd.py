"""
UK MTD VAT: the 9-box return computed from CyCom's own digital records.

MTD requires the return to be derived from digital records with no manual
re-keying, so the boxes come straight from posted invoices in the period
(by invoice date):

  box 1 / box 6  customer invoices' VAT / net, less customer credit notes
  box 4 / box 7  vendor bills' VAT / net, less vendor debit notes
  box 2 / 8 / 9  Northern Ireland <-> EU goods movements -- CyCom doesn't
                 record these separately, so they're reported as 0 and the
                 return says so (a tenant that has such movements must not
                 file from here).

Invoices in a currency other than GBP are refused rather than converted
with a guessed rate.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from platform.einvoicing.national import EInvoiceDataMissing
from platform.einvoicing.periodic.mtd_vat import NineBoxReturn
from products.cycom.ar_ap.models import Invoice

MODE = "gb_mtd"
POSTED = ("posted", "partial", "paid")
NOTES = [
    "Boxes 2, 8 and 9 (Northern Ireland goods movements with the EU) are reported as 0: CyCom does not "
    "record those movements separately. Do not file from here if the business has them.",
]


def compute_return(tenant_id, date_from: date, date_to: date) -> tuple[NineBoxReturn, dict]:
    invoices = list(Invoice.objects.filter(tenant_id=tenant_id, status__in=POSTED,
                                           date__gte=date_from, date__lte=date_to))
    problems = [
        {"scope": f"invoice:{inv.number}", "key": "currency", "label": inv.number,
         "message": f"in {inv.currency}; MTD returns are in GBP and CyCom holds no GBP rate for it"}
        for inv in invoices if (inv.currency or "").upper() != "GBP"
    ]
    if problems:
        raise EInvoiceDataMissing(MODE, problems)

    z = Decimal("0")
    sums = {"vat_sales": z, "net_sales": z, "vat_purchases": z, "net_purchases": z}
    counts = {"sales": 0, "purchases": 0}
    for inv in invoices:
        sign = Decimal("-1") if inv.invoice_type in Invoice.CREDIT_NOTE_TYPES else Decimal("1")
        if Invoice.BASE_SIDE.get(inv.invoice_type) == "customer":
            sums["vat_sales"] += sign * inv.amount_tax
            sums["net_sales"] += sign * inv.amount_subtotal
            counts["sales"] += 1
        else:
            sums["vat_purchases"] += sign * inv.amount_tax
            sums["net_purchases"] += sign * inv.amount_subtotal
            counts["purchases"] += 1
    ret = NineBoxReturn(
        vat_due_sales=sums["vat_sales"], vat_due_acquisitions=z, vat_reclaimed=sums["vat_purchases"],
        total_sales_ex_vat=sums["net_sales"], total_purchases_ex_vat=sums["net_purchases"],
        total_goods_supplied_ex_vat=z, total_acquisitions_ex_vat=z,
    )
    return ret, {"invoice_counts": counts, "notes": NOTES}
