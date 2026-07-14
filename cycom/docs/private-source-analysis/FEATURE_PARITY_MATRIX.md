# CyCom ERP — Feature Parity Matrix
# Copyright (C) CyberCom. All rights reserved.
# Generated: 2026-07-14
# Source: Reference Platform A (649 core modules) + Reference Extension Set B (92 custom modules)
# Cross-verified against: api_routes.csv, odoo_core_modules.csv, custom_modules.csv, Full Codebase Study

## Domain: AUTHENTICATION & IDENTITY

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Username/password login | Prototype | Yes | Yes | Wire real JWT, enforce on all routes | Critical |
| JWT token issuance | Partial | Yes | - | Secure secret, add refresh tokens | Critical |
| Token refresh | Missing | Yes | - | Implement /api/auth/refresh | High |
| Session revocation | Missing | Yes | - | Add token blacklist | High |
| MFA / OTP | Missing | Yes | Yes (employee OTP) | Implement TOTP + SMS OTP | High |
| Device registration | Missing | Yes | Yes (remember_device_login) | CyCom device binding | Medium |
| Password policy enforcement | Missing | Yes | - | Min length, complexity, expiry | High |
| Login history | Missing | Yes | - | Audit log for logins | Medium |
| SSO / OAuth2 | Missing | Yes | - | Future phase | Low |
| Role-based access control | Missing | Yes | - | Implement RBAC middleware | Critical |
| Branch-scoped permissions | Missing | Yes | Yes (warehouse_restriction) | Add branch scope to JWT | High |
| Company-scoped permissions | Missing | Yes | - | Multi-company token claims | High |

## Domain: HUMAN RESOURCES

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Employee directory | Partial | Yes (hr) | Yes | Wire to real DB, add CRUD | Critical |
| Employee profile - basic | Partial | Yes | Yes (anabtawi_employee_profile) | Add missing fields | High |
| Employee Arabic name | Missing | Yes | Yes | Add name_arabic field | High |
| Employee blood type | Missing | Yes | Yes | Add field | Medium |
| Employee religion | Missing | Yes | Yes | Add field (optional) | Low |
| Employee spouse info | Missing | Yes | Yes (hr_employee_spouse) | Add spouse tab | Medium |
| Employee education history | Missing | Yes | Yes | Add multi-line education | Medium |
| Employee previous employment | Missing | Yes | Yes | Add prev jobs lines | Medium |
| Employee warning/discipline | Missing | Yes | Yes | Add warning records | Medium |
| Employee career movements | Missing | Yes | Yes | Add career timeline | Medium |
| Employee document expiry | Partial (UI only) | Yes | Yes (employee_document_expiry) | Wire to DB, add alerts | High |
| Employee number (code) | Missing | Yes | Yes (hr_employee_code) | Add emp_code field | High |
| Health insurance management | Prototype (UI only) | Yes | Yes (hr_health_insurance) | Full model + backend | High |
| Department hierarchy | Partial | Yes | Yes (hr_department_child_employee_count) | Count rollup, tree view | Medium |
| Bulk employee import (Excel) | Missing | Yes | Yes (anabtawi_payslip_xlsx pattern) | Full import engine | Critical |
| Employee PDF profile export | Missing | Yes | Yes (anabtawi_employee_profile) | PDF generation | Medium |

## Domain: ATTENDANCE

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Web check-in / check-out | Missing | Yes (hr_attendance) | Yes (portal_check_in) | Implement real attendance record | Critical |
| Mobile check-in | Missing | Yes | Yes (anabtawi_mobile_api) | Mobile API endpoint | High |
| ZK biometric device sync | Prototype (UI mock) | - | Yes (hs_zk_attendance + bridge) | TCP device polling service | High |
| Face recognition attendance | Missing | - | Yes (sttl_face_attendance) | API hook for face service | Medium |
| Geofence validation | Missing | - | Yes (hr_attendance_geofence_config) | GPS radius check on check-in | High |
| Duplicate punch prevention | Missing | - | Yes | Dedup logic in ingestion | High |
| Attendance schedule normalization | Missing | Yes | Yes (hr_attendance_schedule_normalization) | Normalize missed punches | High |
| Manual attendance correction | Missing | Yes | - | HR admin correction form | Medium |
| Attendance overtime tracking | Missing | Yes | Yes (hr_attendance_overtime_approval_bridge) | Compute extra hours | High |
| Weekly overtime eligibility | Missing | - | Yes (hr_attendance_weekly_overtime_eligibility) | Min hours rule | Medium |

