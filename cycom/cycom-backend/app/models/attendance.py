from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Date

from app.db.base import BaseEntity


class BiometricDevice(BaseEntity):
    __tablename__ = "att_devices"
    name = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    port = Column(Integer, default=4370, nullable=False)
    location = Column(String, nullable=True)
    status = Column(String, default="Online", nullable=False)  # Online|Offline
    last_synced_at = Column(DateTime(timezone=True), nullable=True)


class AttendancePunch(BaseEntity):
    __tablename__ = "att_punches"
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("att_devices.id"), nullable=True)
    punch_at = Column(DateTime(timezone=True), nullable=False, index=True)
    punch_type = Column(String, nullable=False)  # Check-In | Check-Out
    method = Column(String, default="Face ID", nullable=False)  # Face ID | Fingerprint | RFID | Manual
    is_correction = Column(String, default="no", nullable=False)
    correction_reason = Column(String, nullable=True)


class ShiftPlan(BaseEntity):
    __tablename__ = "att_shift_plans"
    name = Column(String, nullable=False)
    weekly_hours = Column(Numeric(5, 2), default=48, nullable=False)
    start_time = Column(String, default="08:00", nullable=False)
    end_time = Column(String, default="17:00", nullable=False)
    break_minutes = Column(Integer, default=60, nullable=False)


class EmployeeSchedule(BaseEntity):
    __tablename__ = "att_employee_schedules"
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False, index=True)
    shift_plan_id = Column(Integer, ForeignKey("att_shift_plans.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
