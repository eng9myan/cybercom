import uuid
from unittest.mock import patch

import jwt
import pytest
from rest_framework.test import APIClient

from platform.events.models import (
    DeadLetterEvent,
    EventDeliveryLog,
    EventSignature,
    OutboxEvent,
    OutboxEventStatus,
)
from platform.events.replay import EventReplayManager
from platform.events.signing import EventSigner


@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()


@pytest.fixture
def auth_client(test_tenant_id):
    client = APIClient()
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "admin@cybercom.io",
        "tenant_id": str(test_tenant_id),
        "realm_access": {"roles": ["platform_admin"]},
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    }
    token = jwt.encode(payload, "dummy-secret", algorithm="HS256")
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_TENANT_ID=str(test_tenant_id),
    )
    return client


@pytest.mark.django_db
class TestEventModels:
    def test_outbox_event_lifecycle(self, test_tenant_id):
        event = OutboxEvent.objects.create(
            tenant_id=test_tenant_id,
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-123"},
        )
        assert event.status == OutboxEventStatus.PENDING
        assert (
            str(event)
            == "OutboxEvent(platform.identity.events, cyidentity.user.provisioned, pending)"
        )

        event.mark_published()
        assert event.status == OutboxEventStatus.PUBLISHED
        assert event.published_at is not None

        event.mark_failed("Network timeout")
        assert event.status == OutboxEventStatus.FAILED
        assert event.error_message == "Network timeout"
        assert event.retry_count == 1

    def test_dead_letter_event(self, test_tenant_id):
        dlq = DeadLetterEvent.objects.create(
            original_event_id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            topic="platform.identity.events",
            payload={"user_id": "usr-123"},
            error_message="Validation error",
        )
        assert dlq.resolved is False
        assert dlq.failed_at is not None

    def test_event_delivery_log(self, test_tenant_id):
        log = EventDeliveryLog.objects.create(
            event_id=uuid.uuid4(),
            consumer_group="identity-group",
            tenant_id=test_tenant_id,
            status="delivered",
        )
        assert log.status == "delivered"

    def test_event_signature(self, test_tenant_id):
        event = OutboxEvent.objects.create(
            tenant_id=test_tenant_id,
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-123"},
        )
        sig = EventSignature.objects.create(event=event, signature="test-sig-123")
        assert sig.signature == "test-sig-123"
        assert event.signature_record == sig


@pytest.mark.django_db
class TestEventSigning:
    def test_sign_and_verify(self, test_tenant_id):
        payload = b'{"user_id": "usr-123"}'
        sig = EventSigner.sign_payload(str(test_tenant_id), payload)

        # Verify valid signature
        assert EventSigner.verify_signature(str(test_tenant_id), payload, sig) is True

        # Verify invalid signature (tampered payload)
        assert (
            EventSigner.verify_signature(str(test_tenant_id), b'{"user_id": "usr-999"}', sig)
            is False
        )

        # Verify invalid signature (wrong tenant)
        assert EventSigner.verify_signature(str(uuid.uuid4()), payload, sig) is False

        # Verify invalid signature string
        assert EventSigner.verify_signature(str(test_tenant_id), payload, "invalid-sig") is False


@pytest.mark.django_db
class TestEventReplay:
    @patch("platform.events.publisher.KafkaEventPublisher.publish")
    def test_replay_events(self, mock_publish, test_tenant_id):
        mock_publish.return_value = True

        # Create events
        OutboxEvent.objects.create(
            tenant_id=test_tenant_id,
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-1"},
        )
        OutboxEvent.objects.create(
            tenant_id=test_tenant_id,
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-2"},
        )
        # Event in different topic/tenant
        OutboxEvent.objects.create(
            tenant_id=uuid.uuid4(),
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-3"},
        )

        replayed = EventReplayManager.replay_events(
            tenant_id=str(test_tenant_id), topic="platform.identity.events"
        )
        assert replayed == 2
        assert mock_publish.call_count == 2

    @patch("platform.events.publisher.KafkaEventPublisher.publish")
    def test_replay_failed_events(self, mock_publish, test_tenant_id):
        mock_publish.return_value = True

        event = OutboxEvent.objects.create(
            tenant_id=test_tenant_id,
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-1"},
            status=OutboxEventStatus.FAILED,
        )

        replayed = EventReplayManager.replay_failed_events(
            tenant_id=str(test_tenant_id), topic="platform.identity.events"
        )
        assert replayed == 1
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.PUBLISHED


@pytest.mark.django_db
class TestEventAPIs:
    def test_list_outbox_events_unauthenticated(self):
        client = APIClient()
        resp = client.get("/api/v1/events/outbox/")
        assert resp.status_code == 401

    def test_list_outbox_events(self, auth_client, test_tenant_id):
        OutboxEvent.objects.create(
            tenant_id=test_tenant_id,
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-1"},
        )
        resp = auth_client.get("/api/v1/events/outbox/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    @patch("platform.events.publisher.KafkaEventPublisher.publish")
    def test_api_replay(self, mock_publish, auth_client, test_tenant_id):
        mock_publish.return_value = True
        OutboxEvent.objects.create(
            tenant_id=test_tenant_id,
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-1"},
        )

        resp = auth_client.post(
            "/api/v1/events/outbox/replay/",
            {"tenant_id": str(test_tenant_id), "topic": "platform.identity.events"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["replayed_count"] == 1

    def test_api_sign_event(self, auth_client, test_tenant_id):
        event = OutboxEvent.objects.create(
            tenant_id=test_tenant_id,
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-1"},
        )
        resp = auth_client.post(f"/api/v1/events/outbox/{event.id}/sign/", format="json")
        assert resp.status_code == 200
        assert "signature" in resp.data

    def test_api_retry_dlq(self, auth_client, test_tenant_id):
        OutboxEvent.objects.create(
            tenant_id=test_tenant_id,
            topic="platform.identity.events",
            event_type="cyidentity.user.provisioned",
            payload={"user_id": "usr-1"},
            status=OutboxEventStatus.FAILED,
        )
        with patch("platform.events.publisher.KafkaEventPublisher.publish", return_value=True):
            resp = auth_client.post(
                "/api/v1/events/dlq/retry/",
                {"tenant_id": str(test_tenant_id), "topic": "platform.identity.events"},
                format="json",
            )
            assert resp.status_code == 200
            assert resp.data["retried_count"] == 1
