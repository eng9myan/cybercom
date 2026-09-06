from django.contrib import admin

from .models import EInvoiceDocument, Invoice, InvoiceLine, TaxProfile


class _RO(admin.ModelAdmin):
    def has_add_permission(self, r): return False
    def has_change_permission(self, r, o=None): return False
    def has_delete_permission(self, r, o=None): return False


@admin.register(TaxProfile)
class TaxProfileAdmin(admin.ModelAdmin):
    list_display = ("legal_name", "scheme", "vat_number", "country_code")
    list_filter = ("scheme", "country_code")


@admin.register(Invoice)
class InvoiceAdmin(_RO):
    list_display = ("number", "customer_name", "invoice_type", "status", "issue_date",
                    "subtotal", "tax_total", "total", "currency")
    list_filter = ("status", "invoice_type", "currency")
    search_fields = ("number", "customer_name")


@admin.register(EInvoiceDocument)
class EInvoiceDocumentAdmin(_RO):
    list_display = ("invoice", "scheme", "status", "icv", "submitted_at", "cleared_at")
    list_filter = ("scheme", "status")


admin.site.register(InvoiceLine, _RO)