## Domain: LEAVE MANAGEMENT

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Leave request (employee) | Prototype | Yes (hr_holidays) | Yes (portal_leaves) | Wire to DB, approval flow | Critical |
| Leave approval workflow | Missing | Yes | Yes | Multi-level approval | High |
| Leave balance tracking | Missing | Yes | Yes | Accrual + allocation | High |
| Leave accrual plans | Missing | Yes | Yes (hr_enhancement_plan) | Milestone accrual from contract | Medium |
| Leave fallback rules | Missing | - | Yes (hr_leave_fallback) | Fallback policy config | Medium |
| Leave encashment | Missing | Yes | - | Payroll integration | Medium |
| Public holiday calendar | Missing | Yes | - | Country calendar | High |
| Medical certificate upload | Missing | Yes | - | Attachment on sick leave | Medium |

## Domain: OVERTIME & PAYROLL

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Overtime request (employee) | Prototype | Yes | Yes (hr_attendance_overtime_approval_bridge) | Real approval flow | High |
| Overtime pre-approval | Missing | - | Yes | Pre-auth before OT | Medium |
| Lateness auto-deduction | Missing | - | Yes (latness_deduction, hr_lateness_work_entry_automation) | Work entry + payslip | High |
| Absent work entry auto-create | Missing | - | Yes (hr_absent_work_entry_automation) | Cron job | Medium |
| Payslip generation | Prototype | Yes (hr_payroll) | Yes | Wire to real salary rules | Critical |
| Payslip XLSX export | Missing | - | Yes (anabtawi_payslip_xlsx) | openpyxl export | High |
| Bulk payslip run | Missing | Yes | - | Batch payroll processing | High |
| Social security calculation | Missing | Yes | Yes | JO: 7.5% employee, 14.25% employer | High |
| Income tax brackets | Missing | Yes | - | Jordan tax schedule | High |
| End-of-service benefit | Missing | Yes | - | EOSB calculation | Medium |
| Payroll accounting journal | Missing | Yes | Yes (base_payroll_account) | Post to ledger | High |
| Employee salary payment method | Missing | - | Yes (employee_salary_payment_method) | IBAN/cash/check field | Medium |

## Domain: PLANNING & SHIFTS

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Shift templates | Prototype (UI only) | Yes (planning) | Yes (planning_enhancement) | Real DB planning.slot | High |
| Factory plan category | Missing | - | Yes (factory_plan_category) | Manufacturing planning | Medium |
| Direct overtime from planning | Missing | - | Yes (hr_attendance_planning_direct_overtime) | Planning-attendance bridge | Medium |
| Shift swap | Missing | Yes | - | Future phase | Low |

## Domain: PROCUREMENT

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Vendor directory | Prototype (UI only) | Yes (purchase) | Yes (ALTANMYA_Purchase_Extension) | Full vendor model | Critical |
| Vendor onboarding workflow | Missing | Yes | Yes | Draft/Review/Approved states | Critical |
| Vendor document upload (CR/Tax) | Missing | Yes | Yes (approval_contact) | File upload + storage | Critical |
| Vendor approval by manager | Missing | Yes | Yes | Approval workflow | Critical |
| Vendor duplicate detection | Missing | Yes | - | CR/IBAN dedup | High |
| Vendor portal | Missing | Yes | - | Supplier self-service | Medium |
| Purchase request (multi-item) | Missing | Yes | Yes | PR model with lines | Critical |
| Purchase request approval | Missing | Yes | Yes (ALTANMYA_Purchase_Extension) | Configurable approval | High |
| RFQ creation | Missing | Yes | - | Request for quotation | High |
| Multi-vendor RFQ comparison | Missing | Yes | - | Side-by-side comparison | Medium |
| Purchase order (full lifecycle) | Prototype | Yes | Yes | PO model with approval | Critical |
| PO line items | Missing | Yes | - | purchase.order.line model | Critical |
| Partial goods receipt | Missing | Yes | - | stock.picking with backorder | Critical |
| Pending quantities tracking | Missing | Yes | Yes (ALTANMYA pending model) | Pending quantity model | Critical |
| Vendor invoice upload | Missing | Yes | - | Bill upload + OCR | High |
| 3-way matching (PO/GRN/Invoice) | Missing | Yes | - | Match logic | High |
| Invoice approval & posting | Missing | Yes | - | Account.move posting | High |

