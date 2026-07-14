from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class _M(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BiometricDeviceBase(BaseModel):
    name: str
    ip_address: str
    port: int = 4370
    location: Optional[str] = None
    status: str = "Online"


class BiometricDeviceCreate(BiometricDeviceBase):
    pass


class BiometricDeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = None


class BiometricDeviceResponse(_M, BiometricDeviceBase):
    id: int
    company_id: int
    last_synced_at: Optional[datetime] = None


class PunchBase(BaseModel):
    employee_id: int
    device_id: Optional[int] = None
    punch_at: datetime
    punch_type: str
    method: str = "Face ID"
    is_correction: str = "no"
    correction_reason: Optional[str] = None


class PunchCreate(PunchBase):
    pass


class PunchResponse(_M, PunchBase):
    id: int
    company_id: int


class ShiftPlanBase(BaseModel):
    name: str
    weekly_hours: Decimal = Decimal("48")
    start_time: str = "08:00"
    end_time: str = "17:00"
    break_minutes: int = 60


class ShiftPlanCreate(ShiftPlanBase):
    pass


class ShiftPlanResponse(_M, ShiftPlanBase):
    id: int
    company_id: int


class ScheduleBase(BaseModel):
    employee_id: int
    shift_plan_id: int
    date: date


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleResponse(_M, ScheduleBase):
    id: int
    company_id: int
