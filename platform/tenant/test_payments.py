"""Payment seam + activation-path tests (provider-agnostic subscription billing)."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, override_settings

from platform.tenant.models import (
    InvoiceStatus,
    SubscriptionPlan,
    Tenant,
    TenantStatus,
    TenantSubscription,
    TenantSubscriptionInvoice,
    TenantType,
)
from platform.tenant.payments import (
    ManualBankTransferProvider,
    WebhookVerificationError,
    get_payment_provider,
)
from platform.tenant.services import activate_paid_subscription


def _make_invoice(provider="manual"):
    suffix = uuid.uuid4().hex[:8]
    tenant = Tenant.objects.create(
        name=f"Acme {suffix}", slug=f"acme-{suffix}",
        tenant_type=TenantType.SAAS, status=TenantStatus.PENDING,
    )
    sub = TenantSubscription.objects.create(
        tenant=tenant, plan=SubscriptionPlan.PROFESSIONAL, is_active=False,
    )
    inv = TenantSubscriptionInvoice.objects.create(
        subscription=sub, invoice_number=f"INV-{suffix}", amount=Decimal("149.00"),
        currency="USD", due_date=date.today() + timedelta(days=7),
        status=InvoiceStatus.PENDING, provider=provider,
    )
    return tenant, sub, inv


class ActivationPathTests(TestCase):
    def test_payment_activates_tenant_and_marks_invoice_paid(self):
        tenant, sub, inv = _make_invoice()
        self.assertEqual(tenant.status, TenantStatus.PENDING)

        activate_paid_subscription(inv, approved_by="test")

        inv.refresh_from_db(); tenant.refresh_from_db(); sub.refresh_from_db()
        self.assertEqual(inv.status, InvoiceStatus.PAID)
        self.assertIsNotNone(inv.paid_at)
        self.assertEqual(tenant.status, TenantStatus.ACTIVE)
        self.assertTrue(sub.is_active)

    def test_activation_is_idempotent(self):
        _, _, inv = _make_invoice()
        activate_paid_subscription(inv, approved_by="first")
        # A webhook retry must not error or double-activate.
        tenant = activate_paid_subscription(inv, approved_by="second")
        self.assertEqual(tenant.status, TenantStatus.ACTIVE)


class ManualProviderTests(TestCase):
    def test_manual_checkout_returns_bank_instructions(self):
        _, _, inv = _make_invoice()
        checkout = ManualBankTransferProvider().create_checkout(inv).as_dict()
        self.assertEqual(checkout["mode"], "manual")
        self.assertEqual(checkout["instructions"]["reference"], inv.invoice_number)
        self.assertEqual(checkout["instructions"]["amount"], "149.00")


@override_settings(DEBUG=True, PAYMENT_PROVIDER="fake")
class FakeProviderTests(TestCase):
    def test_signed_webhook_confirms_payment(self):
        _, _, inv = _make_invoice(provider="fake")
        prov = get_payment_provider("fake")
        body = ('{"invoice_number": "%s", "status": "paid", "ref": "r1"}' % inv.invoice_number).encode()
        event = prov.parse_webhook(body=body, headers={"X-Fake-Signature": prov.sign(inv.invoice_number)})
        self.assertTrue(event.paid)
        self.assertEqual(event.invoice_number, inv.invoice_number)

    def test_bad_signature_rejected(self):
        _, _, inv = _make_invoice(provider="fake")
        prov = get_payment_provider("fake")
        body = ('{"invoice_number": "%s", "status": "paid"}' % inv.invoice_number).encode()
        with self.assertRaises(WebhookVerificationError):
            prov.parse_webhook(body=body, headers={"X-Fake-Signature": "deadbeef"})
