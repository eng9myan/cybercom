# Customer Portal Guide — CyberCom Website Integration
**Date:** 2026-06-29

## Overview

The CyberCom Customer Portal (`portal.cy-com.com`) is the self-service hub for all CyberCom customers. The `/portal` page on the marketing website serves as the landing and sign-in gateway.

## API Module: `packages/api/src/portal.ts`

### Types

**`CustomerPortalAccess`** — A user's portal access record  
Fields: `user_id`, `access_level` (viewer/standard/admin), `can_manage_licenses`, `can_manage_billing`, `can_open_tickets`, `can_download_software`, `is_active`, `last_login_at`

**`SupportTicket`** — A customer support ticket  
Fields: `ticket_number`, `subject`, `description`, `product_code`, `priority` (low/medium/high/critical), `status` (open/in_progress/waiting_customer/resolved/closed), `sla_due_at`, `resolution_notes`, `attachments`

**`WhiteLabelConfig`** — Tenant white-label branding configuration  
Fields: `tenant_name`, `display_name`, `primary_color`, `logo_url`, `favicon_url`, `custom_domain`, `email_from_name`, `support_email`

**`CommercialMetricsSnapshot`** — Commercial KPI snapshot for a tenant  
Fields: `snapshot_date`, `metric_type`, `product_code`, `value`, `breakdown`

### API Methods

| Method | Auth | Description |
|--------|------|-------------|
| `getCustomerAccess(params?)` | Tenant | List portal access records for tenant |
| `getSupportTickets(params?)` | Tenant | List support tickets |
| `getSupportTicket(id)` | Tenant | Get ticket detail |
| `createSupportTicket(body)` | Tenant | Submit new support ticket |
| `assignSupportTicket(id, assignedToId)` | Admin | Assign ticket to engineer |
| `resolveSupportTicket(id, notes)` | Admin | Resolve with notes |
| `closeSupportTicket(id)` | Admin | Close ticket |
| `getWhiteLabelConfigs(params?)` | Tenant | Get white-label configuration |
| `getMetricsSnapshots(params?)` | Tenant | Get commercial metrics |

## Support SLA Matrix

| Priority | First Response | Resolution Target | Trigger |
|----------|---------------|-------------------|---------|
| Critical | 1 hour | 4 hours | System down, data loss risk |
| High | 4 hours | 1 business day | Major feature unavailable |
| Medium | 1 business day | 3 business days | Feature degraded |
| Low | 2 business days | 5 business days | Minor issue, enhancement |

## Page: `/portal`

The `/portal` marketing page includes:
- Hero with portal sign-in CTA (`NEXT_PUBLIC_PORTAL_URL` env var, defaults to `https://portal.cy-com.com`)
- 6 capability cards: Licenses, Billing, Support, Downloads, Analytics, White Label
- 3 access level cards: Viewer, Standard (recommended), Admin
- SLA table for all 4 priority levels
- Security section: MFA, SSO, audit trail, tenant isolation, SOC 2, GDPR/PDPL
