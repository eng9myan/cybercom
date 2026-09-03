from decimal import Decimal

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from core.viewsets import TenantScopedModelViewSet
from platform.tenant.permissions import IsPlatformAdmin
from products.cycom.accounting.services import UnbalancedEntryError, post_journal_entry
from products.cycom.ar_ap.compliance_client import notify_invoice_finalized
from products.cycom.ar_ap.models import Invoice, Partner, Payment
from products.cycom.ar_ap.serializers import InvoiceSerializer, PartnerSerializer, PaymentSerializer
from products.cycom.localization.services import get_jurisdiction_for_tenant


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

        gl_lines = []
        if invoice.invoice_type == "customer":
            # Dr Accounts Receivable (control), Cr revenue accounts, Cr tax payable
            gl_lines.append({"account": invoice.control_account, "debit": total, "credit": 0})
            for line in lines:
                gl_lines.append(
                    {"account": line.account, "debit": 0, "credit": line.subtotal, "description": line.description}
                )
            if tax_total:
                gl_lines.append({"account": invoice.tax_account, "debit": 0, "credit": tax_total})
        else:
            # vendor bill: Dr expense accounts, Dr tax receivable, Cr Accounts Payable (control)
            for line in lines:
                gl_lines.append(
                    {"account": line.account, "debit": line.subtotal, "credit": 0, "description": line.description}
                )
            if tax_total:
                gl_lines.append({"account": invoice.tax_account, "debit": tax_total, "credit": 0})
            gl_lines.append({"account": invoice.control_account, "debit": 0, "credit": total})

        try:
            entry = post_journal_entry(
                tenant_id=invoice.tenant_id,
                date=invoice.date,
                reference=invoice.number,
                lines=gl_lines,
                currency=invoice.currency,
                narration=f"Auto-posted from invoice {invoice.number}",
            )
        except UnbalancedEntryError as exc:
            raise ValidationError(f"Journal entry would be unbalanced: {exc}")

        invoice.amount_subtotal = subtotal
        invoice.amount_tax = tax_total
        invoice.amount_total = total
        invoice.status = "posted"
        invoice.journal_entry = entry
        invoice.save(
            update_fields=["amount_subtotal", "amount_tax", "amount_total", "status", "journal_entry"]
        )

        # CyID ecosystem, Phase 6 — real per-country e-invoicing routing,
        # derived from the tenant's own country_code (platform.tenant),
        # not a new field on Invoice. Never blocks/rolls back the posting
        # itself — compliance formatting is downstream of a real GL entry
        # that already exists at this point.
        jurisdiction = get_jurisdiction_for_tenant(invoice.tenant_id)
        if jurisdiction:
            notify_invoice_finalized(invoice, jurisdiction)

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

        try:
            entry = post_journal_entry(
                tenant_id=payment.tenant_id,
                date=payment.date,
                reference=f"PMT-{invoice.number}",
                lines=gl_lines,
                currency=invoice.currency,
                narration=f"Payment against invoice {invoice.number}",
            )
        except UnbalancedEntryError as exc:
            raise ValidationError(f"Journal entry would be unbalanced: {exc}")

        payment.status = "posted"
        payment.journal_entry = entry
        payment.save(update_fields=["status", "journal_entry"])

        invoice.amount_paid = invoice.amount_paid + payment.amount
        invoice.status = "paid" if invoice.amount_paid >= invoice.amount_total else "partial"
        invoice.save(update_fields=["amount_paid", "status"])

        return Response(PaymentSerializer(payment).data)
