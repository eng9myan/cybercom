# Partner Portal Guide — CyberCom Website Integration
**Date:** 2026-06-29

## Overview

The CyberCom Partner Portal is the dedicated dashboard for authorized implementation, reseller, and technology partners. The `/partner` page on the website serves as the landing and sign-in gateway for partners.

## API Module: `packages/api/src/partner.ts`

### Types

**`PartnerProfile`** — Full authenticated partner organization record  
Key fields: `name`, `partner_type` (implementation/reseller/technology/consulting/oem), `tier` (authorized/silver/gold/platinum), `status`, `country`, `region`, `specializations`, `annual_revenue_target`

**`PartnerOpportunity`** — Sales opportunity registered by a partner  
Key fields: `partner`, `name`, `stage` (prospecting → closed_won/lost), `customer_name`, `customer_country`, `products_of_interest`, `estimated_value`, `expected_close_date`

**`RevenueShare`** — Commission payment record for a partner  
Key fields: `partner`, `period_start`, `period_end`, `gross_revenue`, `share_percentage`, `share_amount`, `status` (pending/approved/paid), `paid_at`

**`PartnerAsset`** — A marketing or training asset available to partners  
Key fields: `title`, `asset_type` (brochure/presentation/video/case_study/whitepaper/logo/training/contract_template), `tier_access`, `language`, `file_url`, `version`

**`DealRegistration`** — A formal deal registration for protection and uplift  
Key fields: `partner`, `customer_name`, `customer_country`, `products_interested`, `estimated_value`, `status` (submitted/approved/rejected/expired/converted), `expiry_date`

### API Methods

| Method | Description |
|--------|-------------|
| `getPartners(params?)` | List partner profiles (admin use) |
| `getPartner(id)` | Get partner profile |
| `getOpportunities(params?)` | List pipeline opportunities |
| `createOpportunity(body)` | Register new opportunity |
| `getRevenueShares(params?)` | List revenue share statements |
| `getAssets(params?)` | Browse partner asset library |
| `getDealRegistrations(params?)` | List deal registrations |
| `registerDeal(body)` | Submit new deal registration |
| `applyForPartnership(body)` | Public endpoint — apply to join partner program |

## Partner Tiers

| Tier | Requirements | Key Benefits |
|------|-------------|-------------|
| Authorized | 1 trained staff, 1 deal/year | Directory listing, basic assets, training access |
| Silver | 2 certified staff, $50K ARR, 6 months | Co-marketing budget, lead sharing, pre-sales support |
| Gold | 4 certified staff, $200K ARR, 12 months | Dedicated partner manager, demo env, priority SLA |
| Platinum | 6 certified staff, $500K ARR, exec alignment | Joint GTM, 5% revenue uplift, executive sponsor |

## Page: `/partner`

The `/partner` marketing page includes:
- Hero with partner sign-in CTA (`NEXT_PUBLIC_PORTAL_URL/partner`)
- 6 portal module cards: Pipeline, Deal Registration, Revenue, Assets, Academy, Co-Marketing
- Tier matrix table with requirements and benefits
- 5 regional contact sections (Levant, UAE/Gulf, KSA, Egypt/Africa, International)
- Partnership application CTA linking to `/partners`
