from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, Date

from app.db.base import BaseEntity


class Vehicle(BaseEntity):
    __tablename__ = "fleet_vehicles"
    plate = Column(String, unique=True, index=True, nullable=False)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    vin = Column(String, nullable=True)
    odometer = Column(Numeric(12, 2), default=0, nullable=False)
    driver_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=True)
    status = Column(String, default="active", nullable=False)  # active|in_service|sold|retired


class FuelLog(BaseEntity):
    __tablename__ = "fleet_fuel_logs"
    vehicle_id = Column(Integer, ForeignKey("fleet_vehicles.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    odometer = Column(Numeric(12, 2), nullable=False)
    liters = Column(Numeric(8, 2), nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)
    station = Column(String, nullable=True)


class VehicleService(BaseEntity):
    __tablename__ = "fleet_vehicle_services"
    vehicle_id = Column(Integer, ForeignKey("fleet_vehicles.id"), nullable=False, index=True)
    service_date = Column(Date, nullable=False)
    description = Column(String, nullable=False)
    cost = Column(Numeric(10, 2), default=0, nullable=False)
    odometer = Column(Numeric(12, 2), nullable=True)
