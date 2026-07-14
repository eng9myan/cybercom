# Website Roadmap

## Completed

### Turborepo Monorepo Setup
- apps/web (Next.js 15 App Router)
- apps/docs (documentation)
- apps/partners (partner portal)
- apps/portal (customer portal)
- Turbo pipeline configuration
- Shared packages structure

### apps/web — Core Pages
- Homepage with Hero, ProductEcosystem, IndustriesSection, CyMedSection, GlobalReach, DemoSection
- Products catalog page (all 9 platforms listed by category)
- Industries page
- About page
- Contact page
- Partners page
- Demo request page

### Technical Foundation
- Next.js 15 App Router with TypeScript
- next-intl internationalization (English + Arabic)
- Tailwind CSS dark theme
- SEO metadata system (`lib/metadata.ts`)
- JSON-LD structured data on homepage
- CyberCom Platform API client (`lib/portal.ts`)
- Turbo build system

### Infrastructure
- CNAME → cy-com.com
- Nginx configuration
- GitHub Actions auto-deploy pipeline
- Oracle Cloud / EC2 deploy scripts

---

## Release 2.1 — Product Detail Pages (Priority)

Build individual product detail pages for all 17 products:

**CyMed Healthcare:**
- [ ] `/products/cymed-clinic`
- [ ] `/products/cymed-hospital`
- [ ] `/products/cymed-laboratory`
- [ ] `/products/cymed-imaging`
- [ ] `/products/cymed-pharmacy`
- [ ] `/products/cymed-patient-portal`
- [ ] `/products/cymed-provider-portal`
- [ ] `/products/cymed-revenue-cycle`
- [ ] `/products/cymed-population-health`

**Enterprise:**
- [ ] `/products/cycom`
- [ ] `/products/cygov`
- [ ] `/products/cycitizen`

**Intelligence:**
- [ ] `/products/cyai`
- [ ] `/products/cydata`
- [ ] `/products/cyidentity`
- [ ] `/products/cyintegrationhub`
- [ ] `/products/cyconnect`

Each page: headline, value proposition, capabilities, clinical standards (if applicable), demo CTA.

---

## Release 2.2 — Documentation Site

- [ ] Installation guide (Docker, Kubernetes, Helm)
- [ ] Administrator guide (tenant setup, monitoring, backup)
- [ ] User guides per CyMed product
- [ ] API reference (embed/link to Swagger UI)
- [ ] FHIR/HL7/DICOM integration guides
- [ ] Release notes
- [ ] Video tutorials (embed)

---

## Release 2.3 — Portals

- [ ] Customer portal: license management, support tickets, billing
- [ ] Partner portal: partner dashboard, resources, deal registration
- [ ] Both portals: Keycloak OIDC authentication

---

## Release 2.4 — Marketing Enhancement

- [ ] Case studies page and content
- [ ] Blog / news section
- [ ] Newsletter management (connect to platform API)
- [ ] Chat widget (CyAI-powered lead qualification)
- [ ] A/B testing setup
- [ ] Analytics integration (privacy-compliant)
- [ ] Pricing page (configurable, not hardcoded)
- [ ] Comparison pages (vs. competitors)

---

## Release 2.5 — SEO & Performance

- [ ] Auto-generated sitemap
- [ ] robots.txt
- [ ] Image optimization audit
- [ ] Core Web Vitals audit and optimization
- [ ] hreflang verification
- [ ] Google Search Console setup
- [ ] Structured data audit

---

## Technology Notes

- Framework stays Next.js 15 — no migration planned
- i18n stays next-intl — extend messages files when adding content
- Styling stays Tailwind CSS — extend design tokens, do not add CSS-in-JS
- Add analytics only with privacy-compliant tools (not GA4 in EU/GDPR regions without consent)
