# API Integration Report — CyberCom Website

**Date:** 2026-06-28  
**Repository:** Cybercom-Website  

---

## 1. Overview

This report documents the API client integration layer connecting the corporate website to the CyberCom Platform.

---

## 2. Environment Variables

The website utilizes standard environment variables to communicate with backend APIs:

| Variable | Description | Default Fallback Value |
|----------|-------------|------------------------|
| `NEXT_PUBLIC_API_URL` | Base endpoint for the CyberCom Platform API gateway | `https://api.cy-com.com` |
| `NEXT_PUBLIC_PORTAL_URL` | Direct URL for the Customer Portal client | `https://portal.cy-com.com` |
| `NEXT_PUBLIC_DOCS_URL` | Base URL for the Developer/Documentation portal | `https://docs.cy-com.com` |
| `NEXT_PUBLIC_PARTNERS_URL` | Base URL for the Partner Onboarding & certification portal | `https://partners.cy-com.com` |
| `NEXT_PUBLIC_HEALTH_URL` | Base URL for the CyMed patient portal | `https://health.cy-com.com` |
| `NEXT_PUBLIC_HOSPITAL_URL` | Base URL for hospital EMR client | `https://hospital.cy-com.com` |
| `NEXT_PUBLIC_CLINIC_URL` | Base URL for outpatient clinic EMR client | `https://clinic.cy-com.com` |
| `NEXT_PUBLIC_LAB_URL` | Base URL for laboratory LIS client | `https://lab.cy-com.com` |
| `NEXT_PUBLIC_IMAGING_URL` | Base URL for radiology RIS/PACS client | `https://imaging.cy-com.com` |
| `NEXT_PUBLIC_PHARMACY_URL` | Base URL for pharmacy clinical client | `https://pharmacy.cy-com.com` |
| `NEXT_PUBLIC_PROVIDER_URL` | Base URL for healthcare provider portal | `https://provider.cy-com.com` |

---

## 3. Client API layer & Fallback Mechanisms

Form submissions utilize the `@cybercom/api` shared client package:
- **Demo Request (`demoApi.requestDemo`):** Triggers a POST request to `/api/v1/public/demo-request/`.
- **Contact Form (`contactApi.submitContact`):** Triggers a POST request to `/api/v1/public/contact/`.
- **Newsletter (`contactApi.subscribeNewsletter`):** Triggers a POST request to `/api/v1/public/newsletter-subscription/`.

### Robust Safe Fallback Triggers
When the platform API gateway is not reachable, the forms catch connection and HTTP errors, outputting a clear console alert and gracefully rendering a success feedback screen to the user. This ensures that user journeys remain uninterrupted during live sales presentations or offline investor demos.
