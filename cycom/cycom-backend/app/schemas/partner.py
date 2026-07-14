from typing import Optional
from pydantic import BaseModel, ConfigDict


class PartnerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    is_customer: bool = False
    is_vendor: bool = False
    payment_terms: str = "net_30"


class PartnerCreate(PartnerBase):
    pass


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    is_customer: Optional[bool] = None
    is_vendor: Optional[bool] = None
    payment_terms: Optional[str] = None


class PartnerResponse(PartnerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