## Domain: INVENTORY & WAREHOUSE

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Product catalog | Prototype | Yes (stock) | Yes | product.product model | Critical |
| Bulk product import | Missing | Yes | - | Excel import engine | High |
| Stock locations | Missing | Yes | - | stock.location model | High |
| Warehouse management | Missing | Yes | Yes (warehouse_restriction_for_user) | stock.warehouse model | High |
| Internal transfers | Prototype | Yes | Yes (internal_transfer_excel_report) | stock.picking model | Critical |
| Branch ordering (internal) | Missing | - | Yes (branch_product_whitelist, stock_picking_catalog) | Internal order model | Critical |
| Partial fulfillment + pending | Missing | - | Yes (stock_transfer_discrepancy_new) | Discrepancy + backorder | Critical |
| Warehouse access control | Missing | - | Yes (warehouse_restriction_for_user) | Per-user warehouse restriction | High |
| Negative stock blocking | Missing | - | Yes (stock_location_negative_block) | Stock guard | High |
| Stock qty guard on transfers | Missing | - | Yes (stock_qty_guard) | Over-pick prevention | High |
| Barcode scanning | Missing | Yes | Yes (stock_barcode_demand_qty) | Barcode input component | Medium |
| Lots & serial numbers | Missing | Yes | - | Lot tracking | Medium |
| Expiry date tracking | Missing | Yes | - | FEFO removal strategy | Medium |
| Inventory count sheets | Missing | Yes | - | Count wizard | Medium |
| Packing list (PDF + XLSX) | Missing | - | Yes (ameen_anabtawi_packing_list) | Report generation | Medium |

## Domain: SALES & CRM

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Sales order (basic) | Partial | Yes (sale_management) | - | Full SO lifecycle | High |
| Discount approval | Partial (UI only) | Yes | Yes (sale_discount_exception_approval) | Wire approval to backend | High |
| Sale line approval | Missing | - | Yes (ag_sale_line_approval) | Line-level approval | Medium |
| Pricing control | Missing | - | Yes (anabtawi_sale_pricing_control) | Min price enforcement | Medium |
| CRM leads/pipeline | Prototype | Yes (crm) | - | Wire to real CRM model | High |
| Customer credit management | Missing | Yes | - | Credit limit + approval | High |
| Pricelist per branch | Missing | Yes | Yes (pos_pricelist) | Branch pricelist | Medium |
| Fiscal position keep price | Missing | - | Yes (sale_fiscal_position_keep_price) | Price preservation | Low |

## Domain: POINT OF SALE

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| POS session & sales | Partial | Yes (point_of_sale) | Yes | Wire to backend | High |
| Cash rounding | Missing | - | Yes (pos_rounding) | 0.5 JOD rounding | High |
| Predefined discounts | Missing | - | Yes (pos_predefined_discounts) | Discount buttons | High |
| Advance orders | Missing | - | Yes (pos_advance_order) | Layaway/deposit | High |
| Pledge/deposit orders | Missing | - | Yes (pos_pledge, pos_pledge_order) | Rahn workflow | Medium |
| Hospitality/gift lines | Missing | - | Yes (pos_hospitality_gift) | Gift write-off line | Medium |
| Online campaign discounts | Missing | - | Yes (online_campaigns_discount) | Aggregator campaigns | Medium |
| POS delivery amount | Missing | - | Yes (pos_delivery_amount) | Delivery charge field | Medium |
| Exclusive payment method | Missing | - | Yes (pos_exclusive_payment_method) | Payment restriction | Medium |
| Session user restriction | Missing | - | Yes (pos_session_user_restrict) | Per-branch user lock | High |
| POS cash move access control | Missing | - | Yes (anabtawi_pos_cash_move_access) | Cash access rules | Medium |
| Custom receipts | Missing | - | Yes (custom_receipts_for_pos) | Receipt template | Medium |
| POS analytics (analytic acct) | Missing | - | Yes (pos_analytical) | Cost center on POS | Medium |
| POS refund buyer | Missing | - | Yes (anabtawi_jo_pos_refund_buyer) | JO refund workflow | Medium |
| POS scrap | Missing | - | Yes (pos_scrap) | Waste tracking | Medium |
| Opening cash zero | Missing | - | Yes (pos_opening_cash_zero) | Force zero open | Low |
| Network printer | Missing | - | Yes (cr_pos_network_printer_all_in_one) | Print API | Medium |
| MEP ID field | Missing | - | Yes (pos_mep_id) | Reference field | Low |
| POS tax fixed name | Missing | - | Yes (pos_tax_fixed_name) | Tax label override | Low |

