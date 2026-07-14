# Demo Integration Report
**CyberCom Revolution — Live Demo Connectivity**
**Date:** 2026-06-29
**Classification:** Internal — Engineering & Product

---

## Overview

All product pages on the CyberCom website connect to live demo environments via environment variables with hardcoded fallback URLs. This report documents every demo link, its environment variable, and its current status.

---

## Demo Link Architecture

```
Website → NEXT_PUBLIC_*_URL (env var)
        → Fallback URL (hardcoded)
        → Live demo environment (hosted separately)
```

All demo links:
- Open in new tab (`target="_blank"` + `rel="noreferrer"`)
- Are labeled with `ExternalLink` icon for user clarity
- Have ARIA labels for accessibility
- Are configurable per deployment environment via `.env.local`

---

## CyMed Demo Links

| Product | Environment Variable | Fallback URL | Status |
|---------|---------------------|-------------|--------|
| CyMed Platform | `NEXT_PUBLIC_CYMED_URL` | `health.cy-com.com` | ✅ Configured |
| CyMed Hospital | `NEXT_PUBLIC_CYMED_HOSPITAL_URL` | `hospital.cy-com.com` | ✅ Configured |
| CyMed Clinic | `NEXT_PUBLIC_CYMED_CLINIC_URL` | `clinic.cy-com.com` | ✅ Configured |
| CyMed Pharmacy | `NEXT_PUBLIC_CYMED_PHARMACY_URL` | `pharmacy.cy-com.com` | ✅ Configured |
| CyMed Laboratory | `NEXT_PUBLIC_CYMED_LAB_URL` | `lab.cy-com.com` | ✅ Configured |
| CyMed Imaging | `NEXT_PUBLIC_CYMED_IMAGING_URL` | `imaging.cy-com.com` | ✅ Configured |
| Patient Portal | `NEXT_PUBLIC_CYMED_PATIENT_PORTAL_URL` | `health.cy-com.com` | ✅ Configured |
| Provider Portal | `NEXT_PUBLIC_CYMED_PROVIDER_PORTAL_URL` | `provider.cy-com.com` | ✅ Configured |
| Revenue Cycle | `NEXT_PUBLIC_CYMED_RCM_URL` | `portal.cy-com.com/rcm` | ✅ Configured |
| Population Health | `NEXT_PUBLIC_CYMED_POPULATION_HEALTH_URL` | `health.cy-com.com/population` | ✅ Configured |

---

## CyShop Demo Link

| Product | Environment Variable | Fallback URL | Status |
|---------|---------------------|-------------|--------|
| CyShop | `NEXT_PUBLIC_CYSHOP_URL` | `cyshop.cy-com.com` | ✅ Configured |

---

## CyCom ERP Demo Links

| Module | Environment Variable | Fallback URL | Status |
|--------|---------------------|-------------|--------|
| CyCom ERP | `NEXT_PUBLIC_CYCOM_URL` | `portal.cy-com.com/erp` | ✅ Configured |
| Finance | `NEXT_PUBLIC_CYCOM_FINANCE_URL` | `portal.cy-com.com/erp/finance` | ✅ Configured |
| Accounting | `NEXT_PUBLIC_CYCOM_ACCOUNTING_URL` | `portal.cy-com.com/erp/accounting` | ✅ Configured |
| Procurement | `NEXT_PUBLIC_CYCOM_PROCUREMENT_URL` | `portal.cy-com.com/erp/procurement` | ✅ Configured |
| Inventory | `NEXT_PUBLIC_CYCOM_INVENTORY_URL` | `portal.cy-com.com/erp/inventory` | ✅ Configured |
| HR | `NEXT_PUBLIC_CYCOM_HR_URL` | `portal.cy-com.com/erp/hr` | ✅ Configured |
| Payroll | `NEXT_PUBLIC_CYCOM_PAYROLL_URL` | `portal.cy-com.com/erp/payroll` | ✅ Configured |
| CRM | `NEXT_PUBLIC_CYCOM_CRM_URL` | `portal.cy-com.com/erp/crm` | ✅ Configured |
| Assets | `NEXT_PUBLIC_CYCOM_ASSETS_URL` | `portal.cy-com.com/erp/assets` | ✅ Configured |
| Manufacturing | `NEXT_PUBLIC_CYCOM_MANUFACTURING_URL` | `portal.cy-com.com/erp/manufacturing` | ✅ Configured |
| Retail/POS | `NEXT_PUBLIC_CYCOM_RETAIL_URL` | `portal.cy-com.com/erp/retail` | ✅ Configured |
| BI | `NEXT_PUBLIC_CYCOM_BI_URL` | `portal.cy-com.com/erp/bi` | ✅ Configured |

---

## Platform Demo Links

| Platform | Environment Variable | Fallback URL | Status |
|---------|---------------------|-------------|--------|
| CyGov | `NEXT_PUBLIC_CYGOV_URL` | `portal.cy-com.com/gov` | ✅ Configured |
| CyIdentity | `NEXT_PUBLIC_CYIDENTITY_URL` | `portal.cy-com.com/identity` | ✅ Configured |
| CyIntegrationHub | `NEXT_PUBLIC_CYINTEGRATIONHUB_URL` | `portal.cy-com.com/integration` | ✅ Configured |
| CyAI | `NEXT_PUBLIC_CYAI_URL` | `portal.cy-com.com/ai` | ✅ Configured |
| CyData | `NEXT_PUBLIC_CYDATA_URL` | `portal.cy-com.com/data` | ✅ Configured |
| CyConnect | `NEXT_PUBLIC_CYCONNECT_URL` | `portal.cy-com.com/connect` | ✅ Configured |
| CyCitizen | `NEXT_PUBLIC_CYCITIZEN_URL` | `portal.cy-com.com` | ✅ Configured |

---

## Additional Env Vars

| Variable | Purpose |
|---------|---------|
| `NEXT_PUBLIC_PORTAL_URL` | Base for portal.cy-com.com links |
| `NEXT_PUBLIC_HEALTH_URL` | Base for health.cy-com.com links |
| `NEXT_PUBLIC_DOCS_URL` | Documentation site URL |

---

## Demo Link Implementation

All demo links in `[slug]/page.tsx` use the pattern:
```typescript
const LAUNCH_URLS: Record<string, string> = {
  "cymed-hospital": process.env.NEXT_PUBLIC_CYMED_HOSPITAL_URL
    ?? process.env.NEXT_PUBLIC_HOSPITAL_URL
    ?? "https://hospital.cy-com.com",
  // ...
};
```

This ensures:
1. Environment-specific override (staging/prod)
2. Secondary fallback var
3. Hardcoded production fallback

---

## CyberCom Platform Connection

All demo environments connect to the CyberCom Platform backend (`api.cy-com.com`) for:
- Authentication via CyIdentity (OAuth 2.1)
- Tenant provisioning
- Audit logging
- FHIR endpoint access (CyMed)
- Integration hub routing

---

## Verdict

**Demo Integration: COMPLETE**

All 30+ demo links are configured with environment variables and production fallbacks. Zero hardcoded credentials. All links open externally in new tab with proper ARIA labels.
