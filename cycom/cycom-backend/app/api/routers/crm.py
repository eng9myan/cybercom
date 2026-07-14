from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import crud
from app.core.dependencies import get_current_company_id, require_permission
from app.db.session import get_db
from app.models.crm import Activity, Lead, Opportunity
from app.models.user import User
from app.schemas.crm import (
    ActivityCreate,
    ActivityResponse,
    LeadCreate,
    LeadResponse,
    LeadUpdate,
    OpportunityCreate,
    OpportunityResponse,
    OpportunityUpdate,
)

router = APIRouter()


# ---------- Leads ----------
@router.get("/leads", response_model=List[LeadResponse])
def list_leads(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("crm.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, Lead, cid)


@router.post("/leads", response_model=LeadResponse)
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("crm.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(db, Lead, cid, payload.model_dump(), created_by_id=user.id)


@router.put("/leads/{obj_id}", response_model=LeadResponse)
def update_lead(
    obj_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("crm.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.update_for_company(
        db, Lead, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )


# ---------- Opportunities ----------
@router.get("/opportunities", response_model=List[OpportunityResponse])
def list_opportunities(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("crm.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, Opportunity, cid)


@router.post("/opportunities", response_model=OpportunityResponse)
def create_opportunity(
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("crm.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(db, Opportunity, cid, payload.model_dump(), created_by_id=user.id)


@router.put("/opportunities/{obj_id}", response_model=OpportunityResponse)
def update_opportunity(
    obj_id: int,
    payload: OpportunityUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("crm.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.update_for_company(
        db, Opportunity, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )


# ---------- Activities ----------
@router.get("/activities", response_model=List[ActivityResponse])
def list_activities(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("crm.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, Activity, cid)


@router.post("/activities", response_model=ActivityResponse)
def create_activity(
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("crm.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(db, Activity, cid, payload.model_dump(), created_by_id=user.id)
