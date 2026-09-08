import logging
from decimal import Decimal

from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from core.viewsets import TenantScopedModelViewSet
from platform.tenant.permissions import IsPlatformAdmin
from products.cycom.accounting.services import UnbalancedEntryError, post_journal_entry
from products.cycom.ar_ap.compliance_client import notify_invoice_finalized
from products.cycom.ar_ap.einvoice import run_einvoice_clearance
from products.cycom.ar_ap.models import Invoice, Partner, Payment
from products.cycom.ar_ap.serializers import InvoiceSerializer, PartnerSerializer, PaymentSerializer
from products.cycom.localization.services import get_jurisdiction_for_tenant

logger = logging.getLogger("cycom.ar_ap")


class PartnerViewSet(TenantScopedModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer

    @action(detail=True, methods=["post"], url_path="submit", permission_classes=[IsPlatformAdmin])
    def submit(self, request, pk=None):
        partner = self.get_object()
        if partner.approval_status != "draft":
            raise ValidationError(f"Partner is '{partner.approval_status}', cannot submit.")
        partner.approval_status = "submitted"
        partner.save(update_fields=["approval_status"])
        return Response(PartnerSerializer(partner).data)

    @action(detail=True, methods=["post"], url_path="approve", permission_classes=[IsPlatformAdmin])
    def approve(self, request, pk=None):
        partner = self.get_object()
        if partner.approval_status not in ("draft", "submitted"):
            raise ValidationError(f"Partner is '{partner.approval_status}', cannot approve.")
        partner.approval_status = "approved"
        partner.rejection_reason = ""
        partner.save(update_fields=["approval_status", "rejection_reason"])
        return Response(PartnerSerializer(partner).data)

    @action(detail=True, methods=["post"], url_path="reject", permission_classes=[IsPlatformAdmin])
    def reject(self, request, pk=None):
        partner = self.get_object()
        if partner.approval_status not in ("draft", "submitted"):
            raise ValidationError(f"Partner is '{partner.approval_status}', cannot reject.")
        reason = request.data.get("reason", "")
        if not reason:
            raise ValidationError("reason is required.")
        partner.approval_status = "rejected"
        partner.rejection_reason = reason
        partner.save(update_fields=["approval_status", "rejection_reason"])
        return Response(PartnerSerializer(partner).data)


class InvoiceViewSet(TenantScopedModelViewSet):
    queryset = Invoice.objects.prefetch_related("lines").all()
    serializer_class = InvoiceSerializer

    @action(detail=True, methods=["post"], url_path="post")
    def post_invoice(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status != "draft":
            raise ValidationError(f"Invoice is already '{invoice.status}', cannot post again.")

        lines = list(invoice.lines.all())
        if not lines:
            raise ValidationError("Invoice has no lines.")

        subtotal = sum((line.subtotal for line in lines), Decimal("0"))
        tax_total = sum((line.tax_amount for line in lines), Decimal("0"))
        total = subtotal + tax_total

        if tax_total and not invoice.tax_account_id:
            raise ValidationError("Invoice has tax lines but no tax_account set.")

        side = Invoice.BASE_SIDE.get(invoice.invoice_type, "customer")
        is_credit_note = invoice.invoice_type in Invoice.CREDIT_NOTE_TYPES

        # C-1: a credit/debit note must reference a posted invoice of its base
        # side, and it must not credit more than the original.
        if is_credit_note:
            original = invoice.reverses
            if original is None:
                raise ValidationError({"reverses": "A credit/debit note must reference the original invoice it reverses."})
            if Invoice.BASE_SIDE.get(original.invoice_type) != side or original.invoice_type in Invoice.CREDIT_NOTE_TYPES:
                raise ValidationError({"reverses": "Referenced document is not an invoice of the matching side."})
            if original.status not in ("posted", "partial", "paid"):
                raise ValidationError({"reverses": f"Original invoice must be posted (it is '{original.status}')."})
            already_credited = sum(
                (cn.amount_total for cn in original.credit_notes.filter(status__in=("posted", "partial", "paid"))),
                Decimal("0"),
            )
            if already_credited + total > original.amount_total + Decimal("0.01"):
                raise ValidationError(
                    f"Credit notes ({already_credited + total}) would exceed the original invoice total "
                    f"({original.amount_total})."
                )

        # HR-2: an ordinary PO-linked vendor bill must pass 3-way match
        # (ordered ↔ received ↔ billed) before it posts — previously the match
        # was a GET-only report that blocked nothing. Repost with
        # override_match=true (admin only) to accept an out-of-tolerance bill.
        if invoice.invoice_type == "vendor" and invoice.purchase_order_id:
            from products.cycom.procurement.services import three_way_match as _match

            invoice.amount_subtotal = subtotal  # in-memory so the match sees a real billed figure
            match = _match(invoice)
            blocking = [e for e in match["exceptions"] if "informational" not in e]
            if blocking:
                if not request.data.get("override_match"):
                    raise ValidationError({
                        "three_way_match": blocking,
                        "detail": "Vendor bill fails 3-way match. Resolve the exception, or repost with "
                                  "override_match=true (requires an admin role).",
                    })
                claims = getattr(request, "auth_claims", {}) or {}
                roles = set(claims.get("realm_access", {}).get("roles", []))
                if not roles & {"platform_admin", "tenant_admin", "cyidentity_admin"}:
                    raise ValidationError("override_match requires an admin role.")

        gl_lines = []
        if side == "customer":
            # normal: Dr AR (control) / Cr revenue / Cr output VAT
            # credit note: the exact reverse
            ar = {"account": invoice.control_account, "debit": 0 if is_credit_note else total,
                  "credit": total if is_credit_note else 0}
            gl_lines.append(ar)
            for line in lines:
                gl_lines.append({
                    "account": line.account,
                    "debit": line.subtotal if is_credit_note else 0,
                    "credit": 0 if is_credit_note else line.subtotal,
                    "description": line.description,
                })
            if tax_total:
                gl_lines.append({"account": invoice.tax_account,
                                 "debit": tax_total if is_credit_note else 0,
                                 "credit": 0 if is_credit_note else tax_total})
        else:
            # vendor bill normal: Dr expense / Dr input VAT / Cr AP (control)
            # vendor debit note: the exact reverse
            for line in lines:
                gl_lines.append({
                    "account": line.account,
                    "debit": 0 if is_credit_note else line.subtotal,
                    "credit": line.subtotal if is_credit_note else 0,
                    "description": line.description,
                })
            if tax_total:
                gl_lines.append({"account": invoice.tax_account,
                                 "debit": 0 if is_credit_note else tax_total,
                                 "credit": tax_total if is_credit_note else 0})
            gl_lines.append({"account": invoice.control_account,
                             "debit": total if is_credit_note else 0,
                             "credit": 0 if is_credit_note else total})

        # GL entry + invoice flip are one unit: a concurrent post that also
        # passed the draft guard loses the row_version CAS below, and its
        # journal entry rolls back with it (no double-posting).
        try:
            with transaction.atomic():
                entry = post_journal_entry(
                    tenant_id=invoice.tenant_id,
                    date=invoice.date,
                    reference=invoice.number,
                    lines=gl_lines,
                    currency=invoice.currency,
                    narration=f"Auto-posted from invoice {invoice.number}",
                )

                invoice.amount_subtotal = subtotal
                invoice.amount_tax = tax_total
                invoice.amount_total = total
                invoice.status = "posted"
                invoice.journal_entry = entry
                invoice.save_if_unchanged(
                    fields=["amount_subtotal", "amount_tax", "amount_total", "status", "journal_entry"]
                )
        except UnbalancedEntryError as exc:
            raise ValidationError(f"Journal entry would be unbalanced: {exc}")

        # CyID ecosystem, Phase 6 — real per-country e-invoicing routing,
        # derived from the tenant's own country_code (platform.tenant),
        # not a new field on Invoice. Never blocks/rolls back the posting
        # itself — compliance formatting is downstream of a real GL entry
        # that already exists at this point.
        jurisdiction = get_jurisdiction_for_tenant(invoice.tenant_id)
        if jurisdiction:
            notify_invoice_finalized(invoice, jurisdiction)

        # E-invoicing clearance (JoFotara today; ZATCA/Peppol as they land).
        # Non-blocking by policy for JO — a failure sets einvoice_status
        # "rejected" and is surfaced in the UI, never rolls back the posting.
        # Credit notes on the customer side also clear (JoFotara requires a
        # credit-note document referencing the original); the engine maps the
        # document type from invoice_type.
        if invoice.invoice_type in ("customer", "customer_credit_note"):
            try:
                run_einvoice_clearance(invoice)
            except Exception:  # pragma: no cover - defensive; helper already guards
                logger.exception("e-invoice clearance raised for %s", invoice.number)

        invoice.refresh_from_db()
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=["get"], url_path="three-way-match")
    def three_way_match(self, request, pk=None):
        """Match this vendor bill against its linked PO (ordered↔received↔billed)."""
        from products.cycom.procurement.services import three_way_match as _match
        invoice = self.get_object()
        return Response(_match(invoice))


class PaymentViewSet(TenantScopedModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    @action(detail=True, methods=["post"], url_path="post")
    def post_payment(self, request, pk=None):
        payment = self.get_object()
        if payment.status != "draft":
            raise ValidationError(f"Payment is already '{payment.status}', cannot post again.")

        invoice = payment.invoice
        if invoice.status not in ("posted", "partial"):
            raise ValidationError(f"Invoice must be posted before payment can apply; it is '{invoice.status}'.")
        if payment.amount > invoice.amount_due:
            raise ValidationError(
                f"Payment {payment.amount} exceeds amount due {invoice.amount_due} on invoice {invoice.number}."
            )

        if invoice.invoice_type == "customer":
            # customer payment received: Dr Cash, Cr Accounts Receivable
            gl_lines = [
                {"account": payment.cash_account, "debit": payment.amount, "credit": 0},
                {"account": invoice.control_account, "debit": 0, "credit": payment.amount},
            ]
        else:
            # vendor payment made: Dr Accounts Payable, Cr Cash
            gl_lines = [
                {"account": invoice.control_account, "debit": payment.amount, "credit": 0},
                {"account": payment.cash_account, "debit": 0, "credit": payment.amount},
            ]

        # One unit: JE, the payment flip, and the invoice running balance. A
        # concurrent post of this same payment loses the payment CAS; two
        # different payments racing the same invoice serialize on the invoice
        # CAS (the loser gets a 409 and retries against the fresh balance).
        try:
            with transaction.atomic():
                entry = post_journal_entry(
                    tenant_id=payment.tenant_id,
                    date=payment.date,
                    reference=f"PMT-{invoice.number}",
                    lines=gl_lines,
                    currency=invoice.currency,
                    narration=f"Payment against invoice {invoice.number}",
                )

                payment.status = "posted"
                payment.journal_entry = entry
                payment.save_if_unchanged(fields=["status", "journal_entry"])

                invoice.amount_paid = invoice.amount_paid + payment.amount
                invoice.status = "paid" if invoice.amount_paid >= invoice.amount_total else "partial"
                invoice.save_if_unchanged(fields=["amount_paid", "status"])
        except UnbalancedEntryError as exc:
            raise ValidationError(f"Journal entry would be unbalanced: {exc}")

        return Response(PaymentSerializer(payment).data)