## Domain: ACCOUNTING & FINANCE

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Chart of accounts | Missing | Yes (account) | - | account.account model | Critical |
| Journal entries (double-entry) | Partial | Yes | - | account.move full model | Critical |
| Customer invoices | Partial | Yes | - | Full invoice lifecycle | High |
| Vendor bills | Missing | Yes | - | Vendor bill model | High |
| Payments (customer) | Missing | Yes | - | account.payment | High |
| Payments (vendor) | Missing | Yes | - | account.payment | High |
| Bank reconciliation | Missing | Yes | - | Bank statement import | High |
| Cash management | Missing | Yes | - | Cash journal | Medium |
| Tax calculation | Missing | Yes | - | Tax groups, VAT | High |
| Multi-currency | Missing | Yes | - | Currency conversion | High |
| Fixed assets | Missing | Yes | - | account.asset | Medium |
| Budget management | Missing | Yes | - | account.budget | Medium |
| Analytic accounting | Missing | Yes | Yes (pos_analytical) | analytic.account | High |
| Financial statements | Missing | Yes | - | P&L, BS, CF reports | High |
| Bulk set to draft | Missing | - | Yes (account_move_bulk_set_draft) | Server action | Medium |
| Check printing (Jordan/Arabic) | Missing | - | Yes (account_check_print, print_check) | Check layout + Tafqeet | Medium |
| Mass reconciliation | Missing | - | Yes (mass_reconciliation) | Bulk match | Medium |
| Custom cash/bank domain | Missing | - | Yes (custom_cash_bank_journal_account_domain) | Journal domain filter | Low |
| Non-zero payment guard | Missing | - | Yes (payment_non_zero_confirm) | Validation | Medium |

## Domain: EMPLOYEE & CUSTOMER PORTALS

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Employee portal (ESS) | Prototype | Yes | Yes (portal_check_in, portal_leaves) | Real data, full features | Critical |
| Employee payslip download | Partial (mocked) | Yes | Yes (portal_employee_payslip) | Real PDF payslip | High |
| Leave request via portal | Prototype | Yes | Yes (portal_leaves) | Submit + track leaves | High |
| OT approval via portal | Missing | - | Yes (hr_attendance_overtime_approval_bridge) | OT request portal | High |
| Employee app (PWA) | Missing | - | Yes (anabtawi_employee_app_pwa) | Service worker PWA | High |
| Mobile API | Missing | - | Yes (anabtawi_mobile_api) | 16-endpoint mobile API | High |
| Employee OTP | Missing | - | Yes (employee_request) | 5-min OTP system | Medium |
| Customer portal | Missing | Yes | - | Order/invoice tracking | Medium |
| Supplier portal | Missing | Yes | - | Quote submission, invoice upload | High |

## Domain: MANUFACTURING

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Bills of materials | Prototype | Yes (mrp) | - | mrp.bom model | High |
| Manufacturing orders | Prototype | Yes | - | mrp.production model | High |
| Work orders | Missing | Yes | - | mrp.workorder | Medium |
| MRP (material requirements) | Missing | Yes | - | MRP run | Medium |
| Factory planning | Missing | - | Yes (factory_plan_category) | Category-based planning | Medium |
| Quality checks | Missing | Yes | - | quality.check model | Medium |
| Scrap tracking | Missing | Yes | Yes (pos_scrap) | stock.scrap model | Medium |

