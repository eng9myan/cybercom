"""
Subscription Service — lifecycle management for CyMed subscriptions.
"""
import uuid
from datetime import date
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from products.cymed.commercial.subscriptions.models import (
    Subscription, SubscriptionPlan, SubscriptionUsage, SubscriptionInvoice
)


class SubscriptionService:

    CYCLE_MONTHS = {
        "monthly": 1,
        "quarterly": 3,
        "annual": 12,
        "multi_year": 36,
        "enterprise": 12,
    }

    @classmethod
    def create_subscription(
        cls,
        plan: SubscriptionPlan,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        started_at: date = None,
        contracted_users: int = 0,
        contracted_beds: int = 0,
        license_id: uuid.UUID = None,
    ) -> Subscription:
        today = started_at or timezone.now().date()
        months = cls.CYCLE_MONTHS.get(plan.billing_cycle, 12)
        period_end = today + relativedelta(months=months) - relativedelta(days=1)

        return Subscription.objects.create(
            tenant_id=tenant_id,
            plan=plan,
            customer_id=customer_id,
            license_id=license_id,
            status="active",
            started_at=today,
            current_period_start=today,
            current_period_end=period_end,
            contracted_users=contracted_users,
            contracted_beds=contracted_beds,
        )

    @classmethod
    def renew_subscription(cls, subscription: Subscription) -> Subscription:
        months = cls.CYCLE_MONTHS.get(subscription.plan.billing_cycle, 12)
        new_start = subscription.current_period_end + relativedelta(days=1)
        new_end = new_start + relativedelta(months=months) - relativedelta(days=1)
        subscription.current_period_start = new_start
        subscription.current_period_end = new_end
        subscription.status = "active"
        subscription.save()
        return subscription

    @classmethod
    def generate_invoice(cls, subscription: Subscription) -> SubscriptionInvoice:
        plan = subscription.plan
        from decimal import Decimal
        base = Decimal(str(plan.base_price))
        overage = Decimal("0")
        if plan.per_user_price and subscription.contracted_users:
            base += Decimal(str(plan.per_user_price)) * subscription.contracted_users
        if plan.per_bed_price and subscription.contracted_beds:
            base += Decimal(str(plan.per_bed_price)) * subscription.contracted_beds

        invoice_number = f"INV-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"
        return SubscriptionInvoice.objects.create(
            tenant_id=subscription.tenant_id,
            subscription=subscription,
            invoice_number=invoice_number,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            base_amount=base,
            overage_amount=overage,
            total_amount=base + overage,
            currency=plan.currency,
            status="draft",
            due_date=subscription.current_period_start + relativedelta(days=30),
        )
