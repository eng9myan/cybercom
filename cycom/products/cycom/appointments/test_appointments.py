import uuid
from datetime import datetime, timedelta, timezone as dt_timezone

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from products.cycom.appointments.models import AppointmentType, AvailabilitySlot, Resource
from products.cycom.appointments.services import book_appointment, cancel_booking, complete_booking


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "front-desk@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


MONDAY = datetime(2026, 9, 21, tzinfo=dt_timezone.utc)  # a Monday, timezone-aware (USE_TZ=True)


@pytest.fixture
def setup(db, tenant_id):
    resource = Resource.objects.create(tenant_id=tenant_id, name="Dr. Smith")
    AvailabilitySlot.objects.create(
        tenant_id=tenant_id, resource=resource, weekday=0, start_time="09:00", end_time="17:00"
    )
    appt_type = AppointmentType.objects.create(
        tenant_id=tenant_id, name="Consultation", duration_minutes=30, buffer_minutes=15
    )
    return {"resource": resource, "appt_type": appt_type}


@pytest.mark.django_db
def test_book_within_availability(tenant_id, setup):
    booking = book_appointment(
        resource=setup["resource"], appointment_type=setup["appt_type"],
        start_at=MONDAY.replace(hour=10), customer_name="Jane",
    )
    assert booking.status == "confirmed"
    assert booking.end_at == MONDAY.replace(hour=10, minute=30)


@pytest.mark.django_db
def test_book_outside_availability_rejected(tenant_id, setup):
    with pytest.raises(ValidationError):
        book_appointment(
            resource=setup["resource"], appointment_type=setup["appt_type"],
            start_at=MONDAY.replace(hour=18), customer_name="Jane",
        )


@pytest.mark.django_db
def test_book_wrong_weekday_rejected(tenant_id, setup):
    tuesday = MONDAY + timedelta(days=1)
    with pytest.raises(ValidationError):
        book_appointment(
            resource=setup["resource"], appointment_type=setup["appt_type"],
            start_at=tuesday.replace(hour=10), customer_name="Jane",
        )


@pytest.mark.django_db
def test_overlapping_booking_rejected(tenant_id, setup):
    book_appointment(
        resource=setup["resource"], appointment_type=setup["appt_type"],
        start_at=MONDAY.replace(hour=10), customer_name="Jane",
    )
    # 10:00-10:30 booked + 15min buffer -> occupied until 10:45.
    with pytest.raises(ValidationError):
        book_appointment(
            resource=setup["resource"], appointment_type=setup["appt_type"],
            start_at=MONDAY.replace(hour=10, minute=20), customer_name="John",
        )


@pytest.mark.django_db
def test_booking_after_buffer_succeeds(tenant_id, setup):
    book_appointment(
        resource=setup["resource"], appointment_type=setup["appt_type"],
        start_at=MONDAY.replace(hour=10), customer_name="Jane",
    )
    # First booking occupies 10:00-10:45 (30min + 15min buffer). 10:45 is free.
    booking2 = book_appointment(
        resource=setup["resource"], appointment_type=setup["appt_type"],
        start_at=MONDAY.replace(hour=10, minute=45), customer_name="John",
    )
    assert booking2.status == "confirmed"


@pytest.mark.django_db
def test_cancelled_booking_frees_the_slot(tenant_id, setup):
    booking = book_appointment(
        resource=setup["resource"], appointment_type=setup["appt_type"],
        start_at=MONDAY.replace(hour=10), customer_name="Jane",
    )
    cancel_booking(booking)
    booking2 = book_appointment(
        resource=setup["resource"], appointment_type=setup["appt_type"],
        start_at=MONDAY.replace(hour=10), customer_name="John",
    )
    assert booking2.status == "confirmed"


@pytest.mark.django_db
def test_cannot_cancel_completed_booking(tenant_id, setup):
    booking = book_appointment(
        resource=setup["resource"], appointment_type=setup["appt_type"],
        start_at=MONDAY.replace(hour=10), customer_name="Jane",
    )
    complete_booking(booking)
    with pytest.raises(ValidationError):
        cancel_booking(booking)


@pytest.mark.django_db
def test_api_book_and_cancel(admin_client, tenant_id, setup):
    resp = admin_client.post(
        "/api/v1/appointments/bookings/",
        {
            "resource": str(setup["resource"].id),
            "appointment_type": str(setup["appt_type"].id),
            "start_at": MONDAY.replace(hour=11).isoformat(),
            "customer_name": "Jane",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.data
    booking_id = resp.data["id"]

    resp = admin_client.post(f"/api/v1/appointments/bookings/{booking_id}/cancel/")
    assert resp.status_code == 200
    assert resp.data["status"] == "cancelled"


@pytest.mark.django_db
def test_tenant_isolation(admin_client):
    Resource.objects.create(tenant_id=uuid.uuid4(), name="Foreign Resource")
    resp = admin_client.get("/api/v1/appointments/resources/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "Foreign Resource" for r in rows)
