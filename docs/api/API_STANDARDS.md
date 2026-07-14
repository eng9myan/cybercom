# CyberCom API Standards

Status: describes what `platform/api/` actually implements, verified against
code (`platform/api/*.py`) as of the Phase 1 platform promotion. Not aspirational.

## Versioning

`platform/api/versioning.py` — `CyberComAPIVersioning(URLPathVersioning)`.
URL-path versioning: `/api/v1/...`. `allowed_versions = ["v1", "v2"]`,
`default_version = "v1"`. Only `cymed` currently wires this in; `cyshop` and
`cycom` do not yet share it (see `docs/architecture/IDENTITY_FEDERATION.md`).

## Authentication & tenant context

Every request (except health checks and `/api/v1/public/*`) must carry
`Authorization: Bearer <token>`. `shared/auth/auth_middleware.py`
(`CyIdentityAuthMiddleware`) validates the token as RS256 against
`CYIDENTITY_JWKS_URI`, then sets:

- `request.auth_claims` — full decoded JWT payload
- `request.user_session` — `{user_id, email, tenant_id, roles, permissions}`

There is no dev-mode bypass in the middleware — tests mint real RS256 tokens
against a mocked JWKS client (`platform/conftest.py`, `cymed/conftest.py`)
rather than the middleware trusting a shared secret. Tenant context also
arrives via `X-Tenant-ID` header in the tests, but the middleware itself only
trusts `tenant_id` from the verified JWT claim — `X-Tenant-ID` is not
independently authenticated by the middleware as written today, which is
worth closing before this is relied on for tenant isolation. **Gap.**

## Pagination

`platform/api/pagination.py` — `CyberComCursorPagination`. Cursor-based (no
offset), `created_at` DESC. Query params: `limit` (default 20, max 200),
`starting_after` (cursor). Response shape:

```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "...",
    "previous_cursor": "...",
    "has_more": true,
    "count": 20,
    "limit": 20
  }
}
```

## Errors

`platform/api/exceptions.py` — `cybercom_exception_handler`, RFC 7807
Problem Details:

```json
{
  "type": "https://cybercom.io/errors/<code>",
  "title": "<HTTP status phrase>",
  "status": 400,
  "detail": "<message>",
  "instance": "<request path>",
  "code": "<DRF exception default_code, if present>"
}
```

## Idempotency

`platform/api/idempotency.py` — `IdempotencyService`. Header:
`Idempotency-Key` (max 255 chars). Request body is SHA-256 hashed and stored
alongside the key; a replayed key returns the cached response instead of
reprocessing. Retention: 24 hours (`RETENTION_HOURS = 24`).

## Rate limiting

`platform/api/rate_limit.py` — sliding-window. `InMemoryRateLimiter` for
dev/test (thread-safe, in-process). Production is documented as Redis-backed
in the module docstring, but no Redis-backed implementation exists in this
file as of this audit — only the in-memory one. **Gap: verify before relying
on rate limiting in a multi-process production deployment**, since an
in-memory limiter does not coordinate across worker processes.

## Correlation IDs

`platform/api/middleware.py` — `CorrelationIdMiddleware` reads
`X-Correlation-ID` from the request or generates one, and echoes it back on
the response. Only wired into `cymed`'s middleware stack currently.

## Known gaps (verified, not assumed)

- `X-Tenant-ID` header is not independently authenticated — see above.
- Rate limiter has no cross-process backend implemented yet.
- `cyshop` (Django) and `cycom` (Odoo) do not use any of the above yet —
  each has its own pagination/error/versioning conventions. Federating them
  is tracked separately (`docs/architecture/IDENTITY_FEDERATION.md`).
