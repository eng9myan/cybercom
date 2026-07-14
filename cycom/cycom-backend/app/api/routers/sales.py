from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import crud
from app.core.audit import log_action
from app.core.dependencies import get_current_company_id, require_permission
from app.db.session import get_db
from app.models.sales import DiscountException, SalesOrder, SalesOrderLine
from app.models.user import User
from app.schemas.sales import (
    DiscountExceptionCreate,
    DiscountExceptionResponse,
    DiscountExceptionUpdate,
    SalesOrderCreate,
    SalesOrderResponse,
    SalesOrderUpdate,
)

router = APIRouter()

APPROVAL_THRESHOLD = Decimal("3000")


def _next_so_ref(db: Session, cid: int) -> str:
    n = db.query(SalesOrder).filter(SalesOrder.company_id == cid).count() + 1
    return f"SO-{1000 + n}"


@router.get("/orders", response_model=List[SalesOrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("sales.read")),
    cid: int = Depends(get_current_company_id),
):
    return (
        db.query(SalesOrder)
        .filter(SalesOrder.company_id == cid)
        .order_by(SalesOrder.id.desc())
        .limit(500)
        .all()
    )


@router.post("/orders", response_model=SalesOrderResponse)
def create_order(
    payload: SalesOrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("sales.write")),
    cid: int = Depends(get_current_company_id),
):
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
    status = "Pending Approval" if total > APPROVAL_THRESHOLD else "Draft"

    order = SalesOrder(
        company_id=cid,
        reference=_next_so_ref(db, cid),
        partner_id=payload.partner_id,
        order_date=payload.order_date,
        delivery_date=payload.delivery_date,
        subtotal=subtotal,
        tax_total=tax_total,
        total=total,
        status=status,
        created_by_id=user.id,
    )
    db.add(order)
    db.flush()

    for line in payload.lines:
        gross = line.quantity * line.unit_price
        discount = gross * line.discount_pct / Decimal("100")
        net = gross - discount
        db.add(
            SalesOrderLine(
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
    log_action(db, user=user, action="create", entity_type="SalesOrder", entity_id=order.id)
    return order


@router.get("/orders/{obj_id}", response_model=SalesOrderResponse)
def get_order(
    obj_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("sales.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.get_for_company(db, SalesOrder, cid, obj_id)


@router.put("/orders/{obj_id}", response_model=SalesOrderResponse)
def update_order(
    obj_id: int,
    payload: SalesOrderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("sales.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.update_for_company(
        db, SalesOrder, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )


# ---------- Discount exceptions ----------
@router.get("/discount-exceptions", response_model=List[DiscountExceptionResponse])
def list_exceptions(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("sales.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, DiscountException, cid)


@router.post("/discount-exceptions", response_model=DiscountExceptionResponse)
def create_exception(
    payload: DiscountExceptionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("sales.write")),
    cid: int = Depends(get_current_company_id),
):
    if payload.discount_pct <= payload.allowed_limit_pct:
        raise HTTPException(
            status_code=400, detail="Discount is within allowed limit — no exception needed"
        )
    return crud.create_for_company(
        db, DiscountException, cid, payload.model_dump(), created_by_id=user.id
    )


@router.put("/discount-exceptions/{obj_id}", response_model=DiscountExceptionResponse)
def update_exception(
    obj_id: int,
    payload: DiscountExceptionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("sales.approve")),
    cid: int = Depends(get_current_company_id),
):
    if payload.status not in ("approved", "rejected", "pending"):
        raise HTTPException(status_code=400, detail="Invalid status")
    obj = crud.get_for_company(db, DiscountException, cid, obj_id)
    obj.status = payload.status
    if payload.status == "approved":
        obj.approved_by_id = user.id
        so = db.query(SalesOrder).filter(SalesOrder.id == obj.order_id).first()
        if so:
            so.status = "Confirmed"
    db.commit()
    db.refresh(obj)
    log_action(db, user=user, action=payload.status, entity_type="DiscountException", entity_id=obj.id)
    return obj
