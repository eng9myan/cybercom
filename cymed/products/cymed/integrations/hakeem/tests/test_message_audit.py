"""HakeemMessage — subject_national_id is encrypted per-tenant at rest."""

import uuid

import pytest

from django.db import connection

from platform.common.fields import MASK
from platform.common.tenant_context import tenant_context
from platform.security.crypto import blind_index, is_encrypted
from products.cymed.integrations.hakeem.models import HakeemMessage


@pytest.mark.django_db
def test_subject_national_id_is_encrypted_and_blind_indexed():
    tid = uuid.uuid4()
    with tenant_context(tid):
        msg = HakeemMessage.objects.create(
            tenant_id=tid, direction="pull", transport="fhir", op="get_patient",
            subject_national_id="2001234567", status="succeeded",
        )
        # round-trips in context
        msg.refresh_from_db()
        assert msg.subject_national_id == "2001234567"
        # blind index is queryable
        found = HakeemMessage.objects.filter(
            tenant_id=tid, subject_national_id_bidx=blind_index("2001234567")
        )
        assert found.count() == 1

    # ciphertext at rest, no plaintext leak
    with connection.cursor() as cur:
        cur.execute(
            "SELECT subject_national_id FROM cymed_hakeem_messages WHERE id = %s",
            [msg.id.hex],
        )
        raw = cur.fetchone()[0]
    raw = raw if isinstance(raw, (bytes, bytearray)) else bytes(raw, "latin-1")
    assert is_encrypted(raw)

    # a read with no tenant context masks rather than leaking
    assert HakeemMessage.objects.get(id=msg.id).subject_national_id == MASK


@pytest.mark.django_db
def test_blank_subject_national_id_is_fine():
    tid = uuid.uuid4()
    with tenant_context(tid):
        msg = HakeemMessage.objects.create(
            tenant_id=tid, direction="push", transport="rpc", op="ping",
            status="succeeded",
        )
        msg.refresh_from_db()
        assert msg.subject_national_id in ("", None)
        assert msg.subject_national_id_bidx is None
