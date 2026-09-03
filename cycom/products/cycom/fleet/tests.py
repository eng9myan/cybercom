"""Fleet module tests (SQLite via core.settings_test)."""

import uuid
from decimal import Decimal

from django.test import TestCase

from products.cycom.fleet.models import FuelLog, MaintenanceLog, Vehicle
from products.cycom.fleet.serializers import VehicleSerializer

TENANT = uuid.uuid4()


class FleetModelTests(TestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            tenant_id=TENANT,
            license_plate="22-12345",
            make="Toyota",
            model="Hilux",
            driver_name="Omar",
            odometer_km=Decimal("50000.0"),
        )

    def test_logs_attach_to_vehicle(self):
        MaintenanceLog.objects.create(
            tenant_id=TENANT, vehicle=self.vehicle, maintenance_date="2026-07-01",
            maintenance_type="preventative", cost=Decimal("120"), odometer_km=Decimal("50100"),
        )
        FuelLog.objects.create(
            tenant_id=TENANT, vehicle=self.vehicle, log_date="2026-07-02",
            liters=Decimal("40"), price_per_liter=Decimal("0.9"),
            total_cost=Decimal("36"), odometer_km=Decimal("50200"),
        )
        self.assertEqual(self.vehicle.maintenance_logs.count(), 1)
        self.assertEqual(self.vehicle.fuel_logs.count(), 1)

    def test_odometer_cannot_decrease(self):
        ser = VehicleSerializer(instance=self.vehicle, data={"odometer_km": "40000.0"}, partial=True)
        self.assertFalse(ser.is_valid())
        self.assertIn("odometer_km", ser.errors)

    def test_odometer_can_increase(self):
        ser = VehicleSerializer(instance=self.vehicle, data={"odometer_km": "50500.0"}, partial=True)
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_plate_unique_per_tenant(self):
        Vehicle.objects.create(tenant_id=uuid.uuid4(), license_plate="22-12345")  # other tenant OK
        with self.assertRaises(Exception):
            Vehicle.objects.create(tenant_id=TENANT, license_plate="22-12345")
