from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class _M(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class WarehouseBase(BaseModel):
    name: str
    code: str
    address: Optional[str] = None


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseResponse(_M, WarehouseBase):
    id: int
    company_id: int


class StockLevelResponse(_M):
    id: int
    warehouse_id: int
    product_id: int
    quantity: Decimal


class StockTransferCreate(BaseModel):
    source_warehouse_id: int
    destination_warehouse_id: int
    product_id: int
    sent_qty: Decimal


class StockTransferUpdate(BaseModel):
    received_qty: Optional[Decimal] = None
    status: Optional[str] = None
    discrepancy_reason: Optional[str] = None


class StockTransferResponse(_M):
    id: int
    reference: str
    company_id: int
    source_warehouse_id: int
    destination_warehouse_id: int
    product_id: int
    sent_qty: Decimal
    received_qty: Decimal
    status: str
    discrepancy_reason: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    received_at: Optional[datetime] = None


class StockMoveResponse(_M):
    id: int
    warehouse_id: int
    product_id: int
    quantity: Decimal
    reason: str
    source_doc_type: Optional[str] = None
    source_doc_id: Optional[int] = None
    moved_at: datetime
