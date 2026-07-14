# CyCom ERP — Implementation Roadmap
# Copyright (C) CyberCom. All rights reserved.
# Generated: 2026-07-14

## Phase 0 — COMPLETE: Audit & Architecture (Current Phase)
- [x] Inspect CyCom ERP source code
- [x] Analyze functional reference archives (api_routes.csv, odoo_core_modules.csv, custom_modules.csv, Full Codebase Study DOCX)
- [x] Produce CYCOM_CURRENT_STATE.md
- [x] Produce FEATURE_PARITY_MATRIX.md (202 features catalogued)
- [x] Produce SECURITY_GAP_ANALYSIS.md (8 critical gaps)
- [x] Produce SOFTWARE_BILL_OF_MATERIALS.md
- [ ] Produce DATA_MODEL_GAP_ANALYSIS.md
- [ ] Produce API_GAP_ANALYSIS.md
- [ ] Produce MODULE_DEPENDENCY_MAP.md

## Phase 1 — Platform Foundation (NEXT)
Duration: 2-3 weeks

### 1.1 Security Hardening (Critical, do first)
- [ ] Move JWT_SECRET_KEY to environment variable
- [ ] Add authentication middleware to all protected routes
- [ ] Fix file upload path traversal (use UUID filenames)
- [ ] Fix CORS configuration
- [ ] Add rate limiting to auth endpoints
- [ ] Add bootstrap endpoint authentication

### 1.2 Missing Backend Models (Critical)
Priority order based on frontend usage:
- [ ] product.product (Inventory catalog - most-needed)
- [ ] purchase.order + purchase.order.line (Procurement)
- [ ] res.partner / cy_vendor (Vendor management)
- [ ] stock.picking + stock.move (Warehouse transfers)
- [ ] stock.quant (Stock levels)
- [ ] hr.expense (Expense claims)
- [ ] hr.applicant (Recruitment)
- [ ] helpdesk.ticket (Support tickets)
- [ ] fleet.vehicle (Fleet management)
- [ ] maintenance.request (Maintenance)
- [ ] mass.mailing (Marketing campaigns)
- [ ] mrp.production (Manufacturing orders)
- [ ] planning.slot (Work schedule)
- [ ] quality.check (QC inspections)
- [ ] subscription.contract (Subscriptions)
- [ ] knowledge.article (Knowledge base)

### 1.3 Bulk Import Engine
- [ ] POST /api/v1/imports/employees — parse Excel, validate, bulk-insert
- [ ] POST /api/v1/imports/products — inventory bulk import
- [ ] POST /api/v1/imports/journal-entries — accounting opening balances
- [ ] GET /api/v1/imports/template/{entity} — download Excel template
- [ ] Frontend: /hr/employees/import page with column mapper
- [ ] Frontend: /inventory/import page
- [ ] Frontend: /accounting/import page

### 1.4 Company & Branch Setup
- [ ] Fix Company model parent_id (add to DB schema)
- [ ] Fix bootstrap UNIQUE constraint
- [ ] Complete setup wizard (Chart of Accounts, Warehouse, HR Departments)
- [ ] Add layout.tsx data-scroll-behavior="smooth" fix
- [ ] Fix React duplicate key warnings in setup steps

## Phase 2 — Vendor Management & Procurement (Critical Workflow 1)
Duration: 2 weeks

### 2.1 Vendor Onboarding
- [ ] cy_vendor model: legal_name, cr_number, tax_number, iban, approval_status
- [ ] cy_vendor_document model: vendor_id, doc_type, filename, storage_path
- [ ] File upload endpoint for vendor documents
- [ ] Vendor approval state machine: draft → submitted → review → approved/rejected
- [ ] Frontend: /purchase/vendors (directory + approval status)
- [ ] Frontend: /purchase/vendors/new (create + upload documents)
- [ ] Frontend: /purchase/vendors/[id]/approve (manager review)
- [ ] Frontend: /purchase/vendors/[id] (full profile)

### 2.2 Purchase Order Full Lifecycle
- [ ] cy_purchase_order model
- [ ] cy_purchase_order_line model
- [ ] PO approval workflow (amount threshold)
- [ ] Goods receipt (full + partial)
- [ ] Pending quantities model
- [ ] Vendor invoice upload + manual entry
- [ ] 3-way matching (PO ↔ GRN ↔ Invoice)
- [ ] Frontend: /purchase/create (multi-line PO form)
- [ ] Frontend: /purchase/receive (GRN form)
- [ ] Frontend: /purchase/invoices (invoice management)

## Phase 3 — Branch Internal Orders (Critical Workflow 2)
Duration: 1.5 weeks

### 3.1 Branch Ordering
- [ ] cy_internal_order model
- [ ] cy_internal_order_line model (requested_qty, approved_qty, shipped_qty, pending_qty)
- [ ] Order states: draft → submitted → warehouse_review → partially_allocated → dispatched → received
- [ ] Frontend: /inventory/branch-orders (branch creates order)
- [ ] Frontend: /inventory/warehouse-requests (warehouse reviews + fulfills)
- [ ] Frontend: /inventory/pending-lines (visibility into unresolved demand)

