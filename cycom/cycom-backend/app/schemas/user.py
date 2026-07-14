from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class RoleBase(BaseModel):
    name: str
    permissions: List[str] = []


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: Optional[int] = None
    created_at: datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True
    is_superuser: bool = False
    role_id: Optional[int] = None
    company_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None
    company_id: Optional[int] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None
    permissions: List[str] = []
    company_id: Optional[int] = None
