import datetime
import uuid
from decimal import Decimal

import pytest

from products.cymart.pantry.models import PantryItem, PurchaseHistory
from products.cymart.pantry.services import ReplenishEngine


@pytest.mark.django_db
class TestReplenishEngine:
    def test_first_purchase_has_no_prediction_yet(self):
        engine = ReplenishEngine()
        customer_id, product_id = uuid.uuid4(), uuid.uuid4()
        item = engine.record_purchase(customer_id, product_id, Decimal("2"), unit="L",
                                      product_name="Milk", purchased_at=datetime.date(2026, 9, 1))
        assert item.typical_interval_days is None
        assert item.predicted_runout_date is None
        assert PurchaseHistory.objects.count() == 1

    def test_second_purchase_learns_interval_and_predicts_runout(self):
        engine = ReplenishEngine()
        customer_id, product_id = uuid.uuid4(), uuid.uuid4()
        engine.record_purchase(customer_id, product_id, Decimal("2"), unit="L",
                               product_name="Milk", purchased_at=datetime.date(2026, 9, 1))
        item = engine.record_purchase(customer_id, product_id, Decimal("2"), unit="L",
                                      product_name="Milk", purchased_at=datetime.date(2026, 9, 8))
        assert item.typical_interval_days == 7
        assert item.predicted_runout_date == datetime.date(2026, 9, 15)

    def test_interval_blends_with_rolling_average(self):
        engine = ReplenishEngine()
        customer_id, product_id = uuid.uuid4(), uuid.uuid4()
        dates = [
            datetime.date(2026, 9, 1), datetime.date(2026, 9, 8),
            datetime.date(2026, 9, 15),  # interval 7,7 -> stays 7
        ]
        for d in dates:
            item = engine.record_purchase(customer_id, product_id, Decimal("2"), purchased_at=d)
        assert item.typical_interval_days == 7

        # a much shorter gap should pull the average down, not snap to it
        item = engine.record_purchase(customer_id, product_id, Decimal("2"),
                                      purchased_at=datetime.date(2026, 9, 18))
        assert 3 < item.typical_interval_days < 7

    def test_due_for_replenish_finds_items_near_runout(self):
        engine = ReplenishEngine()
        customer_id, product_id = uuid.uuid4(), uuid.uuid4()
        engine.record_purchase(customer_id, product_id, Decimal("1"),
                               purchased_at=datetime.date(2026, 9, 1))
        engine.record_purchase(customer_id, product_id, Decimal("1"),
                               purchased_at=datetime.date(2026, 9, 8))
        # predicted runout = Sep 15; "today" = Sep 15 -> due
        due = list(engine.due_for_replenish(customer_id, as_of=datetime.date(2026, 9, 15)))
        assert len(due) == 1
        assert due[0].product_id == product_id

    def test_not_due_when_far_from_runout(self):
        engine = ReplenishEngine()
        customer_id, product_id = uuid.uuid4(), uuid.uuid4()
        engine.record_purchase(customer_id, product_id, Decimal("1"),
                               purchased_at=datetime.date(2026, 9, 1))
        engine.record_purchase(customer_id, product_id, Decimal("1"),
                               purchased_at=datetime.date(2026, 9, 8))
        due = list(engine.due_for_replenish(customer_id, as_of=datetime.date(2026, 9, 9)))
        assert due == []

    def test_build_refill_basket_repeats_last_quantity(self):
        engine = ReplenishEngine()
        customer_id, product_id = uuid.uuid4(), uuid.uuid4()
        engine.record_purchase(customer_id, product_id, Decimal("2"), unit="L",
                               product_name="Milk", purchased_at=datetime.date(2026, 9, 1))
        engine.record_purchase(customer_id, product_id, Decimal("3"), unit="L",
                               product_name="Milk", purchased_at=datetime.date(2026, 9, 8))
        basket = engine.build_refill_basket(customer_id, as_of=datetime.date(2026, 9, 15))
        assert basket[0]["quantity"] == Decimal("3")
        assert basket[0]["unit"] == "L"

    def test_only_one_pantry_item_per_customer_product(self):
        engine = ReplenishEngine()
        customer_id, product_id = uuid.uuid4(), uuid.uuid4()
        for _ in range(3):
            engine.record_purchase(customer_id, product_id, Decimal("1"))
        assert PantryItem.objects.filter(customer_id=customer_id, product_id=product_id).count() == 1