### 3.2 Stock Management
- [ ] cy_product model (with category, UOM, barcode, reorder rules)
- [ ] cy_stock_location model
- [ ] cy_stock_quant (current stock per location)
- [ ] Real-time stock check on order allocation
- [ ] Backorder/pending when insufficient stock

## Phase 4 — Employee Bulk Import (Critical Workflow 3)
Duration: 1 week

### 4.1 Import Engine
- [ ] Excel parser (openpyxl)
- [ ] Field mapping UI component
- [ ] Validation engine with row-level error reporting
- [ ] Dry-run mode
- [ ] Partial acceptance (skip invalid rows)
- [ ] Import progress tracking
- [ ] Error report download

### 4.2 Employee Import Template
Fields: employee_number, national_id, full_name, arabic_name, gender, dob, nationality,
email, mobile, department, job_position, manager, contract_type, contract_start,
salary, bank_iban, working_schedule, branch

## Phase 5 — HR & Payroll Enhancements
Duration: 2 weeks

### 5.1 Extended Employee Profile
- [ ] name_arabic, blood_type, religion (optional), mother_name
- [ ] medical_insurance_ref, insurance_tier
- [ ] spouse_employed checkbox
- [ ] Education history (multi-line)
- [ ] Previous employment history
- [ ] Warning/discipline records
- [ ] Career movement timeline
- [ ] Employee number (emp_code) field

### 5.2 Attendance & Payroll
- [ ] Real web check-in/check-out endpoint
- [ ] ZK device sync API (polling service)
- [ ] Geofence validation on mobile check-in
- [ ] Lateness auto-deduction calculation
- [ ] Overtime approval workflow (employee → manager)
- [ ] Payslip XLSX export
- [ ] Batch payslip run
- [ ] Social security calculation (Jordan: 7.5%/14.25%)
- [ ] Health insurance management

## Phase 6 — POS Enhancements
Duration: 1 week

- [ ] Cash rounding (nearest 0.5 JOD)
- [ ] Predefined discount buttons
- [ ] Advance orders (layaway)
- [ ] Session user restriction per branch
- [ ] POS analytics (cost center)
- [ ] Custom receipt templates

## Phase 7 — Finance & Accounting Completion
Duration: 2 weeks

- [ ] Chart of accounts (full account model)
- [ ] Customer invoices (full lifecycle)
- [ ] Vendor bills (full lifecycle)
- [ ] Customer/vendor payments
- [ ] Bank statement import + reconciliation
- [ ] Tax calculation (VAT 16% JO)
- [ ] Financial statements (P&L, Balance Sheet, Cash Flow)
- [ ] Analytic accounts (cost centers)
- [ ] Check printing (Arabic Tafqeet)
- [ ] Budget management

## Phase 8 — Portals & Mobile
Duration: 2 weeks

- [ ] Employee ESS portal (real data: payslips, leaves, attendance, OT)
- [ ] Employee PWA (service worker, offline support)
- [ ] Mobile API (16 endpoints: auth, profile, attendance, leaves, OT)
- [ ] Overtime portal (submit + track)
- [ ] Customer portal (order/invoice tracking)
- [ ] Vendor portal (quote submission, invoice upload)

## Phase 9 — Analytics & Reporting
Duration: 1 week

- [ ] Executive dashboard (real KPIs)
- [ ] Procurement dashboard
- [ ] Warehouse dashboard
- [ ] HR dashboard
- [ ] POS Z/X reports
- [ ] Internal transfer XLSX report
- [ ] Field-level change tracking (audit)
- [ ] User activity report

## Phase 10 — Security Hardening & Production
Duration: 1 week

- [ ] Migrate to PostgreSQL
- [ ] Implement full RBAC
- [ ] Add branch/company isolation to all queries
- [ ] Add rate limiting
- [ ] Add audit log (immutable)
- [ ] Security scanning
- [ ] Load testing
- [ ] Documentation

## Estimated Total: 16-18 weeks for full production-grade platform

## Three Mandatory Workflows to Implement First

### Workflow 1: Supplier Onboarding → PO → Invoice → Payment
1. Vendor submits registration with documents
2. Manager approves vendor
3. Branch creates purchase request (multi-item)
4. Procurement creates RFQ + PO
5. Warehouse partially receives goods
6. Pending quantities tracked
7. Supplier uploads invoice
8. 3-way matching performed
9. Invoice approved + posted
10. Payment approved + issued

### Workflow 2: Branch Internal Order → Warehouse → Pending
1. Branch creates multi-item internal order
2. Warehouse reviews full order
3. Warehouse ships available quantities
4. Missing quantities remain pending with reason
5. System recommends procurement or transfer
6. Goods dispatched
7. Branch confirms receipt with actual quantities
8. Discrepancies flagged for investigation

### Workflow 3: Bulk Employee Import
1. Download employee Excel template
2. Fill 300 employee records
3. Upload Excel to /hr/employees/import
4. Map columns (with smart defaults)
5. Validate data (show errors per row)
6. Preview valid/invalid rows
7. Correct invalid rows inline
8. Import valid rows
9. Create employee portal accounts
10. Assign branches, departments, contracts, schedules
11. Download import + audit report
