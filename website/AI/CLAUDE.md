# AI Knowledge Base — Architecture Rules for Claude Code (Website)

## Repository

**Cybercom-Website** — Turborepo monorepo, Next.js 15, App Router, next-intl, Tailwind CSS.

Branch: `develop` (default working branch)

---

## Mandatory Workflow

Every session:
1. Read this file.
2. Read `WEBSITE.md` — understand page structure and content requirements.
3. Read `BRAND.md` — understand brand identity before writing any UI.
4. Read `UX.md` — understand UX standards before modifying any component.
5. Inspect the specific app/page/component you are about to modify.
6. Search for existing components before creating new ones.

---

## Monorepo Layout

```
apps/
  web/          cy-com.com marketing website (primary)
  docs/         Developer and user documentation site
  partners/     Partner portal application
  portal/       Customer self-service portal
packages/       Shared packages (UI, config, utils)
src/
  lib/          Shared libraries
  portals/      Portal implementations
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| UI Components | Custom + Radix UI primitives |
| Internationalization | next-intl (English + Arabic) |
| Build system | Turborepo |
| Icons | Lucide React |
| Testing | Vitest + Playwright |
| Analytics | (configured at deployment) |

---

## Mandatory Rules

### Internationalization
- Every user-facing string MUST use `next-intl` translation hooks.
- Never hardcode English text in component JSX.
- Messages files in `apps/web/messages/`.
- Arabic (RTL) must render correctly on every component.
- Use `dir={locale === 'ar' ? 'rtl' : 'ltr'}` at layout level.

### SEO
- Every page must export `generateMetadata()`.
- Use `buildMetadata()` from `lib/metadata.ts`.
- Every page must include OpenGraph tags.
- Every page must include JSON-LD structured data where relevant.
- `homepageSeoKeywords` and similar keyword arrays exist in `lib/metadata.ts` — extend, do not duplicate.

### Components
- Never create a new component if an existing one can be extended.
- Reuse from `apps/web/components/sections/` and `apps/web/components/ui/`.
- No duplicate layout components.
- Responsive design is required — mobile-first.

### API Integration
- Dynamic data comes from CyberCom Platform at `/api/v1/public/` endpoints.
- Use the `portal.ts` and `provider.ts` in `app/lib/` for API client.
- Never duplicate API endpoints in the website.
- Handle loading and error states on all API-driven components.

### Performance
- All images use `next/image` with proper `alt` text.
- No unoptimized external images without explicit `unoptimized` justification.
- Lazy-load non-critical sections.
- Target Core Web Vitals: LCP < 2.5s, CLS < 0.1, INP < 200ms.

---

## Pages (apps/web/app/[locale]/)

| Route | File | Purpose |
|-------|------|---------|
| `/` | `page.tsx` | Homepage — hero, product ecosystem, industries, CyMed highlight, global reach, demo CTA |
| `/products` | `products/page.tsx` | Product catalog — all 9 platforms |
| `/industries` | `industries/page.tsx` | Industry verticals |
| `/about` | `about/page.tsx` | Company information |
| `/contact` | `contact/page.tsx` | Contact form |
| `/partners` | `partners/page.tsx` | Partner program |
| `/demo` | `demo/page.tsx` | Demo request form |

---

## Key Sections (apps/web/components/sections/)

| Component | Purpose |
|-----------|---------|
| `Hero` | Homepage hero |
| `ProductEcosystem` | 9-platform overview |
| `IndustriesSection` | Industry verticals |
| `CyMedSection` | Healthcare platform feature highlight |
| `GlobalReach` | International presence |
| `DemoSection` | Demo request CTA |

---

## Commit Standards

Same as platform: Conventional Commits.

Scopes: `web`, `docs`, `partners`, `portal`, `packages`, `config`

Example: `feat(web): add CyMed Hospital product detail page`
