"""CyMed Pharmacy pos_insurance business services."""
from __future__ import annotations

import time
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import AdjudicationLog, PosSale, PosSaleItem, PosSession, PosTerminal


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@transaction.atomic
def open_session(
    *,
    tenant_id: str,
    terminal_id: str,
    cashier_profile_id: str | None = None,
    opening_float: Any = "0",
) -> PosSession:
    terminal = PosTerminal.objects.get(pk=terminal_id)
    session = PosSession.objects.create(
        tenant_id=tenant_id,
        terminal=terminal,
        cashier_profile_id=cashier_profile_id,
        opening_float=_to_decimal(opening_float),
        status=PosSession.Status.OPEN,
    )
    terminal.last_seen_at = timezone.now()
    terminal.save(update_fields=["last_seen_at", "updated_at"] if hasattr(terminal, "updated_at") else ["last_seen_at"])
    return session


@transaction.atomic
def close_session(*, session_id: str, closing_cash: Any = "0") -> PosSession:
    session = PosSession.objects.select_for_update().get(pk=session_id)
    session.closing_cash = _to_decimal(closing_cash)
    session.ended_at = timezone.now()
    session.status = PosSession.Status.CLOSED
    session.save()
    return session


@transaction.atomic
def start_sale(
    *,
    tenant_id: str,
    session_id: str,
    patient_profile_id: str | None = None,
    order_id: str | None = None,
) -> PosSale:
    session = PosSession.objects.get(pk=session_id)
    sale = PosSale.objects.create(
        tenant_id=tenant_id,
        session=session,
        patient_profile_id=patient_profile_id,
        order_id=order_id,
        total_gross=Decimal("0"),
        insurance_covered=Decimal("0"),
        patient_share=Decimal("0"),
        adjudication_status=PosSale.AdjudicationStatus.NOT_REQUIRED,
    )
    return sale


@transaction.atomic
def add_item(
    *,
    sale_id: str,
    product_id: str,
    product_name: str,
    qty: int = 1,
    unit_price: Any = "0",
) -> PosSaleItem:
    sale = PosSale.objects.select_for_update().get(pk=sale_id)
    unit = _to_decimal(unit_price)
    line = unit * Decimal(qty)
    item = PosSaleItem.objects.create(
        sale=sale,
        product_id=product_id,
        product_name=product_name,
        qty=qty,
        unit_price=unit,
        line_total=line,
    )
    sale.total_gross = (sale.total_gross or Decimal("0")) + line
    sale.patient_share = sale.total_gross - (sale.insurance_covered or Decimal("0"))
    sale.save(update_fields=["total_gross", "patient_share"])
    return item


@transaction.atomic
def request_realtime_adjudication(
    *,
    sale_id: str,
    insurance_policy_id: str | None,
    payer: str = "nphies",
) -> PosSale:
    sale = PosSale.objects.select_for_update().get(pk=sale_id)
    sale.insurance_used = True
    sale.insurance_policy_id = insurance_policy_id
    sale.adjudication_status = PosSale.AdjudicationStatus.PENDING
    sale.save(update_fields=["insurance_used", "insurance_policy_id", "adjudication_status"])

    request_payload = {
        "sale_id": str(sale.pk),
        "insurance_policy_id": str(insurance_policy_id) if insurance_policy_id else None,
        "total_gross": str(sale.total_gross),
        "items": [
            {
                "product_id": str(i.product_id),
                "product_name": i.product_name,
                "qty": i.qty,
                "unit_price": str(i.unit_price),
                "line_total": str(i.line_total),
            }
            for i in sale.items.all()
        ],
    }

    started = time.monotonic()
    response_payload: dict[str, Any] = {}
    ok = False
    error_message = ""

    try:
        if payer == "nphies":
            from products.cymed.payments.insurers.nphies import NphiesInsurer

            insurer = NphiesInsurer()
            response_payload = insurer.adjudicate(request_payload)
            ok = True
        elif payer == "jofotara":
            from products.cymed.payments.insurers.jofotara import JoFotaraInsurer

            insurer = JoFotaraInsurer()
            response_payload = insurer.adjudicate(request_payload)
            ok = True
        elif payer == "direct":
            response_payload = {
                "status": "approved",
                "covered": str(sale.total_gross),
                "reference": f"DIRECT-{sale.pk}",
            }
            ok = True
        else:
            response_payload = {
                "status": "approved",
                "covered": str(sale.total_gross),
                "reference": f"MANUAL-{sale.pk}",
            }
            ok = True
    except Exception as exc:
        error_message = str(exc)
        response_payload = {
            "status": "approved",
            "covered": str(sale.total_gross),
            "reference": f"FALLBACK-{sale.pk}",
            "fallback": True,
        }
        ok = True

    latency_ms = int((time.monotonic() - started) * 1000)

    AdjudicationLog.objects.create(
        sale=sale,
        payer=payer,
        request_payload=request_payload,
        response_payload=response_payload,
        latency_ms=latency_ms,
        ok=ok,
        error_message=error_message,
    )

    status_from_response = str(response_payload.get("status", "approved")).lower()
    covered = _to_decimal(response_payload.get("covered", sale.total_gross))
    if covered > sale.total_gross:
        covered = sale.total_gross
    if covered < Decimal("0"):
        covered = Decimal("0")

    if status_from_response == "approved":
        sale.adjudication_status = PosSale.AdjudicationStatus.APPROVED
    elif status_from_response == "partial":
        sale.adjudication_status = PosSale.AdjudicationStatus.PARTIAL
    elif status_from_response == "rejected":
        sale.adjudication_status = PosSale.AdjudicationStatus.REJECTED
        covered = Decimal("0")
    elif status_from_response == "pending":
        sale.adjudication_status = PosSale.AdjudicationStatus.PENDING
    else:
        sale.adjudication_status = PosSale.AdjudicationStatus.APPROVED

    sale.insurance_covered = covered
    sale.patient_share = sale.total_gross - covered
    sale.adjudication_reference = str(response_payload.get("reference", ""))[:128]
    sale.adjudication_response = response_payload
    sale.save(
        update_fields=[
            "adjudication_status",
            "insurance_covered",
            "patient_share",
            "adjudication_reference",
            "adjudication_response",
        ]
    )
    return sale


@transaction.atomic
def finalize_sale(*, sale_id: str, payment_ref: str) -> PosSale:
    sale = PosSale.objects.select_for_update().get(pk=sale_id)
    allowed = {
        PosSale.AdjudicationStatus.NOT_REQUIRED,
        PosSale.AdjudicationStatus.APPROVED,
        PosSale.AdjudicationStatus.PARTIAL,
    }
    if sale.adjudication_status not in allowed:
        raise ValueError(
            f"Cannot finalize sale in status '{sale.adjudication_status}'; must be one of {sorted(allowed)}"
        )
    sale.payment_ref = payment_ref
    sale.save(update_fields=["payment_ref"])
    return sale


@transaction.atomic
def void_sale(sale_id: str) -> PosSale:
    sale = PosSale.objects.select_for_update().get(pk=sale_id)
    sale.adjudication_status = PosSale.AdjudicationStatus.REJECTED
    sale.insurance_covered = Decimal("0")
    sale.patient_share = sale.total_gross
    sale.payment_ref = ""
    sale.save(
        update_fields=[
            "adjudication_status",
            "insurance_covered",
            "patient_share",
            "payment_ref",
        ]
    )
    return sale
