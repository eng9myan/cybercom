"""
SIF AU v3.x interoperability for CyEd.

WHAT THIS IS
------------
A **SIF AU v3.x data mapping layer plus a RefId registry**. It lets CyEd expose
its domain data as SIF-shaped objects (XML and JSON) with stable, RFC 4122
128-bit RefIds, which is the prerequisite for exchanging data with Australian
government and jurisdictional systems.

WHAT THIS IS *NOT*
------------------
This is **not** a certified SIF Zone / broker integration and CyEd must not be
described as "SIF certified" on the strength of it. Explicitly still outstanding:

  * SIF Zone registration and Environment provisioning (Infrastructure services:
    ``/environments``, ``/requestsConnector``, ``/queues``, ``/subscriptions``).
  * Event publication / subscription (CREATE / UPDATE / DELETE events onto a
    zone topic) — this module is request/response only.
  * Delayed (asynchronous) message exchange and message queue semantics.
  * SIF conformance certification against a jurisdiction's test harness.
  * Consumer-side ingestion (CyEd currently *provides* objects; it does not
    *consume* them).

The ``/api/v1/sif/coverage/`` endpoint restates the same disclaimer at runtime
and additionally lists, element by element, which required SIF elements CyEd
cannot currently populate and why. That report — not a conformance badge — is
what an auditor should be given.

WHY A REFID REGISTRY (AND NOT A ``refid`` COLUMN ON EVERY MODEL)
---------------------------------------------------------------
SIF requires every object instance to carry a RefId: a 128-bit UUID that is
*minted once and never changes* for the life of that object, because consumers
(jurisdictional data warehouses, NAPLAN/attendance collections, third-party
zone applications) key their own records off it.

The naive retrofit is to add a ``refid`` column to each of the ~30 existing
domain models. That is the wrong move for an established schema:

  * it is a schema migration against every table in the product, touching code
    owned by many teams at once;
  * it couples an integration concern to core domain models that have nothing
    to do with SIF;
  * SIF objects are not 1:1 with tables — ``StudentSchoolEnrollment`` and
    ``StudentAttendance`` are *derived* views over several tables and have no
    single row to hang a column on;
  * one physical row can legitimately surface as more than one SIF object.

The registry pattern inverts it: a single side table (``cyed_sif_refids``) maps
``(tenant_id, object_type, local_id) -> refid``. RefIds are minted lazily on
first emission and are stable forever after. Derived/synthetic objects get a
deterministic ``local_id`` via UUIDv5 (see ``refids.synthetic_local_id``) so
they too are stable across runs. No domain model is modified.

MODULE MAP
----------
  ``models.py``   — ``SifRefId``, the registry table.
  ``refids.py``   — ``get_or_create_refid`` and friends; canonical RefId form.
  ``mappers.py``  — one mapper per SIF object; declares its honest gap list.
  ``encoding.py`` — dict -> SIF XML (namespaced) / SIF JSON.
  ``views.py``    — object collection, object-by-RefId, and the coverage report.
"""
