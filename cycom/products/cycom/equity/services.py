"""
Liquidation/dividend waterfall calculation.

IMPORTANT: this implements one well-known, standard waterfall algorithm
(seniority-ranked preference, then pro-rata participation), but real cap
tables can have deal-specific terms (caps on participation, multiple
liquidation triggers, complex anti-dilution) that this does not attempt
to model. Treat this as a real, working default — not a substitute for
legal/financial review before an actual distribution is paid out.
"""

from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from products.cycom.equity.models import DividendAllocation, DividendDistribution, ShareGrant


@transaction.atomic
def compute_waterfall(distribution: DividendDistribution) -> DividendDistribution:
    if distribution.status != "draft":
        raise ValidationError(f"Distribution must be 'draft' to compute, is '{distribution.status}'.")

    grants = list(
        ShareGrant.objects.filter(tenant_id=distribution.tenant_id).select_related("share_class", "shareholder")
    )
    as_of = distribution.distribution_date
    vested = [(g, g.vested_quantity(as_of)) for g in grants]
    vested = [(g, qty) for g, qty in vested if qty > 0]

    remaining = distribution.total_amount
    allocations = []

    # ── Step 1: liquidation preferences, seniority order ────────────────
    preferred_classes = sorted(
        {g.share_class for g, _ in vested if g.share_class.class_type == "preferred" and not g.share_class.convert_to_common},
        key=lambda c: c.seniority_rank,
    )
    for share_class in preferred_classes:
        class_grants = [(g, qty) for g, qty in vested if g.share_class_id == share_class.id]
        pref_amounts = {
            g.id: (qty * g.price_per_share * share_class.liquidation_preference_multiple).quantize(Decimal("0.01"))
            for g, qty in class_grants
        }
        class_total_pref = sum(pref_amounts.values())
        if class_total_pref <= 0:
            continue
        payout_ratio = min(Decimal("1"), remaining / class_total_pref) if class_total_pref else Decimal("0")
        for g, _qty in class_grants:
            pay = (pref_amounts[g.id] * payout_ratio).quantize(Decimal("0.01"))
            if pay > 0:
                allocations.append(
                    DividendAllocation(
                        tenant_id=distribution.tenant_id,
                        distribution=distribution,
                        shareholder=g.shareholder,
                        grant=g,
                        amount=pay,
                        basis="liquidation_preference",
                    )
                )
                remaining -= pay

    # ── Step 2: pro-rata participation pool ──────────────────────────────
    # Common shares, participating preferred (as-converted), and any class
    # that manually elected convert_to_common all share what's left.
    pool = []
    for g, qty in vested:
        sc = g.share_class
        if sc.class_type == "common":
            pool.append((g, qty))
        elif sc.convert_to_common:
            pool.append((g, qty * sc.conversion_ratio))
        elif sc.is_participating:
            pool.append((g, qty * sc.conversion_ratio))

    total_pool_units = sum(units for _g, units in pool)
    if remaining > 0 and total_pool_units > 0:
        for g, units in pool:
            share = (remaining * units / total_pool_units).quantize(Decimal("0.01"))
            if share > 0:
                allocations.append(
                    DividendAllocation(
                        tenant_id=distribution.tenant_id,
                        distribution=distribution,
                        shareholder=g.shareholder,
                        grant=g,
                        amount=share,
                        basis="pro_rata",
                    )
                )

    DividendAllocation.objects.bulk_create(allocations)
    distribution.status = "computed"
    distribution.save(update_fields=["status", "updated_at"])
    return distribution


def mark_paid(distribution: DividendDistribution) -> DividendDistribution:
    if distribution.status != "computed":
        raise ValidationError(f"Distribution must be 'computed' to mark paid, is '{distribution.status}'.")
    distribution.status = "paid"
    distribution.save(update_fields=["status", "updated_at"])
    return distribution
