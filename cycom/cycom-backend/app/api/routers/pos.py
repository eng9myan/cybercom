from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import crud
from app.core.audit import log_action
from app.core.dependencies import get_current_company_id, require_permission
from app.db.session import get_db
from app.models.pos import PosCashMove, PosOrder, PosOrderLine, PosSession
from app.models.user import User
from app.schemas.pos import (
    PosCashMoveCreate,
    PosCashMoveResponse,
    PosOrderCreate,
    PosOrderResponse,
    PosSessionClose,
    PosSessionOpen,
    PosSessionResponse,
)

router = APIRouter()


def _next_session_ref(db: Session, cid: int) -> str:
    n = db.query(PosSession).filter(PosSession.company_id == cid).count() + 1
    today = datetime.now(timezone.utc)
    return f"POS-SESS/{today.year}-{today.month:02d}-{n:03d}"


def _next_order_ref(db: Session, cid: int) -> str:
    n = db.query(PosOrder).filter(PosOrder.company_id == cid).count() + 1
    return f"POS-{1000 + n}"


# ---------- Sessions ----------
@router.post("/sessions/open", response_model=PosSessionResponse)
def open_session(
    payload: PosSessionOpen,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pos.write")),
    cid: int = Depends(get_current_company_id),
):
    open_session = (
        db.query(PosSession)
        .filter(PosSession.company_id == cid, PosSession.status == "Open", PosSession.operator_id == user.id)
        .first()
    )
    if open_session:
        raise HTTPException(status_code=400, detail="An open session already exists for this operator")

    session = PosSession(
        company_id=cid,
        reference=_next_session_ref(db, cid),
        opened_at=datetime.now(timezone.utc),
        opening_float=payload.opening_float,
        operator_id=user.id,
        status="Open",
        created_by_id=user.id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    log_action(db, user=user, action="open", entity_type="PosSession", entity_id=session.id)
    return session


@router.get("/sessions", response_model=List[PosSessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pos.read")),
    cid: int = Depends(get_current_company_id),
):
    return (
        db.query(PosSession)
        .filter(PosSession.company_id == cid)
        .order_by(PosSession.id.desc())
        .limit(100)
        .all()
    )


@router.put("/sessions/{obj_id}/close", response_model=PosSessionResponse)
def close_session(
    obj_id: int,
    payload: PosSessionClose,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pos.write")),
    cid: int = Depends(get_current_company_id),
):
    s = crud.get_for_company(db, PosSession, cid, obj_id)
    if s.status != "Open":
        raise HTTPException(status_code=400, detail="Session is not open")
    s.status = "Closed"
    s.closing_amount = payload.closing_amount
    s.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(s)
    log_action(db, user=user, action="close", entity_type="PosSession", entity_id=s.id)
    return s


# ---------- Orders ----------
@router.post("/orders", response_model=PosOrderResponse)
def create_order(
    payload: PosOrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pos.write")),
    cid: int = Depends(get_current_company_id),
):
    session = crud.get_for_company(db, PosSession, cid, payload.session_id)
    if session.status != "Open":
        raise HTTPException(status_code=400, detail="Session is closed")

    subtotal = Decimal("0")
    tax_total = Decimal("0")
    for line in payload.lines:
        gross = line.quantity * line.unit_price
        discount = gross * line.discount_pct / Decimal("100")
        net = gross - discount
        tax = (net * line.tax_rate).quantize(Decimal("0.01"))
        subtotal += net
        tax_total += tax
    total = subtotal + tax_total
    change = max(Decimal("0"), payload.tendered - total)

    order = PosOrder(
        company_id=cid,
        session_id=payload.session_id,
        reference=_next_order_ref(db, cid),
        customer_name=payload.customer_name,
        partner_id=payload.partner_id,
        subtotal=subtotal,
        tax_total=tax_total,
        total=total,
        payment_method=payload.payment_method,
        tendered=payload.tendered,
        change=change,
        order_type=payload.order_type,
        deposit=payload.deposit,
        deadline_date=payload.deadline_date,
        status="Paid" if payload.order_type == "standard" else "Pending",
        created_by_id=user.id,
    )
    db.add(order)
    db.flush()
    for line in payload.lines:
        gross = line.quantity * line.unit_price
        discount = gross * line.discount_pct / Decimal("100")
        net = gross - discount
        db.add(
            PosOrderLine(
                company_id=cid,
                order_id=order.id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_pct=line.discount_pct,
                tax_rate=line.tax_rate,
                subtotal=net,
            )
        )
    db.commit()
    db.refresh(order)
    log_action(db, user=user, action="create", entity_type="PosOrder", entity_id=order.id)
    return order


@router.get("/orders", response_model=List[PosOrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pos.read")),
    cid: int = Depends(get_current_company_id),
):
    return (
        db.query(PosOrder)
        .filter(PosOrder.company_id == cid)
        .order_by(PosOrder.id.desc())
        .limit(500)
        .all()
    )


# ---------- Cash moves ----------
@router.post("/cash-moves", response_model=PosCashMoveResponse)
def add_cash_move(
    payload: PosCashMoveCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pos.write")),
    cid: int = Depends(get_current_company_id),
):
    if payload.move_type not in ("Cash-In", "Cash-Out"):
        raise HTTPException(status_code=400, detail="Invalid move type")
    move = PosCashMove(
        company_id=cid,
        session_id=payload.session_id,
        move_type=payload.move_type,
        amount=payload.amount,
        reason=payload.reason,
        timestamp=datetime.now(timezone.utc),
        created_by_id=user.id,
    )
    db.add(move)
    db.commit()
    db.refresh(move)
    return move


@router.get("/cash-moves", response_model=List[PosCashMoveResponse])
def list_cash_moves(
    session_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pos.read")),
    cid: int = Depends(get_current_company_id),
):
    q = db.query(PosCashMove).filter(PosCashMove.company_id == cid)
    if session_id:
        q = q.filter(PosCashMove.session_id == session_id)
    return q.order_by(PosCashMove.id.desc()).limit(500).all()
