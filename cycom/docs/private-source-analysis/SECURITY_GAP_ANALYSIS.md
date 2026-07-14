# CyCom ERP — Security Gap Analysis
# Copyright (C) CyberCom. All rights reserved.
# Generated: 2026-07-14

## Critical Security Gaps

### GAP-SEC-001: JWT Secret Hardcoded
- File: cycom-backend/app/core/security.py
- Issue: SECRET_KEY = "cycom-super-secret-key-for-development-only" hardcoded
- Risk: Anyone with source access can forge any user token
- Fix: Load from environment variable (JWT_SECRET_KEY), rotate on deploy

### GAP-SEC-002: No Endpoint Authentication
- Files: All routers in cycom-backend/app/api/routers/
- Issue: No route uses Depends(get_current_user) middleware
- Risk: Any unauthenticated caller can access all data
- Fix: Add auth dependency to every protected route; create public route whitelist

### GAP-SEC-003: Path Traversal in File Upload
- File: cycom-backend/app/api/routers/sign.py:25
- Issue: os.path.join(UPLOAD_DIR, file.filename) without sanitization
- Risk: Attacker uploads file to arbitrary path (e.g. ../../app/main.py)
- Fix: Use uuid4() as filename, ignore user-supplied filename

### GAP-SEC-004: CORS Wildcard + Credentials
- File: cycom-backend/app/main.py
- Issue: allow_origins=["*"] + allow_credentials=True (browser rejects this)
- Risk: CORS misconfiguration; actual intent unclear
- Fix: Specify allowed origins explicitly from environment config

### GAP-SEC-005: SQLite Single Writer
- File: cycom-backend/app/core/config.py
- Issue: SQLite cannot handle concurrent writes; lock timeouts in multi-user scenarios
- Risk: Data corruption / loss under concurrent load
- Fix: Migrate to PostgreSQL before any production use

### GAP-SEC-006: Bootstrap Endpoint Unauthenticated
- File: core-kernel/main.py
- Issue: /api/setup/bootstrap creates company records without authentication
- Risk: Anyone can reinitialize or corrupt tenant data
- Fix: Require admin token + one-time setup token

### GAP-SEC-007: Missing Rate Limiting
- All API endpoints lack rate limiting
- Risk: Brute force on login, DDoS on data endpoints
- Fix: Add slowapi or nginx rate limiting

### GAP-SEC-008: No Input Validation on Uploads
- File: Multiple upload handlers
- Issue: No file size limit, no MIME type validation, no virus scan
- Risk: Large file DoS, malicious file execution
- Fix: Limit to 10MB, whitelist MIME types, scan uploads

## Reference Platform Security Findings (from Full Codebase Study)
Findings from functional reference analysis - CyCom must NOT replicate these issues:

- 90 instances of sudo() bypassing record rules in reference platform
- 16 instances of raw SQL in reference platform
- 8 public routes without token validation
- 6 endpoints with CSRF disabled
- Device login with public bootstrap endpoint

## CyCom Security Implementation Plan

Phase 1 (Immediate):
1. Move JWT_SECRET_KEY to .env file
2. Add get_current_user dependency to all routes except /api/auth/login
3. Fix file upload path sanitization
4. Restrict CORS to localhost:5555 in dev, configured domain in prod

Phase 2:
5. Implement RBAC middleware (check role claims in JWT)
6. Add branch_id scope filter to all tenant queries
7. Add company_id scope filter
8. Add rate limiting (5 req/sec per IP on auth endpoints)

Phase 3:
9. Migrate to PostgreSQL (concurrent writes)
10. Add immutable audit log table
11. Implement field-level change tracking
12. Add upload size limits and MIME validation
