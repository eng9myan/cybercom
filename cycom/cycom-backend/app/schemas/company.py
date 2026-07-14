from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CompanyBase(BaseModel):
    name: str
    short_name: str
    code: str
    currency: str = "JOD"
    country_code: str = "JO"
    type: str = "commercial"


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    currency: Optional[str] = None
    country_code: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
