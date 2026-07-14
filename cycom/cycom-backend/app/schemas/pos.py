from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class _M(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PosSessionOpen(BaseModel):
    opening_float: Decimal = Decimal("0")


class PosSessionClose(BaseModel):
    closing_amount: Decimal


class PosSessionResponse(_M):
    id: int
    reference: str
    company_id: int
    opened_at: datetime
    closed_at: Optional[datetime] = None
    opening_float: Decimal
    closing_amount: Optional[Decimal] = None
    operator_id: Optional[int] = None
    status: str


class PosOrderLineCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    discount_pct: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")


class PosOrderLineResponse(_M, PosOrderLineCreate):
    id: int
    subtotal: Decimal


class PosOrderCreate(BaseModel):
    session_id: int
    customer_name: str = "Walk-in Customer"
    partner_id: Optional[int] = None
    payment_method: str = "cash"
    tendered: Decimal = Decimal("0")
    order_type: str = "standard"
    deposit: Decimal = Decimal("0")
    deadline_date: Optional[datetime] = None
    lines: List[PosOrderLineCreate]


class PosOrderResponse(_M):
    id: int
    reference: str
    company_id: int
    session_id: int
    customer_name: str
    partner_id: Optional[int] = None
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    payment_method: str
    tendered: Decimal
    change: Decimal
    order_type: str
    deposit: Decimal
    deadline_date: Optional[datetime] = None
    status: str


class PosCashMoveCreate(BaseModel):
    session_id: int
    move_type: str  # Cash-In | Cash-Out
    amount: Decimal
    reason: str


class PosCashMoveResponse(_M, PosCashMoveCreate):
    id: int
    company_id: int
    timestamp: datetime
