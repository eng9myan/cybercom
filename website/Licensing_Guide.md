# Licensing Guide — CyberCom Website Integration
**Date:** 2026-06-29

## API Module: `packages/api/src/licensing.ts`

### Types

**`License`** — Full license record for a tenant's product deployment  
Key fields: `license_type`, `license_scope`, `status`, `product_code`, `edition`, `license_key`, `max_users`, `max_concurrent`, `max_facilities`, `licensed_features`, `licensed_modules`, `valid_from`, `valid_until`, `grace_period_days`, `offline_token`, `auto_renew`

**`Subscription`** — Recurring billing subscription linked to a license  
Key fields: `license`, `plan`, `status`, `billing_cycle`, `amount`, `currency`, `current_period_start`, `current_period_end`, `trial_end`, `cancel_at_period_end`

### API Methods

| Method | Endpoint | Description |
|--------|----------|-------------|
| `getLicenses(params?)` | GET `/commercial-readiness/licenses/` | List all tenant licenses |
| `getLicense(id)` | GET `/commercial-readiness/licenses/{id}/` | Get single license |
| `activateLicense(id)` | POST `.../activate/` | Activate an issued license |
| `deactivateLicense(id)` | POST `.../deactivate/` | Deactivate a license |
| `renewLicense(id)` | POST `.../renew/` | Renew and extend valid_until |
| `suspendLicense(id)` | POST `.../suspend/` | Suspend license (admin action) |
| `generateOfflineToken(id)` | POST `.../generate_offline_token/` | Generate SHA-256 offline validation token |
| `getSubscriptions(params?)` | GET `/commercial-readiness/subscriptions/` | List subscriptions |
| `cancelSubscription(id)` | POST `.../cancel/` | Cancel at period end |
| `resumeSubscription(id)` | POST `.../resume/` | Resume canceled subscription |
| `checkinConcurrentSession(id)` | POST `.../checkin/` | Check in a concurrent session |
| `checkoutConcurrentSession(id)` | POST `.../checkout/` | Release a concurrent session |

### Usage Example

```typescript
import { licensingApi } from "@cybercom/api";

// List active licenses
const licenses = await licensingApi.getLicenses({ status: "active" });

// Generate offline token for air-gapped deployment
const { offline_token, valid_days } = await licensingApi.generateOfflineToken(licenseId);
```

### Portal Pages
- `/portal` — Customer portal page showing licensing capabilities
- `/pricing` — Pricing tiers with licensing model overview
