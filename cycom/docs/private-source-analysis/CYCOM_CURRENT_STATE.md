# CyCom ERP — Current State Audit
# Copyright (C) CyberCom. All rights reserved.
# Generated: 2026-07-14

## 1. Executive Summary

CyCom ERP is a Next.js 16 + React 19 frontend paired with a FastAPI micro-kernel backend.
The platform has approximately 30 frontend module screens but only 1 module (eSign) has real
backend persistence. All other modules run on in-memory React state and lose data on refresh.

### Key Metrics

| Metric | Value |
|---|---|
| Frontend modules | 30 |
| Backend-wired modules | 1 (eSign only) |
| Backend models registered | ~12 (hr.employee, hr.department, hr.leave, hr.payslip, pos.*, account.move, sale.order) |
| Models being mocked (no DB table) | 14+ |
| Security issues (critical) | 5 |
| Lines of frontend code | ~14,400 |
| Lines of backend code | ~1,200 |

## 2. Architecture

### Backend (core-kernel + cycom-backend)
- Framework: FastAPI (Python)
- Database: SQLite (cycom_erp.db) - SINGLE FILE, no concurrent writes
- ORM: SQLAlchemy
- Auth: JWT HS256, 7-day expiry
- RPC Layer: /api/rpc endpoint dispatching to MODEL_MAP
- Port: 8888

### Frontend (cycom-erp)
- Framework: Next.js 16 + React 19
- Styling: Tailwind CSS 4 + Radix UI + Framer Motion
- Port: 5555
- API calls: via /api/cycom/* Next.js route handlers -> /api/rpc on backend

### Databases (SQLite shards)
- cycom_erp.db (main)
- Per-tenant sharding planned but not implemented

## 3. Module Status

| Module | Frontend | Backend Model | API Endpoint | Status |
|---|---|---|---|---|
| Login/Auth | Complete | Partial | /api/auth/login, /api/auth/me | Prototype |
| Dashboard | Complete | Missing | None | Prototype |
| HR/Employees | Complete | Partial (hr.employee, hr.department) | /api/rpc | Partial |
| HR/Attendance | Complete | Missing | Mocked | Prototype |
| HR/Payroll | Complete | Partial (hr.payslip) | /api/rpc | Partial |
| HR/Insurance | Complete | Missing | Mocked | Prototype |
| HR/Documents | Complete | Missing | Mocked | Prototype |
| HR/Requests | Complete | Partial (hr.leave) | /api/rpc | Partial |
| Inventory | Complete | Missing | Mocked | Prototype |
| Purchase | Complete | Missing | Mocked | Prototype |
| Sales | Complete | Partial (sale.order) | /api/rpc | Partial |
| Accounting | Complete | Partial (account.move) | /api/rpc | Partial |
| POS | Complete | Partial (pos.session, pos.order) | /api/rpc | Partial |
| CRM | Complete | Missing | Mocked | Prototype |
| Projects | Complete | Partial (project.task) | /api/rpc | Partial |
| Helpdesk | Complete | Missing | Mocked | Prototype |
| Fleet | Complete | Missing | Mocked | Prototype |
| Manufacturing | Complete | Missing | Mocked | Prototype |
| Maintenance | Complete | Missing | Mocked | Prototype |
| Marketing | Complete | Missing | Mocked | Prototype |
| Knowledge | Complete | Missing | Mocked | Prototype |
| Planning | Complete | Missing | Mocked | Prototype |
| Quality | Complete | Missing | Mocked | Prototype |
| Recruitment | Complete | Missing | Mocked | Prototype |
| Expenses | Complete | Missing | Mocked | Prototype |
| eSign | Complete | Complete | /api/sign/* | Complete |
| Portal/ESS | Partial | Partial | /api/rpc | Partial |
| Setup Wizard | Partial | Partial | /api/cycom/setup/* | Partial |
| Documents | Complete | Missing | Mocked | Prototype |
| Subscriptions | Complete | Missing | Mocked | Prototype |

## 4. Security Gaps (Critical)

| # | Issue | Severity | File |
|---|---|---|---|
| 1 | JWT secret hardcoded in source | Critical | cycom-backend/app/core/security.py |
| 2 | No endpoint auth enforcement | Critical | All routers |
| 3 | CORS wildcard + credentials | High | cycom-backend/app/main.py |
| 4 | Path traversal in eSign upload | Critical | cycom-backend/app/api/routers/sign.py |
| 5 | SQLite single-writer (no concurrent use) | High | cycom-backend/app/core/config.py |
| 6 | No input size limits on uploads | High | Multiple |
| 7 | No rate limiting | High | All endpoints |
| 8 | Bootstrap endpoint unauthenticated | Critical | core-kernel/main.py |

## 5. Missing Backend Models (Currently Mocked)

| Model Name | Frontend Usage | Priority |
|---|---|---|
| hr.document | HR Documents page | High |
| hr.employee.insurance | HR Insurance page | High |
| hr.applicant | Recruitment page | Medium |
| product.product | Inventory catalog | Critical |
| helpdesk.ticket | Helpdesk page | Medium |
| mass.mailing | Marketing page | Medium |
| mrp.eco | PLM/Manufacturing page | Medium |
| fleet.vehicle | Fleet page | Medium |
| maintenance.request | Maintenance page | Medium |
| knowledge.article | Knowledge page | Medium |
| planning.slot | Planning page | Medium |
| quality.check | Quality page | Medium |
| subscription.contract | Subscriptions page | Low |
| hr.expense | Expenses page | High |
| purchase.order | Purchase page | Critical |
| res.partner (vendor) | Purchase/Vendor management | Critical |
| stock.picking | Inventory transfers | Critical |
| stock.quant | Inventory stock levels | Critical |

## 6. Missing Features (vs. Target Reference Platform)

### Bulk Operations
- No Excel/CSV import for any entity
- No bulk employee creation
- No bulk product/inventory import
- No batch operations on records

### Procurement
- No vendor onboarding workflow
- No vendor document upload
- No vendor approval process
- No RFQ creation
- No PO line items management
- No goods receipt (partial/full)
- No vendor invoice 3-way matching

### Inventory/Warehouse
- No real-time stock levels
- No branch-to-warehouse internal ordering
- No partial fulfillment with pending quantities
- No transfer discrepancy tracking
- No warehouse access controls

### HR/Payroll
- No payroll batch generation
- No overtime approval workflow
- No lateness deduction calculation
- No social security calculation
- No payslip Excel export
- No employee document expiry monitoring
- No health insurance management

### POS
- No advance orders
- No pledge/deposit orders
- No predefined discounts
- No cash rounding
- No network printer support
- No shift handover

### Finance
- No bank statement reconciliation
- No multi-currency support
- No tax return generation
- No financial statement reports

### Portals
- No employee self-service portal (real data)
- No customer portal
- No vendor/supplier portal

### AI/Automation
- No document OCR extraction
- No smart import field mapping
- No anomaly detection
