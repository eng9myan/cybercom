# Commercial Platform Report — CyberCom Website
**Date:** 2026-06-29

## Overview

This report documents the commercial platform capabilities exposed through the CyberCom marketing and sales website (`Cybercom-Website`). The website now serves as the full commercial front-end for the CyberCom SaaS platform ecosystem.

## Commercial Pages

### Marketplace (`/marketplace`)
- Public-facing catalog of certified extensions, modules, and connectors
- Categories: modules, extensions, AI packages, connectors, clinical templates, reports
- Featured listings with publisher badges (Official, Verified Partner, Community)
- Publisher CTA for the partner ecosystem
- Statistics: 200+ listings, 45 verified partners, 28K+ installs

### Customer Portal (`/portal`)
- Secure customer lifecycle management hub
- Capabilities: license management, billing, support, downloads, analytics, white-label config
- Role-based access: Viewer, Standard, Admin
- Support SLA matrix: Critical (1h), High (4h), Medium (1 day), Low (2 days)
- Security features: CyIdentity MFA, SSO, full audit trail, tenant isolation

### Partner Portal (`/partner`)
- Authenticated partner dashboard landing page
- Modules: pipeline, deal registration, revenue share, assets, academy, co-marketing
- Four-tier program: Authorized → Silver → Gold → Platinum
- Regional team contacts for Levant, UAE/Gulf, KSA, Egypt/Africa, International

### ROI Calculator (`/tools/roi`)
- Three benchmark scenarios: clinic (50 staff), hospital (500 staff), government ministry
- ROI ranges from 94% to 250% with 3.5–6 month payback periods
- Four key drivers: time savings, revenue improvement, staff efficiency, risk/compliance
- 3-year cumulative return chart (visual, accessible)

### Product Comparison (`/tools/compare`)
- Side-by-side edition comparison: Starter, Professional, Enterprise, Government
- 7 feature categories: Core Platform, Deployment, Users & Capacity, Clinical & Interoperability, Security & Compliance, White Label & Branding, Support
- 30+ individual feature rows with check/dash/text values
- Highlighted Enterprise tier (most popular)

## Navigation

Marketplace added to main navigation between Partners and Documentation — visible on both desktop mega-menu bar and mobile menu.

## API Integration

Four typed API modules connect the website to the Platform backend:
- `licensingApi` — license lifecycle management
- `marketplaceApi` — marketplace catalog and installations
- `portalApi` — customer portal operations
- `partnerApi` — partner ecosystem management
