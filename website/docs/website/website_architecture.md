# CyberCom Website Architecture

**Program**: 3.10 — CyberCom Digital Experience Platform  
**Production Domain**: www.cy-com.com  
**Repository**: https://github.com/eng9myan/Cybercom-Website

---

## Overview

The CyberCom Website is a **Turborepo monorepo** containing four Next.js 15 applications, two shared packages, and legacy assets. It powers the CyberCom commercial presence across four sub-domains.

---

## Monorepo Structure

```
Cybercom-Website/
├── apps/
│   ├── web/          → www.cy-com.com (marketing site)
│   ├── portal/       → portal.cy-com.com (customer portal)
│   ├── partners/     → partners.cy-com.com (partner portal)
│   └── docs/         → docs.cy-com.com (documentation)
├── packages/
│   ├── ui/           → Shared component library
│   ├── api/          → API client (wraps CyberCom Platform APIs)
│   └── config/       → Shared Tailwind, TypeScript, ESLint configs
├── src/              → Legacy TypeScript SDK (preserved)
├── auth/             → OAuth 2.1 PKCE callback (vanilla HTML, preserved)
├── portals/          → Portal login pages (vanilla HTML, preserved)
└── nginx/            → Nginx configuration
```

---

## Application Architecture

### apps/web — Marketing Site (www.cy-com.com)

**Framework**: Next.js 15, App Router, Server Components  
**Routing**: `app/[locale]/*` (next-intl for EN/AR)

| Route | Description |
|-------|-------------|
| `/[locale]` | Homepage with all marketing sections |
| `/[locale]/products` | Products catalog |
| `/[locale]/products/[slug]` | Product detail page |
| `/[locale]/industries` | Industries landing |
| `/[locale]/industries/[slug]` | Industry detail |
| `/[locale]/demo` | Demo request form |
| `/[locale]/contact` | Contact form |
| `/[locale]/about` | About CyberCom |
| `/[locale]/partners` | Partner program landing |
| `/[locale]/legal/*` | Legal pages |

**Homepage Sections** (rendered in order):
1. `Hero` — Animated hero with headline, CTAs, compliance badges, stats
2. `ProductEcosystem` — 9-product interactive grid
3. `IndustriesSection` — 8 industry cards
4. `CyMedSection` — Healthcare platform spotlight
5. `GlobalReach` — Stats, deployment options, CTA strip
6. `DemoSection` — Integrated demo request form

**Internationalization**: next-intl, `messages/en.json` + `messages/ar.json`, RTL support for Arabic

### apps/portal — Customer Portal (portal.cy-com.com)

**Auth**: CyIdentity OAuth 2.1 + PKCE  
**Scopes**: `openid profile email customer.licenses customer.downloads support.tickets`

| Section | Description |
|---------|-------------|
| Dashboard | Overview, active licenses, open tickets |
| Licenses | License management, download certificates |
| Downloads | Software installers, updates, documentation |
| Deployments | Deployment tracking |
| Support Tickets | Ticket creation and tracking |
| Training | Training catalog and progress |

### apps/partners — Partner Portal (partners.cy-com.com)

**Public pages**: Partner landing, Application form  
**Auth**: CyIdentity OAuth 2.1

| Section | Description |
|---------|-------------|
| Dashboard | Partner tier, pipeline, quick actions |
| Leads | Lead registration, tracking |
| Sales Kits | Downloadable sales assets |
| Certifications | Training and certification tracking |
| Marketing Kits | Co-branded marketing assets |

### apps/docs — Documentation (docs.cy-com.com)

**Content source**: CyberCom Platform API (`/api/v1/public/documentation/`)  
**Features**: Full-text search, section navigation, content type filtering, MDX support

---

## Shared Packages

### @cybercom/api

TypeScript client wrapping all public CyberCom Platform APIs:

```typescript
// Base URL: https://api.cy-com.com/api/v1/public/
productsApi.list()         // GET /products/
productsApi.get(slug)      // GET /products/{slug}/
industriesApi.list()       // GET /industries/
demoApi.submit(payload)    // POST /demo-request/
contactApi.send(payload)   // POST /contact/
contactApi.subscribeNewsletter() // POST /contact/newsletter/
partnersApi.list()         // GET /partners/
partnersApi.submitApplication() // POST /partners/apply/
docsApi.listSections()     // GET /documentation/
docsApi.search(q)          // GET /documentation/search/
```

All reads: `next: { revalidate: 300 }` (5-minute ISR cache)

### @cybercom/ui

Reusable React component library:
- `Button` — variant: primary/secondary/ghost/destructive
- `Card` — glassmorphism card with optional hover state
- `Badge` — status/category badge with color variants
- `Input` — form input with label, error, and aria support

