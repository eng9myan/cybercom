from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class _M(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SalesOrderLineCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    discount_pct: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")


class SalesOrderLineResponse(_M, SalesOrderLineCreate):
    id: int
    subtotal: Decimal


class SalesOrderCreate(BaseModel):
    partner_id: int
    order_date: date
    delivery_date: Optional[date] = None
    lines: List[SalesOrderLineCreate]


class SalesOrderUpdate(BaseModel):
    status: Optional[str] = None
    delivery_date: Optional[date] = None


class SalesOrderResponse(_M):
    id: int
    reference: str
    company_id: int
    partner_id: int
    order_date: date
    delivery_date: Optional[date] = None
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    status: str


class DiscountExceptionCreate(BaseModel):
    order_id: int
    product_id: int
    standard_price: Decimal
    offered_price: Decimal
    discount_pct: Decimal
    allowed_limit_pct: Decimal


class DiscountExceptionUpdate(BaseModel):
    status: str  # pending|approved|rejected


class DiscountExceptionResponse(_M, DiscountExceptionCreate):
    id: int
    company_id: int
    status: str
