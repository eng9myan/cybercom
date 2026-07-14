# ADR: CyShop / CyCom Identity Federation

Status: proposed, not implemented. Documenting per working-method rule
"stop and document blockers rather than inventing missing business rules" —
this is a real architectural fork, not something to execute unverified.

## Current state (verified by reading each product's code)

- **CyMed** (`cymed/`): uses `platform.cyidentity` — full CyIdentity
  (realms, roles, sessions, WebAuthn, break-glass) via `shared.auth.
  auth_middleware.CyIdentityAuthMiddleware`, RS256/JWKS.
- **CyShop** (`cyshop/backend/apps/identity/`): its own Django app —
  `authentication.py`, `models.py`, real applied migrations
  (`0001_initial.py`, `0002_initial.py`). Independently working, has its
  own user/session model. Not connected to `platform.cyidentity` at all.
- **CyCom** (`cycom/cycom-platform/`): Odoo 19's own built-in auth
  (`res.users`, Odoo sessions). Not Django, can't import `platform.
  cyidentity` as code — any integration has to be over the network (OIDC),
  not a shared Python import.

Three separate, independently-working identity systems today. The master
spec's rule — "one consumer identity, not duplicate records per product" —
isn't met yet.

## Why this wasn't just implemented

Ripping out CyShop's working identity app and pointing it at `platform.
cyidentity` is a real migration: existing users, sessions, and any
downstream code depending on CyShop's own user model would need a data
migration, not just a code change. Doing that without a live Keycloak
instance to actually test the federation against — and without knowing
whether CyShop has real user data anywhere that this would need to
preserve — risks exactly the kind of breakage the "preserve all working
functionality" rule exists to prevent. This needs a live IdP to build and
test against, not a blind code change.

## Recommended path (not yet executed)

1. **Federation, not replacement.** `platform.cyidentity` becomes the
   platform-wide IdP (Keycloak-backed). CyShop's own identity app becomes
   an OIDC *client* of it, not a competing user store — CyShop users get a
   `platform_user_id` foreign key/claim mapping to the CyIdentity realm,
   but CyShop's own session/auth code isn't deleted until the mapping is
   proven in a real environment.
2. **CyCom (Odoo) integrates via `auth_oidc`** (Odoo's built-in OpenID
   Connect auth module), pointed at the same Keycloak realm/JWKS endpoint
   `cymed` already uses (`CYIDENTITY_JWKS_URI` / `CYIDENTITY_ISSUER` in
   `cymed/core/settings.py`). This is configuration, not a code merge —
   matches "do not introduce microservices/rewrites only for appearance."
3. **Shared claim shape**: reuse the same JWT claim structure the
   `shared/auth/auth_middleware.py` already expects (`sub`, `email`,
   `tenant_id`, `roles`, `permissions`) so CyShop and CyCom's federated
   sessions produce a `request.user_session` shaped identically to
   CyMed's, letting any future cross-product code (CyMart, Super App) rely
   on one shape regardless of which product issued the request.

## Blocking this from being implemented right now

- No live Keycloak instance in this environment to register CyShop/CyCom
  clients against or to test the federation flow end-to-end.
- Unknown whether CyShop's `identity` app has real production user data
  that a migration would need to preserve, or whether it's still pre-launch
  (this needs the human product answer, not a guess).

## What CyShop can safely adopt now, without touching auth

`platform.audit` and `platform.events` (outbox) are purely additive —
logging and event emission don't conflict with CyShop's existing auth.
These are lower-risk to wire in ahead of full identity federation and are
tracked as Phase 2 work.
