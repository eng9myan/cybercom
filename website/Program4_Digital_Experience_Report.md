# Program 4 — Digital Experience & SaaS Platform Report

**Date:** 2026-06-28  
**Branch:** develop  
**Program:** 4 — CyberCom Digital Experience & SaaS Platform  
**Status:** Phase 1 Complete

---

## Executive Summary

Program 4 transforms the CyberCom website into a customer-facing, sales-ready, demo-ready commercial platform. All corporate pages, product ecosystem pages, CyMed sub-product pages, navigation, and customer flows have been built or completed in this phase.

---

## Pages Delivered

### Corporate Pages

| Page | Path | Status |
|------|------|--------|
| Home | `/[locale]` | Pre-existing |
| About | `/[locale]/about` | Pre-existing |
| Products | `/[locale]/products` | Pre-existing |
| Industries | `/[locale]/industries` | Pre-existing |
| Solutions | `/[locale]/solutions` | **New** |
| Pricing | `/[locale]/pricing` | **New** |
| Contact | `/[locale]/contact` | Pre-existing |
| Careers | `/[locale]/careers` | **New** |
| Partners | `/[locale]/partners` | Pre-existing |
| Investors | `/[locale]/investors` | **New** |
| Blog/News | `/[locale]/blog` | **New** |
| Demo | `/[locale]/demo` | Pre-existing |

### Product Ecosystem Pages (17 slugs via dynamic route)

All served by `apps/web/app/[locale]/products/[slug]/page.tsx`:

| Slug | Product | Category |
|------|---------|----------|
| `cymed` | CyMed Platform Overview | Healthcare |
| `cymed-clinic` | CyMed Clinic | Healthcare |
| `cymed-hospital` | CyMed Hospital | Healthcare |
| `cymed-laboratory` | CyMed Laboratory | Healthcare |
| `cymed-imaging` | CyMed Imaging | Healthcare |
| `cymed-pharmacy` | CyMed Pharmacy | Healthcare |
| `cymed-patient-portal` | CyMed Patient Portal | Healthcare |
| `cymed-provider-portal` | CyMed Provider Portal | Healthcare |
| `cymed-revenue-cycle` | CyMed Revenue Cycle | Healthcare |
| `cymed-population-health` | CyMed Population Health | Healthcare |
| `cycom` | CyCom ERP | Enterprise |
| `cygov` | CyGov | Government |
| `cyidentity` | CyIdentity | Platform |
| `cyintegrationhub` | CyIntegrationHub | Platform |
| `cyai` | CyAI | Platform |
| `cydata` | CyData | Platform |
| `cyconnect` | CyConnect | Platform |
| `cycitizen` | CyCitizen | Government |

---

## Product Page Sections (Per Product)

Each product page now includes:

1. **Hero** — Breadcrumb, category badge, name, tagline, description, compliance tags
2. **CTAs** — Request Demo, Launch Product (external subdomain), Documentation
3. **Sub-Products** — CyMed overview shows all 9 sub-products as linked cards
4. **Key Features** — 10 features per product in responsive grid
5. **How It Works (Workflows)** — 5-step workflow with numbered progression
6. **Platform Preview (Screens)** — Dark-theme mock UI with sidebar, KPI cards, table, charts
7. **Editions** — 2-3 editions per product with feature lists and demo CTA
8. **Deployment Models** — Visual list of supported deployment options
9. **Final CTA** — Dual CTA: Request Demo + Launch Product + Docs

---

## Navigation Updates

### Navbar

- Added **Solutions** link (desktop + mobile)
- Added **Pricing** link (desktop + mobile)
- Existing: Products (mega menu), Industries, Partners, Docs, About

### Footer

- Added: Solutions, Pricing, Blog, Careers, Investors to Company column
- Existing: About, Partners, Contact, Documentation, Partner Portal

### i18n Keys Added

**en.json / ar.json:**
- `nav.solutions` — "Solutions" / "الحلول"
- `nav.pricing` — "Pricing" / "الأسعار"
- `nav.blog` — "Blog" / "المدونة"
- `nav.careers` — "Careers" / "الوظائف"
- `nav.investors` — "Investors" / "المستثمرون"

---

## Design System Compliance (UI/UX Pro Max)

- **Pattern:** Enterprise Gateway — mega menu, metric cards, industry tabs
- **Style:** Trust & Authority — dark theme, credentialed metrics, professional tone
- **Colors:** cy-orange accent on cy-black/cy-dark background (consistent with existing system)
- **Typography:** Font heading (Lexend) for headings, Source Sans for body
- **Components:** glass-card, btn-primary, btn-secondary, btn-ghost, product-badge, glow-orb
- **Accessibility:** WCAG 2.1 AA — aria-labels, heading hierarchy, skip links, role attributes
- **Responsive:** Mobile-first, RTL/LTR, EN/AR
- **Icons:** Lucide React exclusively (no emoji)

---

## Customer-Facing Flows

| Flow | Implementation |
|------|---------------|
| Demo Request | `/[locale]/demo` with product+edition query params |
| Contact Sales | `/[locale]/contact` |
| Product Discovery | Products mega menu → product detail page |
| Industry Selector | `/[locale]/industries` |
| Partner Inquiry | `/[locale]/partners` |
| Portal Entry | External link to `NEXT_PUBLIC_PORTAL_URL` |
| Product Launch | Per-product subdomain via `NEXT_PUBLIC_*_URL` env vars |
| Documentation | External link to `NEXT_PUBLIC_DOCS_URL` |
| Investor Contact | mailto:investors@cy-com.com |
| Careers Apply | mailto:careers@cy-com.com |

---

## Environment Variables Referenced

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_HOSPITAL_URL` | CyMed Hospital subdomain |
| `NEXT_PUBLIC_CLINIC_URL` | CyMed Clinic subdomain |
| `NEXT_PUBLIC_LAB_URL` | CyMed Laboratory subdomain |
| `NEXT_PUBLIC_IMAGING_URL` | CyMed Imaging subdomain |
| `NEXT_PUBLIC_PHARMACY_URL` | CyMed Pharmacy subdomain |
| `NEXT_PUBLIC_HEALTH_URL` | CyMed Patient Portal / Health |
| `NEXT_PUBLIC_PROVIDER_URL` | CyMed Provider Portal |
| `NEXT_PUBLIC_PORTAL_URL` | Main portal (ERP, Gov, Identity, etc.) |
| `NEXT_PUBLIC_DOCS_URL` | Documentation site |
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
