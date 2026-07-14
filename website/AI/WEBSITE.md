# Website Reference

## Purpose

`cy-com.com` is the commercial marketing website for CyberCom Revolution.

It must:
- Establish CyberCom as a credible enterprise software company
- Present 9 integrated platforms clearly and professionally
- Generate qualified demo requests and sales inquiries
- Support partner acquisition
- Link to documentation, customer portal, and partner portal
- Work in English and Arabic (RTL)

---

## Site Architecture

### apps/web — cy-com.com Marketing Site

```
app/
  layout.tsx              Root layout (fonts, providers)
  [locale]/
    layout.tsx            Locale layout (nav, footer)
    page.tsx              Homepage
    products/page.tsx     Product catalog
    industries/page.tsx   Industry verticals
    about/page.tsx        Company page
    contact/page.tsx      Contact form
    partners/page.tsx     Partner program
    demo/page.tsx         Demo request

components/
  sections/               Page section components
    Hero.tsx
    ProductEcosystem.tsx
    IndustriesSection.tsx
    CyMedSection.tsx
    GlobalReach.tsx
    DemoSection.tsx
  ui/                     Reusable UI primitives
  layout/                 Nav, Footer, etc.

lib/
  metadata.ts             SEO metadata builder + keyword maps
  i18n.ts                 Locale types and config
  portal.ts               CyberCom Platform API client
  provider.ts             React context providers
  health.ts               Platform health check

messages/
  en.json                 English strings
  ar.json                 Arabic strings
```

---

### apps/docs — Documentation Site

Product documentation, API references, installation guides, administrator guides, user guides.

**Content requirements:**
- Installation guide (Docker, Kubernetes, Helm)
- Administrator guide (tenant provisioning, configuration, monitoring)
- User guide per product (CyMed Clinic, Hospital, etc.)
- API reference (link to `/api/docs/` on platform)
- Integration guides (FHIR, HL7, DICOM)
- Release notes

---

### apps/partners — Partner Portal

Partner program information, partner application, partner login, partner resources.

**Content requirements:**
- Partner tiers (Silver, Gold, Platinum)
- Benefits per tier
- Partner application form → Platform API `/api/v1/public/partner-applications/`
- Partner login (redirect to CyIdentity)

---

### apps/portal — Customer Self-Service Portal

Authenticated customer portal for license management, support tickets, and documentation access.

**Integration:** Authenticates via CyIdentity (Keycloak) OIDC.

---

## Content Requirements Per Page

### Homepage (`/`)
- Hero: headline, subheadline, primary CTA (Request Demo), secondary CTA (View Products)
- Product ecosystem overview: all 9 platforms, visual architecture
- Industry verticals: Healthcare, Government, Enterprise
- CyMed flagship highlight: FHIR, ICD-11, clinical capabilities
- Global reach: deployment regions, language support
- Demo request CTA section

### Products Page (`/products`)
- All 9 platforms with descriptions
- Grouped by category (Healthcare, Enterprise, Intelligence & Data, Platform)
- Each product links to individual product detail page (or anchor)
- Clear differentiation between products

### Individual Product Pages
One page per product minimum:
- CyMed Clinic, CyMed Hospital, CyMed Laboratory, CyMed Imaging, CyMed Pharmacy
- CyMed Patient Portal, CyMed Provider Portal, CyMed Revenue Cycle, CyMed Population Health
- CyCom ERP, CyGov, CyCitizen
- CyAI, CyData, CyIdentity, CyIntegrationHub, CyConnect

Each page includes:
- Product headline and value proposition
- Key capabilities (feature list)
- Clinical/regulatory standards (where applicable)
- Screenshot or UI preview
- Demo request CTA

### Industries Page (`/industries`)
- Healthcare (Hospitals, Clinics, Labs, Imaging, Pharmacies)
- Government (Health ministries, Public health agencies)
- Enterprise (ERP for any industry)

### About Page (`/about`)
- Company mission
- Products overview
- Technology approach
- Team/company description

### Contact Page (`/contact`)
- Contact form → Platform API `/api/v1/public/contact/`
- Regional office information
- Support email

### Demo Page (`/demo`)
- Demo request form → Platform API `/api/v1/public/demo-requests/`
- Fields: name, email, company, phone, product interest, message, GDPR consent
- Thank you confirmation on submission

### Partners Page (`/partners`)
- Partner program overview
- Tier benefits
- Partner application form → Platform API `/api/v1/public/partner-applications/`

---

## Platform API Integration

CyberCom-Website connects to CyberCom-Platform public APIs:

| Action | Platform API Endpoint |
|--------|----------------------|
| Demo request | `POST /api/v1/public/demo-requests/` |
| Contact form | `POST /api/v1/public/contact/` |
| Newsletter signup | `POST /api/v1/public/newsletter/subscribe/` |
| Partner application | `POST /api/v1/public/partner-applications/` |
| Platform health | `GET /api/v1/public/health/` |
| Product listing | `GET /api/v1/public/products/` |
| Case studies | `GET /api/v1/public/case-studies/` |
| Industry content | `GET /api/v1/public/industries/` |

All API calls via client in `apps/web/lib/portal.ts`.

---

## Missing Pages (To Be Built)

The following product detail pages are listed in the products catalog but do not yet have dedicated pages:

- `/products/cymed-clinic`
- `/products/cymed-hospital`
- `/products/cymed-laboratory`
- `/products/cymed-imaging`
- `/products/cymed-pharmacy`
- `/products/cymed-patient-portal`
- `/products/cymed-provider-portal`
- `/products/cymed-revenue-cycle`
- `/products/cymed-population-health`
- `/products/cycom`
- `/products/cygov`
- `/products/cycitizen`
- `/products/cyai`
- `/products/cydata`
- `/products/cyidentity`
- `/products/cyintegrationhub`
- `/products/cyconnect`

These are the primary build target for Release 2.1.
