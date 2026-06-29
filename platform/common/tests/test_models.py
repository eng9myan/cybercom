"""Unit tests for common base models."""

import uuid

import pytest


@pytest.mark.unit
class TestBaseModelAbstracts:
    def test_uuid_is_valid_format(self):
        pk = uuid.uuid4()
        assert str(pk) == str(uuid.UUID(str(pk)))

    def test_uuid_uniqueness(self):
        ids = {uuid.uuid4() for _ in range(1000)}
        assert len(ids) == 1000
