from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import crud
from app.core.audit import log_action
from app.core.dependencies import get_current_company_id, require_permission
from app.db.session import get_db
from app.models.inventory import StockLevel, StockMove, StockTransfer, Warehouse
from app.models.user import User
from app.schemas.inventory import (
    StockLevelResponse,
    StockMoveResponse,
    StockTransferCreate,
    StockTransferResponse,
    StockTransferUpdate,
    WarehouseCreate,
    WarehouseResponse,
)

router = APIRouter()


def _next_reference(db: Session, cid: int) -> str:
    n = db.query(StockTransfer).filter(StockTransfer.company_id == cid).count() + 1
    return f"WH-TR-{n:04d}"


def _apply_move(db: Session, cid: int, warehouse_id: int, product_id: int, qty: Decimal, reason: str, doc_type: str, doc_id: int) -> None:
    level = (
        db.query(StockLevel)
        .filter(
            StockLevel.company_id == cid,
            StockLevel.warehouse_id == warehouse_id,
            StockLevel.product_id == product_id,
        )
        .first()
    )
    if not level:
        level = StockLevel(
            company_id=cid, warehouse_id=warehouse_id, product_id=product_id, quantity=Decimal("0")
        )
        db.add(level)
        db.flush()
    level.quantity = level.quantity + qty
    db.add(
        StockMove(
            company_id=cid,
            warehouse_id=warehouse_id,
            product_id=product_id,
            quantity=qty,
            reason=reason,
            source_doc_type=doc_type,
            source_doc_id=doc_id,
            moved_at=datetime.now(timezone.utc),
        )
    )


# ---------- Warehouses ----------
@router.get("/warehouses", response_model=List[WarehouseResponse])
def list_warehouses(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inventory.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, Warehouse, cid)


@router.post("/warehouses", response_model=WarehouseResponse)
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inventory.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(db, Warehouse, cid, payload.model_dump(), created_by_id=user.id)


# ---------- Stock levels ----------
@router.get("/levels", response_model=List[StockLevelResponse])
def list_levels(
    warehouse_id: Optional[int] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inventory.read")),
    cid: int = Depends(get_current_company_id),
):
    q = db.query(StockLevel).filter(StockLevel.company_id == cid)
    if warehouse_id:
        q = q.filter(StockLevel.warehouse_id == warehouse_id)
    if product_id:
        q = q.filter(StockLevel.product_id == product_id)
    return q.all()


# ---------- Stock transfers ----------
@router.get("/transfers", response_model=List[StockTransferResponse])
def list_transfers(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inventory.read")),
    cid: int = Depends(get_current_company_id),
):
    return (
        db.query(StockTransfer)
        .filter(StockTransfer.company_id == cid)
        .order_by(StockTransfer.id.desc())
        .limit(500)
        .all()
    )


@router.post("/transfers", response_model=StockTransferResponse)
def dispatch_transfer(
    payload: StockTransferCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inventory.write")),
    cid: int = Depends(get_current_company_id),
):
    # Negative-stock guard
    src_level = (
        db.query(StockLevel)
        .filter(
            StockLevel.company_id == cid,
            StockLevel.warehouse_id == payload.source_warehouse_id,
            StockLevel.product_id == payload.product_id,
        )
        .first()
    )
    available = src_level.quantity if src_level else Decimal("0")
    if available < payload.sent_qty:
        raise HTTPException(
            status_code=400, detail=f"Insufficient stock: have {available}, need {payload.sent_qty}"
        )

    transfer = StockTransfer(
        company_id=cid,
        reference=_next_reference(db, cid),
        source_warehouse_id=payload.source_warehouse_id,
        destination_warehouse_id=payload.destination_warehouse_id,
        product_id=payload.product_id,
        sent_qty=payload.sent_qty,
        status="Dispatched",
        dispatched_at=datetime.now(timezone.utc),
        created_by_id=user.id,
    )
    db.add(transfer)
    db.flush()

    _apply_move(
        db, cid, payload.source_warehouse_id, payload.product_id, -payload.sent_qty,
        "transfer_out", "StockTransfer", transfer.id,
    )

    db.commit()
    db.refresh(transfer)
    log_action(db, user=user, action="dispatch", entity_type="StockTransfer", entity_id=transfer.id)
    return transfer


@router.put("/transfers/{obj_id}/receive", response_model=StockTransferResponse)
def receive_transfer(
    obj_id: int,
    payload: StockTransferUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inventory.write")),
    cid: int = Depends(get_current_company_id),
):
    t = crud.get_for_company(db, StockTransfer, cid, obj_id)
    if t.status not in ("Dispatched",):
        raise HTTPException(status_code=400, detail=f"Cannot receive in status {t.status}")
    if payload.received_qty is None:
        raise HTTPException(status_code=400, detail="received_qty is required")

    t.received_qty = payload.received_qty
    t.received_at = datetime.now(timezone.utc)
    if payload.received_qty == t.sent_qty:
        t.status = "Resolved"
    else:
        t.status = "Discrepancy"
        t.discrepancy_reason = payload.discrepancy_reason or "Quantity mismatch"

    _apply_move(
        db, cid, t.destination_warehouse_id, t.product_id, payload.received_qty,
        "transfer_in", "StockTransfer", t.id,
    )

    db.commit()
    db.refresh(t)
    log_action(db, user=user, action="receive", entity_type="StockTransfer", entity_id=t.id)
    return t


# ---------- Stock moves (read-only) ----------
@router.get("/moves", response_model=List[StockMoveResponse])
def list_moves(
    warehouse_id: Optional[int] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inventory.read")),
    cid: int = Depends(get_current_company_id),
):
    q = db.query(StockMove).filter(StockMove.company_id == cid)
    if warehouse_id:
        q = q.filter(StockMove.warehouse_id == warehouse_id)
    if product_id:
        q = q.filter(StockMove.product_id == product_id)
    return q.order_by(StockMove.moved_at.desc()).limit(500).all()
