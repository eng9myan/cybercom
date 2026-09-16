"""
RefId minting and lookup.

Two rules carry the weight here:

**Mint once, never change.** A RefId is a promise to a consumer that this
object is the same object it was last week. Regenerating one looks to the
consumer like a delete followed by a create, orphaning whatever history they
attached to the old identifier.

**Derived objects need deterministic local ids.** ``StudentAttendance`` is not
a table — it is a student, a date and a school taken together. Hashing those
components with UUIDv5 gives the same local id on every run, so the registry
finds the existing RefId instead of minting a second one for the same fact.
"""

import uuid

from products.cyed.sif.models import SifRefId

# Namespace for synthetic local ids. Fixed forever: changing it would change
# every derived local id and therefore mint a fresh RefId for every derived
# object in existence.
CYED_SIF_NAMESPACE = uuid.UUID("6f5c0e2a-6d3b-5f6a-9a1e-2c7b4d8e9f01")


def synthetic_local_id(*components) -> str:
    """
    A stable local id for an object that has no single row behind it.

    Components are stringified and joined; ``None`` becomes an empty string so
    a missing optional part does not shift the hash of everything after it.
    """
    joined = "|".join("" if c is None else str(c) for c in components)
    return str(uuid.uuid5(CYED_SIF_NAMESPACE, joined))


def get_or_create_refid(tenant_id, object_type: str, local_id, *,
                        source_local_id=None, description="") -> uuid.UUID:
    """
    The RefId for this object, minting one on first use.

    ``get_or_create`` rather than a check-then-insert: two concurrent exports
    of the same student would otherwise race and mint two RefIds for one
    object, which is precisely the failure the uniqueness constraints exist to
    prevent.

    ``source_local_id`` is the CyEd row behind a derived object. Passing it
    turns a later RefId lookup into a direct fetch instead of a scan that
    re-derives hashes until one matches.
    """
    row, _created = SifRefId.objects.get_or_create(
        tenant_id=tenant_id,
        object_type=object_type,
        local_id=str(local_id),
        defaults={
            "refid": uuid.uuid4(),
            "source_local_id": str(source_local_id if source_local_id is not None else local_id),
            "source_description": description[:255],
        },
    )
    return row.refid


def resolve_refid(tenant_id, refid):
    """The registry row for a RefId, or None. Used to serve object-by-RefId."""
    try:
        parsed = uuid.UUID(str(refid))
    except (ValueError, AttributeError, TypeError):
        return None
    return SifRefId.objects.filter(tenant_id=tenant_id, refid=parsed).first()


def canonical(refid) -> str:
    """
    SIF RefIds appear on the wire as lowercase hyphenated UUIDs.

    Normalised in one place so an object emitted through XML and the same
    object emitted through JSON never differ by formatting — a consumer
    comparing the two strings would treat them as different objects.
    """
    return str(uuid.UUID(str(refid)))
