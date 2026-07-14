from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class _M(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderLineCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    tax_rate: Decimal = Decimal("0")


class PurchaseOrderLineResponse(_M, PurchaseOrderLineCreate):
    id: int
    subtotal: Decimal


class PurchaseOrderCreate(BaseModel):
    vendor_id: int
    order_date: date
    expected_date: Optional[date] = None
    lines: List[PurchaseOrderLineCreate]


class PurchaseOrderUpdate(BaseModel):
    status: Optional[str] = None
    expected_date: Optional[date] = None


class PurchaseOrderResponse(_M):
    id: int
    reference: str
    company_id: int
    vendor_id: int
    order_date: date
    expected_date: Optional[date] = None
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    status: str