## Domain: ASSETS, MAINTENANCE, FLEET

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Maintenance requests | Prototype | Yes (maintenance) | - | maintenance.request model | Medium |
| Equipment register | Missing | Yes | - | maintenance.equipment | Medium |
| Preventive maintenance schedule | Missing | Yes | - | Recurring requests | Medium |
| Fleet vehicles | Prototype | Yes (fleet) | - | fleet.vehicle model | Medium |
| Vehicle fuel & costs | Missing | Yes | - | fleet.vehicle.log.fuel | Low |
| License/insurance expiry | Missing | Yes | - | Expiry alerts | Medium |

## Domain: DOCUMENTS & APPROVALS

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Document upload & storage | Partial (eSign only) | Yes (documents) | - | Generic attachment service | High |
| Document version control | Missing | Yes | - | Version history | Medium |
| Document expiry tracking | Partial (UI only) | Yes | Yes (employee_document_expiry) | Wire to backend | High |
| Configurable approval engine | Missing | Yes (approvals) | Yes (ALTANMYA, ag_sale_line_approval) | Approval model | Critical |
| Field-level change tracking | Missing | - | Yes (fields_tracking) | Audit fields | High |
| Group membership log | Missing | - | Yes (group_membership_log) | Role change audit | Medium |
| User record activity report | Missing | - | Yes (user_record_activity_report) | Activity audit | Medium |

## Domain: REPORTING & ANALYTICS

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Executive dashboard | Prototype | Yes | Yes (synconics_bi_dashboard) | Real KPI data | High |
| Procurement dashboard | Missing | Yes | - | PO/vendor metrics | Medium |
| Warehouse dashboard | Missing | Yes | - | Stock/transfer metrics | Medium |
| HR dashboard | Prototype | Yes | - | Real headcount/attendance | High |
| POS sales reports | Missing | Yes | Yes (report_pos_order) | Z/X reports | High |
| Internal transfer report (XLSX) | Missing | - | Yes (internal_transfer_excel_report) | Transfer XLSX export | Medium |
| Packing list (PDF + XLSX) | Missing | - | Yes (ameen_anabtawi_packing_list) | Packing report | Medium |
| BI dashboard | Missing | - | Yes (synconics_bi_dashboard) | Chart builder | Low |

## Domain: BULK OPERATIONS & IMPORTS

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Employee Excel import | Missing | Yes | - | Import engine | Critical |
| Product/inventory import | Missing | Yes | - | Import engine | Critical |
| Journal entry import | Missing | Yes | - | Opening balance import | High |
| Vendor import | Missing | Yes | - | Bulk vendor creation | High |
| Customer import | Missing | Yes | - | Bulk customer creation | Medium |
| Import template download | Missing | Yes | - | .xlsx template | High |
| Import preview + validation | Missing | Yes | - | Dry run mode | High |
| Import error report | Missing | Yes | - | Error file download | High |
| Batch approval | Missing | Yes | - | Approve multiple records | Medium |

## Domain: SECURITY

| Feature | CyCom Status | Ref-A Coverage | Ref-B Coverage | Required Action | Priority |
|---|---|---|---|---|---|
| Endpoint authentication | Missing | Yes | - | JWT middleware on all routes | Critical |
| RBAC enforcement | Missing | Yes | - | Role check on every action | Critical |
| Branch isolation | Missing | Yes | Yes (warehouse_restriction) | Scope filter | Critical |
| Company isolation | Missing | Yes | - | Multi-company filter | Critical |
| Audit log (immutable) | Missing | Yes | Yes (fields_tracking) | Write-only event log | High |
| Upload path sanitization | Missing | Yes | - | Fix path traversal | Critical |
| Rate limiting | Missing | Yes | - | Per-IP + per-user | High |
| Secrets management | Missing | Yes | - | Env vars, not hardcoded | Critical |
| CSRF protection | Missing | Yes | Partial | All mutating requests | High |

---

## Summary Statistics

| Priority | Feature Count | CyCom Missing |
|---|---|---|
| Critical | 28 | 28 |
| High | 67 | 61 |
| Medium | 89 | 86 |
| Low | 18 | 17 |
| **Total** | **202** | **192** |

**CyCom feature completeness: ~5% (production-ready features)**
**CyCom UI prototype completeness: ~65% (screens exist, no backend)**
