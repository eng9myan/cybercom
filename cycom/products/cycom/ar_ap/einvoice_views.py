"""
E-invoicing settings + per-invoice national-format actions.

Everything format-specific is driven by the format's FieldSpecs
(platform.einvoicing.national), so these views never hardcode a country:
the settings page and the invoice panel render whatever fields the tenant's
mode declares, and the same specs validate what's saved.
"""
from __future__ import annotations

import re
import uuid

from django.db import transaction
from django.http import HttpResponse
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from platform.einvoicing.engine import NATIONAL_FORMATS, mode_for_country
from platform.einvoicing.models import EInvoiceInteraction, EInvoiceProfile
from platform.einvoicing.signing import KEY_LOADER, NATIONAL_KEY_ENV
from platform.tenant.models import Tenant, TenantProfile
from products.cycom.accounting.sequencing import OVERRIDE_ROLES
from products.cycom.ar_ap.einvoice import (
    EINVOICE_ATTR,
    national_doc_input,
    resubmit_generated,
    run_einvoice_clearance,
)
from products.cycom.ar_ap.models import Invoice, InvoiceLine, Partner

_BUYER_CORE = ("tax_id", "name", "street", "building_number", "city", "postal_code",
               "region", "country_code", "email")


def _require_finance_role(request):
    session = getattr(request, "user_session", None) or {}
    roles = set(session.get("roles", []))
    claims = getattr(request, "auth_claims", None) or {}
    roles |= set(claims.get("realm_access", {}).get("roles", []))
    if not roles & OVERRIDE_ROLES:
        raise PermissionDenied("Changing e-invoicing data requires a finance or admin role.")


def _tenant_country(tenant_id) -> str:
    tenant = Tenant.objects.filter(id=tenant_id).first()
    return (getattr(tenant, "country_code", "") or "").upper()


def _clean(specs, values: dict, scope_label: str) -> tuple[dict, list[dict]]:
    """Keep only keys a spec declares; validate format of non-blank values.
    Blank is allowed on save (a profile is filled in over time); what's
    required is enforced when a document is actually built."""
    by_key = {s.key: s for s in specs}
    out, errors = {}, []
    for key, raw in (values or {}).items():
        spec = by_key.get(key)
        if spec is None:
            continue
        value = "" if raw is None else str(raw).strip()
        if value:
            if spec.pattern and not re.fullmatch(spec.pattern, value):
                errors.append({"scope": scope_label, "key": key, "message": "invalid format"})
                continue
            if spec.choices and value not in {c for c, _ in spec.choices}:
                errors.append({"scope": scope_label, "key": key, "message": "not a valid option"})
                continue
        out[key] = value
    return out, errors


def _format_for(tenant_id):
    country = _tenant_country(tenant_id)
    mode = mode_for_country(country)
    return country, mode, NATIONAL_FORMATS.get(mode or "")


class EInvoiceProfileView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def _payload(self, tenant_id):
        country, mode, fmt = _format_for(tenant_id)
        ep = EInvoiceProfile.objects.filter(tenant_id=tenant_id).first()
        tprofile = TenantProfile.objects.filter(tenant_id=tenant_id).first()
        values = {}
        if ep:
            values = {k: getattr(ep, k) for k in EInvoiceProfile.CORE_FIELDS}
            values.update(ep.national or {})
        values.setdefault("legal_name", "")
        values.setdefault("tax_id", "")
        # Map the format-spec vocabulary ("name") onto the profile column.
        values["name"] = values.get("legal_name") or ""
        key_pem, cert_pem = KEY_LOADER(mode) if mode else (None, None)
        return {
            "country_code": country,
            "mode": mode,
            "mode_label": fmt.label if fmt else None,
            "is_national": fmt is not None,
            "fields": [s.as_dict() for s in fmt.fields if s.scope == "seller"] if fmt else [],
            "buyer_fields": [s.as_dict() for s in fmt.fields if s.scope == "buyer"] if fmt else [],
            "line_fields": [s.as_dict() for s in fmt.fields if s.scope == "line"] if fmt else [],
            "document_fields": [s.as_dict() for s in fmt.fields if s.scope == "document"] if fmt else [],
            "values": values,
            "fallbacks": {
                "name": getattr(tprofile, "legal_name", "") or "",
                "tax_id": getattr(tprofile, "vat_number", "") or "",
            },
            "transport_configured": bool(fmt and getattr(fmt.client(), "configured", False)),
            "signing_supported": bool(mode in NATIONAL_KEY_ENV),
            "signing_configured": bool(key_pem and cert_pem),
        }

    def get(self, request):
        return Response(self._payload(request.tenant_id))

    def put(self, request):
        _require_finance_role(request)
        tenant_id = request.tenant_id
        _country, _mode, fmt = _format_for(tenant_id)
        if fmt is None:
            raise ValidationError({"detail": "This tenant's country has no national e-invoicing format."})
        specs = [s for s in fmt.fields if s.scope == "seller"]
        cleaned, errors = _clean(specs, request.data.get("values") or {}, "seller")
        if errors:
            return Response({"detail": "Some e-invoicing fields are invalid.", "errors": errors}, status=400)
        ep, _ = EInvoiceProfile.objects.get_or_create(tenant_id=tenant_id)
        if "name" in cleaned:
            ep.legal_name = cleaned.pop("name")
        for core in EInvoiceProfile.CORE_FIELDS:
            if core in cleaned:
                setattr(ep, core, cleaned.pop(core))
        national = dict(ep.national or {})
        national.update(cleaned)
        ep.national = {k: v for k, v in national.items() if v != ""}
        ep.save()
        return Response(self._payload(tenant_id))

    # Partial by nature (only the sent keys change); the frontend REST proxy
    # forwards PATCH, not PUT.
    patch = put


