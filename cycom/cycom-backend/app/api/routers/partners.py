from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import crud
from app.core.dependencies import get_current_company_id, require_permission
from app.db.session import get_db
from app.models.partner import Partner
from app.models.user import User
from app.schemas.partner import PartnerCreate, PartnerResponse, PartnerUpdate

router = APIRouter()


@router.get("/", response_model=List[PartnerResponse])
def list_partners(
    is_customer: Optional[bool] = None,
    is_vendor: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("partners.read")),
    cid: int = Depends(get_current_company_id),
):
    q = db.query(Partner).filter(Partner.company_id == cid, Partner.is_active.is_(True))
    if is_customer is not None:
        q = q.filter(Partner.is_customer == is_customer)
    if is_vendor is not None:
        q = q.filter(Partner.is_vendor == is_vendor)
    return q.all()


@router.post("/", response_model=PartnerResponse)
def create_partner(
    payload: PartnerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("partners.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(db, Partner, cid, payload.model_dump(), created_by_id=user.id)


@router.get("/{obj_id}", response_model=PartnerResponse)
def get_partner(
    obj_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("partners.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.get_for_company(db, Partner, cid, obj_id)


@router.put("/{obj_id}", response_model=PartnerResponse)
def update_partner(
    obj_id: int,
    payload: PartnerUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("partners.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.update_for_company(
        db, Partner, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )


@router.delete("/{obj_id}")
def delete_partner(
    obj_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("partners.write")),
    cid: int = Depends(get_current_company_id),
):
    crud.soft_delete_for_company(db, Partner, cid, obj_id)
    return {"ok": True}