### @cybercom/config

Shared configuration:
- `tailwind/index.js` — CyberCom design system tokens
- `typescript/base.json` — Base TypeScript config
- `typescript/nextjs.json` — Next.js TypeScript config

---

## Design System

### Visual Language
- **Style**: Liquid Glass (glassmorphism on dark background)
- **Mode**: Dark-first with full dark mode
- **Inspiration**: OpenAI, Stripe, Vercel, Linear

### Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| `cy-black` | `#0a0a0f` | Page background |
| `cy-dark` | `#0f0f1a` | Section backgrounds |
| `cy-orange` | `#ED6C00` | Primary CTA, accent |
| `cy-cyan` | `#59c3e1` | Secondary accent |
| `cy-glass-bg` | `rgba(255,255,255,0.04)` | Card background |
| `cy-glass-border` | `rgba(255,255,255,0.08)` | Card border |

### Typography
- **Headings**: Lexend (corporate, trustworthy, accessible)
- **Body**: Source Sans 3 (professional, readable)
- **Code**: JetBrains Mono
- **Arabic**: Noto Sans Arabic (RTL support)

### Component Classes
- `.glass-card` — glassmorphism card with hover shadow
- `.btn-primary` — orange CTA button with glow on hover
- `.btn-secondary` — glass border button
- `.btn-ghost` — transparent hover button
- `.form-input` — dark glass form input
- `.text-gradient` — orange-to-cyan gradient text
- `.section-container` — max-w-7xl centered container
- `.glow-orb` — decorative background glow element

---

## API Integration

All client-side data fetching goes through `@cybercom/api`:

```typescript
// Server Component (ISR cached)
const products = await productsApi.featured();

// Client Component (React Query)
const { data } = useQuery({
  queryKey: ['products'],
  queryFn: () => productsApi.list(),
});

// Form submission
const result = await demoApi.submit(formData);
```

**Rate limits** enforced server-side:
- Read endpoints: 600/hour per IP
- Demo requests: 5/hour per IP
- Contact: 10/hour per IP
- Partner applications: 3/hour per IP

---

## Security

- **Headers**: HSTS, X-Frame-Options, CSP, X-Content-Type-Options (via nginx + Next.js)
- **OAuth 2.1**: PKCE code challenge for all authenticated portals
- **Token storage**: Access token in sessionStorage, refresh via httpOnly cookie
- **API keys**: All via environment variables, never in client code
- **GDPR**: Consent checkbox required for all lead forms; consent stored with submission

---

## Environment Variables

### apps/web
```env
NEXT_PUBLIC_API_URL=https://api.cy-com.com
NEXT_PUBLIC_SITE_URL=https://www.cy-com.com
NEXT_PUBLIC_PORTAL_URL=https://portal.cy-com.com
NEXT_PUBLIC_DOCS_URL=https://docs.cy-com.com
NEXT_PUBLIC_PARTNERS_URL=https://partners.cy-com.com
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_CLARITY_ID=xxxxxxxxxx
```

### apps/portal
```env
NEXT_PUBLIC_API_URL=https://api.cy-com.com
NEXT_PUBLIC_PORTAL_URL=https://portal.cy-com.com
NEXT_PUBLIC_IDENTITY_URL=https://id.cy-com.com
NEXT_PUBLIC_PORTAL_CLIENT_ID=portal-client-id
NEXTAUTH_SECRET=<secret>
NEXTAUTH_URL=https://portal.cy-com.com
```

### apps/partners
```env
NEXT_PUBLIC_API_URL=https://api.cy-com.com
NEXT_PUBLIC_PARTNERS_URL=https://partners.cy-com.com
NEXT_PUBLIC_IDENTITY_URL=https://id.cy-com.com
NEXT_PUBLIC_PARTNERS_CLIENT_ID=partners-client-id
NEXTAUTH_SECRET=<secret>
NEXTAUTH_URL=https://partners.cy-com.com
```

---

## Build & Development

```bash
# Install dependencies
npm install

# Development (all apps)
npm run dev

# Development (specific app)
cd apps/web && npm run dev

# Build all
npm run build

# Run tests
npm run test

# Run E2E tests
cd apps/web && npm run test:e2e

# Type check
npm run typecheck
```

---

## Deployment

Each app deploys independently to its sub-domain:

| App | Domain | Deploy Target |
|-----|--------|---------------|
| apps/web | www.cy-com.com | Vercel / Docker |
| apps/portal | portal.cy-com.com | Vercel / Docker |
| apps/partners | partners.cy-com.com | Vercel / Docker |
| apps/docs | docs.cy-com.com | Vercel / Docker |

Nginx config: `nginx/cy-com.com.conf`
