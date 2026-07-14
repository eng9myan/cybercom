# CyberCom Website — Platform API Integration Guide

## Overview

The Cybercom-Website connects to the CyberCom Platform backend (`CyberCom-Platform`) for dynamic content, lead capture, authentication, and service health monitoring.

---

## Architecture

```
cy-com.com (Static Site)
       │
       ├── TypeScript SDK (src/lib/)
       │     ├── API Client (api/client.ts)      ← centralized fetch
       │     ├── Middleware (api/middleware.ts)   ← JWT, retry, errors
       │     ├── Products API (api/products.ts)
       │     ├── Industries API (api/industries.ts)
       │     ├── Partners API (api/partners.ts)
       │     ├── Demo API (api/demo.ts)
       │     ├── Contact API (api/contact.ts)
       │     └── Docs API (api/docs.ts)
       │
       ├── Auth Layer (src/lib/auth/)
       │     ├── CyIdentity (cyidentity.ts)      ← OAuth 2.1 / OIDC
       │     ├── PKCE (pkce.ts)                  ← RFC 7636
       │     └── Token Store (tokens.ts)         ← sessionStorage
       │
       ├── Portal Entry Points (portals/)
       │     ├── portal-login.html               → portal.cy-com.com
       │     ├── health-login.html               → health.cy-com.com
       │     └── provider-login.html             → provider.cy-com.com
       │
       ├── Auth Callback (auth/callback.html)
       │
       └── Admin (admin/)
             └── platform-status.html            → /admin/platform-status
```

---

## Quick Start

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your backend URLs and CyIdentity client ID
```

### 3. Build the SDK

```bash
npm run build:all
```

This produces:
- `dist/cybercom-api.js` — bundled SDK for browser use
- `dist/portals/portal.js`, `health.js`, `provider.js` — portal bundles

### 4. Load in HTML

```html
<script src="/dist/cybercom-api.js"></script>
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `CYBERCOM_API_URL` | Platform API base URL | `https://api.cy-com.com` |
| `CYBERCOM_API_VERSION` | API version prefix | `v1` |
| `CYIDENTITY_URL` | CyIdentity OIDC issuer | `https://identity.cy-com.com` |
| `CYIDENTITY_WEBSITE_CLIENT_ID` | OAuth 2.1 public client ID | `cybercom-website-public` |
| `CYIDENTITY_REDIRECT_URI` | OAuth callback URL | `https://cy-com.com/auth/callback` |
| `PORTAL_URL` | Patient portal URL | `https://portal.cy-com.com` |
| `HEALTH_URL` | Health portal URL | `https://health.cy-com.com` |
| `PROVIDER_URL` | Provider portal URL | `https://provider.cy-com.com` |
| `STATUS_REFRESH_INTERVAL` | Health check interval (ms) | `30000` |

See `.env.example` for the full list including per-service health URLs.

---

## TypeScript SDK Usage

### Demo Request Form

```typescript
import { demoApi } from './src/lib';

const form = document.querySelector('#demo-form') as HTMLFormElement;
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const result = await demoApi.submitForm(new FormData(form));
  showSuccess(`Reference: ${result.reference_number}`);
});
```

### Newsletter Sign-Up

```typescript
import { contactApi } from './src/lib';

const result = await contactApi.submitForm('user@example.com', 'footer_newsletter');
// { status: 'subscribed', message: '...' }
```

### Load Products

```typescript
import { productsApi } from './src/lib';

const products = await productsApi.featured();
// renders division cards dynamically
```

### Contact Message

```typescript
import { contactApi } from './src/lib';

const response = await contactApi.send({
  email: 'cto@hospital.com',
  subject: 'Enterprise demo request',
  message: 'We would like to evaluate CyMed for 3,000 beds.',
  department: 'sales',
  company: 'King Faisal Medical City',
});
// { ticket_number: 'CYB-00123', status: 'received' }
```

---

## Authentication (CyIdentity)

### OAuth 2.1 + PKCE Flow

```
1. User clicks "Sign In"
2. website calls cyIdentity.login({ portalHint: 'portal' })
3. Browser redirects → CyIdentity /oauth/authorize (with code_challenge)
4. User authenticates (+ MFA if required)
5. CyIdentity redirects → cy-com.com/auth/callback?code=…&state=…
6. auth/callback.html exchanges code for tokens (PKCE verification)
7. Tokens stored in sessionStorage (access token) + httpOnly cookie (refresh)
8. User redirected to their portal (portal.cy-com.com / health.cy-com.com / provider.cy-com.com)
```

### Token Lifecycle

| Token | Storage | Lifetime | Notes |
|---|---|---|---|
| Access Token | `sessionStorage` | 15 min (default) | Auto-refreshed 30s before expiry |
| Refresh Token | `httpOnly` cookie | 8 hours | Set by CyIdentity — never accessible to JS |
| ID Token | `sessionStorage` | Session | Used for logout (`id_token_hint`) |

### Portal Entry Points

| Portal | URL | Scopes | ACR |
|---|---|---|---|
| Patient / Citizen | `portal.cy-com.com` | `cymed.patient.read` | `portal:portal` |
| Health / Clinical | `health.cy-com.com` | `cymed.clinical.read/write`, `cymed.orders.write` | `portal:health mfa:required` |
| Provider | `provider.cy-com.com` | `cymed.clinical.*`, `cymed.prescriptions.write` | `portal:provider mfa:required device:registered` |

---

## API Endpoints

### Products

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/v1/website/products/` | None | List all products |
| GET | `/v1/website/products/{slug}/` | None | Single product |
| GET | `/v1/website/products/?is_featured=true` | None | Featured products |

### Industries

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/v1/website/industries/` | None | List industries |
| GET | `/v1/website/industries/{slug}/` | None | Industry detail |
| GET | `/v1/website/industries/case-studies/` | None | Case studies |

### Partners

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/v1/website/partners/` | None | Partner directory |
| POST | `/v1/website/partners/apply/` | None | Partner application |

### Demo Requests

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/v1/website/demo-requests/` | None | Submit demo request |
| GET | `/v1/website/demo-requests/availability/` | None | Available slots |
| GET | `/v1/website/demo-requests/{ref}/status/` | None | Request status |

### Contact

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/v1/website/contact/` | None | Send message |
| POST | `/v1/website/contact/newsletter/` | None | Newsletter sign-up |
| GET | `/v1/website/contact/{ticket}/status/` | None | Ticket status |

### Documentation

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/v1/website/docs/` | None | Doc sections |
| GET | `/v1/website/docs/search/?q={query}` | None | Full-text search |
| GET | `/v1/website/docs/releases/` | None | Release notes |

---

## Admin Status Dashboard

**URL:** `https://cy-com.com/admin/platform-status`

Displays real-time health of:
- CyMed (P3.1–P3.9)
- CyCom
- CyGov
- CyIdentity (P2.1)
- CyAI (P2.8)
- CyData (P2.7)
- CyIntegrationHub (P2.6)

Auto-refreshes every 30 seconds. Shows: operational status, response latency, 30-day uptime history.

**Access control:** Restrict to internal IPs in nginx (`allow 10.0.0.0/8; deny all;`).

---

## API Middleware

### Error Handling

All API errors are thrown as `CyberComApiError`:

```typescript
import { CyberComApiError, demoApi } from './src/lib';

try {
  await demoApi.submit(request);
} catch (err) {
  if (err instanceof CyberComApiError) {
    console.log(err.status);    // HTTP status code
    console.log(err.code);      // Platform error code (e.g. VALIDATION_ERROR)
    console.log(err.message);   // Human-readable message
    console.log(err.requestId); // X-Request-Id for support reference
  }
}
```

### Retry Logic

Automatic retry with exponential backoff + jitter:
- Retries on: `429`, `502`, `503`, `504`
- Max attempts: 3
- Base delay: 300ms
- Max delay: 5000ms

### Token Refresh

The middleware automatically refreshes the access token when it expires or when a `401` response is received, using the httpOnly refresh token cookie. The refresh is deduplicated — concurrent requests wait for a single refresh call.

---

## Nginx Configuration

Routes handled:

| Path | Served by |
|---|---|
| `/` | `index.html` |
| `/auth/callback` | `auth/callback.html` |
| `/login/portal` | `portals/portal-login.html` |
| `/login/health` | `portals/health-login.html` |
| `/login/provider` | `portals/provider-login.html` |
| `/admin/platform-status` | `admin/platform-status.html` |
| `/api/*` | Proxied → `https://api.cy-com.com` |
| `/dist/*` | Compiled SDK bundles (7d cache) |

Subdomains:
- `portal.cy-com.com` → `302 /login/portal`
- `health.cy-com.com` → `302 /login/health`
- `provider.cy-com.com` → `302 /login/provider`

---

## Backend Integration (CyberCom-Platform)

The website expects the following Django app to be registered in `CyberCom-Platform`:

```
backend/products/website/
  products/     → GET /v1/website/products/
  industries/   → GET /v1/website/industries/
  partners/     → GET /v1/website/partners/, POST /apply/
  demo/         → POST /v1/website/demo-requests/
  contact/      → POST /v1/website/contact/, /newsletter/
  docs/         → GET /v1/website/docs/, /search/, /releases/
```

All public endpoints are unauthenticated (no JWT required). The backend uses rate limiting (100 req/hour per IP for POST endpoints) and CAPTCHA verification for form submissions.
