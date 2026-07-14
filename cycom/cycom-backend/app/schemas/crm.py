from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class _M(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LeadBase(BaseModel):
    name: str
    partner_id: Optional[int] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    source: Optional[str] = None
    expected_revenue: Decimal = Decimal("0")
    assigned_to_id: Optional[int] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    stage: Optional[str] = None
    assigned_to_id: Optional[int] = None
    expected_revenue: Optional[Decimal] = None


class LeadResponse(_M, LeadBase):
    id: int
    company_id: int
    stage: str


class OpportunityBase(BaseModel):
    name: str
    lead_id: Optional[int] = None
    partner_id: Optional[int] = None
    amount: Decimal = Decimal("0")
    probability: Decimal = Decimal("0")
    expected_close: Optional[date] = None
    assigned_to_id: Optional[int] = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    stage: Optional[str] = None
    amount: Optional[Decimal] = None
    probability: Optional[Decimal] = None


class OpportunityResponse(_M, OpportunityBase):
    id: int
    company_id: int
    stage: str


class ActivityCreate(BaseModel):
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    activity_type: str
    subject: str
    notes: Optional[str] = None
    due_date: Optional[date] = None


class ActivityResponse(_M, ActivityCreate):
    id: int
    company_id: int
    status: str
