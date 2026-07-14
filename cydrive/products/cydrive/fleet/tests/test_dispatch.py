import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from products.cydrive.fleet.models import (
    DeliveryCompany,
    DeliveryJob,
    DeliveryJobStatus,
    Driver,
    DriverStatus,
    Vehicle,
    VehicleType,
)
from products.cydrive.fleet.services import (
    DispatchEngine,
    InvalidJobTransitionError,
    NoEligibleDriverError,
    transition_job,
)


@pytest.mark.django_db
class TestDispatchEngine:
    def _company(self):
        return DeliveryCompany.objects.create(tenant_id=uuid.uuid4(), name="Test Co")

    def _vehicle(self, company, **overrides):
        defaults = dict(vehicle_type=VehicleType.CAR, plate_number=f"P-{uuid.uuid4().hex[:6]}")
        defaults.update(overrides)
        return Vehicle.objects.create(company=company, **defaults)

    def _driver(self, company, vehicle, **overrides):
        defaults = dict(
            user_id=uuid.uuid4(),
            name="Driver",
            phone="+962700000000",
            license_number="LN-1",
            status=DriverStatus.AVAILABLE,
            current_vehicle=vehicle,
        )
        defaults.update(overrides)
        return Driver.objects.create(company=company, **defaults)

    def _job(self, company, **overrides):
        defaults = dict(pickup_address={}, dropoff_address={})
        defaults.update(overrides)
        return DeliveryJob.objects.create(company=company, **defaults)

    def test_no_eligible_driver_raises(self):
        company = self._company()
        job = self._job(company)
        with pytest.raises(NoEligibleDriverError):
            DispatchEngine().assign_nearest(job)

    def test_off_shift_driver_not_eligible(self):
        company = self._company()
        vehicle = self._vehicle(company)
        self._driver(company, vehicle, status=DriverStatus.OFF_SHIFT)
        job = self._job(company)
        with pytest.raises(NoEligibleDriverError):
            DispatchEngine().assign_nearest(job)

    def test_temperature_controlled_job_requires_matching_vehicle(self):
        company = self._company()
        regular_vehicle = self._vehicle(company, is_temperature_controlled=False)
        self._driver(company, regular_vehicle)
        job = self._job(company, requires_temperature_control=True)
        with pytest.raises(NoEligibleDriverError):
            DispatchEngine().assign_nearest(job)

    def test_temperature_controlled_job_assigns_matching_vehicle(self):
        company = self._company()
        cold_vehicle = self._vehicle(company, is_temperature_controlled=True)
        driver = self._driver(company, cold_vehicle)
        job = self._job(company, requires_temperature_control=True)
        job = DispatchEngine().assign_nearest(job)
        assert job.driver_id == driver.id
        assert job.status == DeliveryJobStatus.ASSIGNED

    def test_expired_insurance_vehicle_not_eligible(self):
        company = self._company()
        expired_vehicle = self._vehicle(
            company, insurance_expiry=timezone.now().date() - timedelta(days=1)
        )
        self._driver(company, expired_vehicle)
        job = self._job(company)
        with pytest.raises(NoEligibleDriverError):
            DispatchEngine().assign_nearest(job)

    def test_zone_mismatch_not_eligible(self):
        company = self._company()
        vehicle = self._vehicle(company)
        self._driver(company, vehicle, zone="north")
        job = self._job(company, dropoff_address={"zone": "south"})
        with pytest.raises(NoEligibleDriverError):
            DispatchEngine().assign_nearest(job)

    def test_assign_nearest_uses_distance_when_given(self):
        company = self._company()
        v1, v2 = self._vehicle(company), self._vehicle(company)
        near = self._driver(company, v1)
        far = self._driver(company, v2)
        job = self._job(company)

        assigned = DispatchEngine().assign_nearest(
            job, driver_distances={str(far.id): 10.0, str(near.id): 1.0}
        )
        assert assigned.driver_id == near.id

    def test_assign_highest_rated(self):
        company = self._company()
        v1, v2 = self._vehicle(company), self._vehicle(company)
        low = self._driver(company, v1, rating="3.50")
        high = self._driver(company, v2, rating="4.90")
        job = self._job(company)

        assigned = DispatchEngine().assign_highest_rated(job)
        assert assigned.driver_id == high.id

    def test_assigning_driver_marks_them_on_job(self):
        company = self._company()
        vehicle = self._vehicle(company)
        driver = self._driver(company, vehicle)
        job = self._job(company)
        DispatchEngine().assign_nearest(job)
        driver.refresh_from_db()
        assert driver.status == DriverStatus.ON_JOB

    def test_full_job_lifecycle(self):
        company = self._company()
        vehicle = self._vehicle(company)
        driver = self._driver(company, vehicle)
        job = self._job(company)

        job = DispatchEngine().assign_nearest(job)
        job = transition_job(job, DeliveryJobStatus.ACCEPTED)
        job = transition_job(job, DeliveryJobStatus.PICKED_UP)
        assert job.picked_up_at is not None
        job = transition_job(job, DeliveryJobStatus.IN_TRANSIT)
        job = transition_job(job, DeliveryJobStatus.DELIVERED)
        assert job.delivered_at is not None

        DispatchEngine().release_driver(job)
        driver.refresh_from_db()
        assert driver.status == DriverStatus.AVAILABLE

    def test_invalid_transition_raises(self):
        company = self._company()
        job = self._job(company)
        with pytest.raises(InvalidJobTransitionError):
            transition_job(job, DeliveryJobStatus.DELIVERED)

    def test_rejected_job_can_be_redispatched(self):
        company = self._company()
        vehicle = self._vehicle(company)
        self._driver(company, vehicle)
        job = self._job(company)
        job = DispatchEngine().assign_nearest(job)
        job = transition_job(job, DeliveryJobStatus.REJECTED)
        job = transition_job(job, DeliveryJobStatus.PENDING)
        assert job.status == DeliveryJobStatus.PENDING
