from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import crud
from app.core.audit import log_action
from app.core.dependencies import get_current_company_id, require_permission
from app.db.session import get_db
from app.models.purchase import PurchaseOrder, PurchaseOrderLine
from app.models.user import User
from app.schemas.purchase import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
)

router = APIRouter()


def _next_po_ref(db: Session, cid: int) -> str:
    n = db.query(PurchaseOrder).filter(PurchaseOrder.company_id == cid).count() + 1
    return f"PO-{1000 + n}"


@router.get("/orders", response_model=List[PurchaseOrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("purchase.read")),
    cid: int = Depends(get_current_company_id),
):
    return (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.company_id == cid)
        .order_by(PurchaseOrder.id.desc())
        .limit(500)
        .all()
    )


@router.post("/orders", response_model=PurchaseOrderResponse)
def create_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("purchase.write")),
    cid: int = Depends(get_current_company_id),
):
    subtotal = Decimal("0")
    tax_total = Decimal("0")
    for line in payload.lines:
        net = line.quantity * line.unit_price
        tax = (net * line.tax_rate).quantize(Decimal("0.01"))
        subtotal += net
        tax_total += tax

    order = PurchaseOrder(
        company_id=cid,
        reference=_next_po_ref(db, cid),
        vendor_id=payload.vendor_id,
        order_date=payload.order_date,
        expected_date=payload.expected_date,
        subtotal=subtotal,
        tax_total=tax_total,
        total=subtotal + tax_total,
        status="RFQ",
        created_by_id=user.id,
    )
    db.add(order)
    db.flush()

    for line in payload.lines:
        net = line.quantity * line.unit_price
        db.add(
            PurchaseOrderLine(
                company_id=cid,
                order_id=order.id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                tax_rate=line.tax_rate,
                subtotal=net,
            )
        )

    db.commit()
    db.refresh(order)
    log_action(db, user=user, action="create", entity_type="PurchaseOrder", entity_id=order.id)
    return order


@router.get("/orders/{obj_id}", response_model=PurchaseOrderResponse)
def get_order(
    obj_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("purchase.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.get_for_company(db, PurchaseOrder, cid, obj_id)


@router.put("/orders/{obj_id}", response_model=PurchaseOrderResponse)
def update_order(
    obj_id: int,
    payload: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("purchase.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.update_for_company(
        db, PurchaseOrder, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )
