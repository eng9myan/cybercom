# CyberCom Website API Integration

**Program 3.10** — Frontend API Reference

This document covers how the Cybercom-Website frontend integrates with the CyberCom Platform public APIs.

---

## API Client

The `@cybercom/api` package provides a typed TypeScript client for all public platform APIs.

### Base Configuration

```typescript
// packages/api/src/client.ts
const client = new CyberComApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL ?? "https://api.cy-com.com",
});
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | CyberCom Platform API base URL |
| `NEXT_PUBLIC_PORTAL_URL` | No | Portal subdomain URL |
| `NEXT_PUBLIC_PROVIDER_URL` | No | Provider portal URL |
| `NEXT_PUBLIC_PATIENT_URL` | No | Patient portal URL |
| `NEXT_PUBLIC_SITE_URL` | No | Main site URL for canonical links |

---

## Products API

```typescript
import { productsApi } from "@cybercom/api";

// List all products
const products = await productsApi.list({ category: "healthcare" });

// Get a specific product
const cymed = await productsApi.get("cymed-hospital");

// Homepage featured products
const featured = await productsApi.featured();
```

**Server Component Example (ISR cached)**:
```typescript
// app/[locale]/products/page.tsx
export default async function ProductsPage() {
  // Cached for 5 minutes via Next.js fetch cache
  const products = await productsApi.list();
  return <ProductGrid products={products.data} />;
}
```

---

## Demo Request API

```typescript
import { demoApi } from "@cybercom/api";

const result = await demoApi.submit({
  full_name: "Sara Al-Nour",
  email: "sara@hospital.sa",
  job_title: "CIO",
  company: "King Faisal Medical City",
  company_size: "1001+",
  country: "Saudi Arabia",
  product_interests: ["CyMed Hospital", "CyMed Pharmacy"],
  gdpr_consent: true,
});

// Returns: { reference_number: "CYB-481923", status: "pending", ... }
```

**Validation rules** (enforced server-side):
- `email`: Rejects disposable email providers
- `product_interests`: At least one required
- `gdpr_consent`: Must be `true`

**Rate limit**: 5 requests/hour per IP

---

## Contact API

```typescript
import { contactApi } from "@cybercom/api";

// Contact form
const contact = await contactApi.send({
  full_name: "Mohammed Al-Rashid",
  email: "mohammed@company.com",
  subject: "Enterprise Pricing",
  message: "We are evaluating CyMed for our hospital network.",
  department: "sales",
  gdpr_consent: true,
});

// Newsletter subscription
const sub = await contactApi.subscribeNewsletter({
  email: "user@company.com",
  source: "footer",
  gdpr_consent: true,
});
```

---

## Partners API

```typescript
import { partnersApi } from "@cybercom/api";

// Partner directory
const partners = await partnersApi.list({ country: "Saudi Arabia" });

// Submit partner application
const application = await partnersApi.submitApplication({
  company_name: "AlSharq Consulting",
  contact_name: "Khalid Al-Rashid",
  email: "khalid@alsharq.sa",
  country: "Saudi Arabia",
  partner_type: "implementation",
  expertise_areas: ["CyMed", "CyGov"],
  gdpr_consent: true,
});

// Returns: { reference_number: "PAR-123456", status: "pending", ... }
```

---

## Documentation API

```typescript
import { docsApi } from "@cybercom/api";

// List all documentation sections
const sections = await docsApi.listSections();

// Get a section with its items
const section = await docsApi.getSection("cymed-getting-started");

// Search documentation
const results = await docsApi.search("FHIR integration", {
  product: "cymed",
  content_type: "guide",
});
```

---

## Error Handling

All API methods throw a typed `ApiError` on failure:

```typescript
import { type ApiError } from "@cybercom/api";

try {
  await demoApi.submit(formData);
} catch (error) {
  const apiErr = error as ApiError;
  // apiErr.status — HTTP status code
  // apiErr.errors — field-level validation errors
  // apiErr.errors.email — ["Enter a valid email address."]
}
```

**Rate limit handling** (HTTP 429):
```typescript
catch (error) {
  const apiErr = error as ApiError;
  if (apiErr.status === 429) {
    // Show rate limit message with Retry-After guidance
    setError("Too many requests. Please try again in an hour.");
  }
}
```

---

## Caching Strategy

| Request type | Cache | Strategy |
|-------------|-------|----------|
| `productsApi.list()` | `next: { revalidate: 300 }` | ISR - 5 min |
| `industriesApi.list()` | `next: { revalidate: 300 }` | ISR - 5 min |
| `docsApi.listSections()` | `next: { revalidate: 300 }` | ISR - 5 min |
| Form submissions | No cache | `POST` requests |
| `docsApi.search()` | No cache | Dynamic per query |

---

## CyIdentity Integration

Portal and partner portals use CyIdentity OAuth 2.1 + PKCE:

### Authorization Flow (PKCE)

```javascript
// 1. Generate code verifier and challenge
const verifier = generateCodeVerifier(); // 64-byte random string
const challenge = await sha256base64url(verifier);

// 2. Store verifier
sessionStorage.setItem("cy_pkce_verifier", verifier);
sessionStorage.setItem("cy_oauth_state", state);

// 3. Redirect to CyIdentity
const authUrl = `https://id.cy-com.com/oauth/authorize?` +
  `client_id=${clientId}&` +
  `redirect_uri=${encodeURIComponent(callbackUrl)}&` +
  `response_type=code&` +
  `scope=${encodeURIComponent(scopes)}&` +
  `state=${state}&` +
  `code_challenge=${challenge}&` +
  `code_challenge_method=S256`;

window.location.href = authUrl;
```

### Token Exchange (`auth/callback.html`)

```javascript
// 4. On callback: validate state, exchange code
const { code, state } = new URLSearchParams(window.location.search);
const verifier = sessionStorage.getItem("cy_pkce_verifier");

const response = await fetch("https://id.cy-com.com/oauth/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({
    grant_type: "authorization_code",
    client_id: clientId,
    code,
    redirect_uri: callbackUrl,
    code_verifier: verifier,
  }),
  credentials: "include", // for httpOnly refresh cookie
});

const { access_token, id_token, expires_in } = await response.json();
sessionStorage.setItem("cy_access_token", access_token);
```

### Portal Scopes

| Portal | ACR | Scopes |
|--------|-----|--------|
| Customer Portal | `portal:customer` | `openid profile email customer.licenses customer.downloads support.tickets` |
| Partner Portal | `portal:partner` | `openid profile email partner.leads partner.kits` |
| Health Portal (Patient) | `portal:health` | `openid profile email cymed.patient.read cymed.appointments.write` |
| Health Portal (Provider) | `portal:health mfa:required` | + `cymed.clinical.read cymed.prescriptions.write` |
| Provider Portal | `portal:provider mfa:required device:registered` | All clinical scopes |