class InvoiceEInvoiceView(APIView):
    """GET: the invoice's e-invoicing state + the buyer/line/document fields
    its format needs, with current values. PATCH: save those fields (onto
    the partner / lines / invoice attributes -- never amounts)."""

    permission_classes = [IsAuthenticatedViaClaims]

    def _invoice(self, request, pk):
        invoice = Invoice.objects.filter(pk=pk, tenant_id=request.tenant_id).select_related("partner").first()
        if invoice is None:
            from django.http import Http404
            raise Http404
        return invoice

    def _payload(self, invoice):
        country, mode, fmt = _format_for(invoice.tenant_id)
        partner_vals = dict((invoice.partner.attributes or {}).get(EINVOICE_ATTR, {}))
        buyer = national_doc_input(invoice, country).buyer if fmt else None
        buyer_values = {}
        if buyer:
            buyer_values = {k: getattr(buyer, k) for k in _BUYER_CORE}
            buyer_values.update(buyer.extra)
        buyer_values.update(partner_vals)
        interaction = (EInvoiceInteraction.objects
                       .filter(tenant_id=invoice.tenant_id, invoice_ref=invoice.number)
                       .exclude(document="").order_by("-created_at").first())
        return {
            "mode": invoice.einvoice_mode or mode,
            "mode_label": fmt.label if fmt else None,
            "is_national": fmt is not None,
            "status": invoice.einvoice_status,
            "reference": invoice.einvoice_reference,
            "response": invoice.einvoice_response,
            "cleared_at": invoice.einvoice_cleared_at,
            "has_document": interaction is not None,
            "document_filename": interaction.document_filename if interaction else "",
            "buyer_fields": [s.as_dict() for s in fmt.fields if s.scope == "buyer"] if fmt else [],
            "line_fields": [s.as_dict() for s in fmt.fields if s.scope == "line"] if fmt else [],
            "document_fields": [s.as_dict() for s in fmt.fields if s.scope == "document"] if fmt else [],
            "buyer_values": buyer_values,
            "document_values": dict((invoice.attributes or {}).get(EINVOICE_ATTR, {})),
            "lines": [
                {"id": str(ln.pk), "description": ln.description, "tax_percent": str(ln.tax_percent),
                 "values": dict((ln.attributes or {}).get(EINVOICE_ATTR, {}))}
                for ln in invoice.lines.all()
            ],
        }

    def get(self, request, pk):
        return Response(self._payload(self._invoice(request, pk)))

    def patch(self, request, pk):
        _require_finance_role(request)
        invoice = self._invoice(request, pk)
        if invoice.einvoice_status in ("cleared", "reported", "generated"):
            raise ValidationError({"detail": "This invoice's e-invoice was already issued; its data is locked."})
        _country, _mode, fmt = _format_for(invoice.tenant_id)
        if fmt is None:
            raise ValidationError({"detail": "No national e-invoicing format applies to this invoice."})
        # All-or-nothing: one bad field must not leave the others half-saved.
        with transaction.atomic():
            errors = self._apply_patch(request, invoice, fmt)
            if errors:
                transaction.set_rollback(True)
                return Response({"detail": "Some e-invoicing fields are invalid.", "errors": errors}, status=400)
        invoice.refresh_from_db()
        return Response(self._payload(invoice))

    def _apply_patch(self, request, invoice, fmt) -> list[dict]:
        errors: list[dict] = []
        buyer_specs = [s for s in fmt.fields if s.scope == "buyer"]
        if "buyer" in request.data:
            cleaned, errs = _clean(buyer_specs, request.data["buyer"], "buyer")
            errors += errs
            if not errs:
                partner = Partner.objects.get(pk=invoice.partner_id)
                attrs = dict(partner.attributes or {})
                merged = {**attrs.get(EINVOICE_ATTR, {}), **cleaned}
                attrs[EINVOICE_ATTR] = {k: v for k, v in merged.items() if v != ""}
                partner.attributes = attrs
                partner.save(update_fields=["attributes", "updated_at"])
        if "document" in request.data:
            cleaned, errs = _clean([s for s in fmt.fields if s.scope == "document"],
                                   request.data["document"], "document")
            errors += errs
            if not errs:
                attrs = dict(invoice.attributes or {})
                merged = {**attrs.get(EINVOICE_ATTR, {}), **cleaned}
                attrs[EINVOICE_ATTR] = {k: v for k, v in merged.items() if v != ""}
                invoice.attributes = attrs
                invoice.save(update_fields=["attributes", "updated_at"])
        line_specs = [s for s in fmt.fields if s.scope == "line"]
        for line_id, values in (request.data.get("lines") or {}).items():
            try:
                uuid.UUID(str(line_id))
                line = InvoiceLine.objects.filter(pk=line_id, invoice=invoice).first()
            except ValueError:
                line = None
            if line is None:
                errors.append({"scope": "line", "key": str(line_id), "message": "not a line of this invoice"})
                continue
            cleaned, errs = _clean(line_specs, values, f"line:{line_id}")
            errors += errs
            if not errs:
                attrs = dict(line.attributes or {})
                merged = {**attrs.get(EINVOICE_ATTR, {}), **cleaned}
                attrs[EINVOICE_ATTR] = {k: v for k, v in merged.items() if v != ""}
                line.attributes = attrs
                line.save(update_fields=["attributes", "updated_at"])
        return errors


