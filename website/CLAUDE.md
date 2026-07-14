# Cybercom Website — Claude Code Primary Guide

## Start Here

Before making any change:

1. Read `AI/CLAUDE.md` for architecture rules.
2. Read `AI/WEBSITE.md` for page structure and content rules.
3. Read `AI/BRAND.md` for brand identity and design system.
4. Read `AI/UX.md` for UX standards.
5. Inspect the repository. Treat existing code as source of truth.

---

## Mission

The Cybercom Website is the commercial front door for CyberCom Revolution.
It must present 9 integrated enterprise platforms professionally, generate qualified leads,
and support sales, partners, documentation, and customer portals.

---

## Repository Layout

```
apps/
  web/          Public marketing website (Next.js 15, App Router, next-intl)
  docs/         Documentation site
  partners/     Partner portal
  portal/       Customer portal
packages/       Shared UI, config, utilities
src/
  lib/          Shared libraries
  portals/      Portal implementations
```

---

## Non-Negotiable Rules

1. **Inspect before writing.** Read existing components and pages before creating new ones.
2. **Reuse components.** Never duplicate UI components. Extend what exists.
3. **No hardcoded brand.** All branding via brand tokens and theme system.
4. **Bilingual always.** Every user-facing string must use next-intl. Support English and Arabic (RTL).
5. **SEO on every page.** Every page needs metadata, OpenGraph, and structured data.
6. **Production-only.** No placeholder content, no lorem ipsum, no mock data.
7. **API from Platform.** All dynamic data from CyberCom Platform public APIs at `/api/v1/public/`.
8. **Performance first.** Core Web Vitals matter. No unoptimized images. No layout shift.
9. **Accessibility.** WCAG 2.1 AA minimum on all pages.
10. **No duplicate portals.** Each portal (customer, partner, docs) lives in its own app.

---

## Products to Represent

CyMed (Clinic, Hospital, Laboratory, Imaging, Pharmacy, Patient Portal, Provider Portal, Revenue Cycle, Population Health)
CyCom ERP, CyGov, CyCitizen, CyAI, CyData, CyIdentity, CyIntegrationHub, CyConnect

---

## Before Finishing Any Task

Validate:
- All strings use next-intl
- SEO metadata present
- No layout regressions
- Both RTL (Arabic) and LTR (English) render correctly
- Conventional Commits format for any commit
