# Marketplace Guide — CyberCom Website Integration
**Date:** 2026-06-29

## Overview

The CyberCom Marketplace is the distribution channel for certified extensions to the CyberCom platform ecosystem. It includes modules, connectors, AI packages, clinical templates, and community extensions.

## API Module: `packages/api/src/marketplace.ts`

### Types

**`MarketplaceListing`** — A published extension in the marketplace  
Key fields: `code`, `name`, `category`, `product_codes`, `publisher`, `publisher_type` (official/partner/community), `version`, `description`, `price_model` (free/one_time/subscription/usage), `price_amount`, `install_count`, `rating_avg`, `tags`, `is_featured`

**`MarketplaceInstallation`** — A tenant's installation of a listing  
Key fields: `listing`, `installed_by_id`, `installed_version`, `is_active`, `installed_at`, `config`

### API Methods

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `getListings(params?)` | GET `/commercial-readiness/marketplace-listings/` | Public | Browse all published listings |
| `getListing(id)` | GET `.../marketplace-listings/{id}/` | Public | Get listing detail |
| `installListing(id)` | POST `.../marketplace-listings/{id}/install/` | Tenant | Install a listing to tenant |
| `getInstallations(params?)` | GET `/commercial-readiness/marketplace-installations/` | Tenant | List tenant's installations |

### Categories

| Value | Display Name | Description |
|-------|-------------|-------------|
| `module` | Clinical Modules | Full product modules (e.g., Cardiology Module) |
| `extension` | Extensions | Feature extensions to existing products |
| `ai_package` | AI Packages | Pre-built AI models and analytics packs |
| `connector` | Connectors | Integration connectors (MOH, NABIDH, lab systems) |
| `clinical_template` | Clinical Templates | FHIR-based clinical template libraries |
| `report` | Reports | Pre-built BI and operational reports |
| `dashboard` | Dashboards | Operational and clinical dashboards |
| `theme` | Themes | UI themes and white-label templates |

### Publisher Types

- **Official** — Published by CyberCom. Included in platform subscription where applicable.
- **Verified Partner** — Published by a Gold/Platinum partner. Certified by CyberCom technical review.
- **Community** — Published by community developers. Use at your own discretion.

## Page: `/marketplace`

Public-facing marketplace browser with:
- Category filter bar (8 categories with icons)
- Featured listings grid (3-column, glass cards with publisher badges, ratings, install counts)
- Publisher CTA section for partners wanting to publish extensions
- Platform access CTA linking to `/demo`

### Usage Example

```typescript
import { marketplaceApi } from "@cybercom/api";

// Browse official listings by category
const aiPackages = await marketplaceApi.getListings({ 
  category: "ai_package",
  publisher_type: "official"
});

// Install a listing for the current tenant
const result = await marketplaceApi.installListing(listingId);
// result: { status: "installed", installation_id: "..." }
```