class InvoiceEInvoiceRetryView(APIView):
    """Re-run e-invoicing for a posted invoice: rebuild after fixing missing
    data (incomplete / rejected), or transmit an already-generated document
    once a transport is configured (never rebuilt -- it has its progressive)."""

    permission_classes = [IsAuthenticatedViaClaims]

    def post(self, request, pk):
        _require_finance_role(request)
        invoice = Invoice.objects.filter(pk=pk, tenant_id=request.tenant_id).first()
        if invoice is None:
            from django.http import Http404
            raise Http404
        if invoice.status not in ("posted", "partial", "paid"):
            raise ValidationError({"detail": "Only a posted invoice is e-invoiced."})
        if invoice.invoice_type not in ("customer", "customer_credit_note"):
            raise ValidationError({"detail": "Only customer invoices and credit notes are e-invoiced."})
        if invoice.einvoice_status in ("cleared", "reported"):
            raise ValidationError({"detail": "Already accepted by the authority."})
        if invoice.einvoice_status == "generated":
            resubmit_generated(invoice)
        else:
            run_einvoice_clearance(invoice)
        invoice.refresh_from_db()
        return Response(InvoiceEInvoiceView()._payload(invoice))


class InvoiceEInvoiceDocumentView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request, pk):
        invoice = Invoice.objects.filter(pk=pk, tenant_id=request.tenant_id).first()
        if invoice is None:
            from django.http import Http404
            raise Http404
        interaction = (EInvoiceInteraction.objects
                       .filter(tenant_id=invoice.tenant_id, invoice_ref=invoice.number)
                       .exclude(document="").order_by("-created_at").first())
        if interaction is None:
            from django.http import Http404
            raise Http404
        resp = HttpResponse(interaction.document, content_type="application/xml; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{interaction.document_filename or "einvoice.xml"}"'
        return resp
