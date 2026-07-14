# CyCom ERP — API Gap Analysis
# Copyright (C) CyberCom. All rights reserved.
# Generated: 2026-07-14

## Existing CyCom API Endpoints

| Endpoint | Method | Auth | Status |
|---|---|---|---|
| /api/auth/login | POST | None | Working |
| /api/auth/me | GET | JWT | Working |
| /api/rpc | POST | JWT | Working (dispatch) |
| /api/setup/bootstrap | POST | None | Working but INSECURE |
| /api/cycom/setup/company | POST | JWT | Partial |
| /api/sign/templates | GET/POST | None | Working (unauthenticated) |
| /api/sign/requests | GET/POST | None | Working (unauthenticated) |
| /api/sign/public/[token] | GET/POST | Public | Working |

## Missing CyCom API Endpoints (by module)

### Authentication & Identity
- POST /api/v1/auth/refresh — refresh JWT token
- POST /api/v1/auth/logout — revoke session
- POST /api/v1/auth/otp/generate — generate employee OTP
- POST /api/v1/auth/otp/verify — verify OTP

### Bulk Import API
- POST /api/v1/imports/employees — upload + process employee Excel
- POST /api/v1/imports/products — upload + process product Excel
- POST /api/v1/imports/journal-entries — upload + process journal Excel
- POST /api/v1/imports/vendors — upload + process vendor Excel
- GET /api/v1/imports/template/{entity} — download Excel template
- GET /api/v1/imports/{job_id}/status — check import job status
- GET /api/v1/imports/{job_id}/errors — download error report

### Vendor Management
- GET /api/v1/vendors — list vendors (with approval filter)
- POST /api/v1/vendors — create vendor (draft)
- GET /api/v1/vendors/{id} — get vendor profile
- PUT /api/v1/vendors/{id} — update vendor
- POST /api/v1/vendors/{id}/submit — submit for review
- POST /api/v1/vendors/{id}/approve — manager approves
- POST /api/v1/vendors/{id}/reject — manager rejects
- POST /api/v1/vendors/{id}/documents — upload vendor document
- GET /api/v1/vendors/{id}/documents — list vendor documents
- GET /api/v1/vendors/{id}/documents/{doc_id} — download document

### Procurement
- GET /api/v1/purchase/requests — list purchase requests
- POST /api/v1/purchase/requests — create purchase request (multi-item)
- PUT /api/v1/purchase/requests/{id} — update PR
- POST /api/v1/purchase/requests/{id}/submit — submit for approval
- POST /api/v1/purchase/requests/{id}/approve — approve PR
- GET /api/v1/purchase/orders — list POs
- POST /api/v1/purchase/orders — create PO from PR
- GET /api/v1/purchase/orders/{id} — get PO detail
- POST /api/v1/purchase/orders/{id}/confirm — confirm PO
- POST /api/v1/purchase/orders/{id}/receive — record goods receipt
- POST /api/v1/purchase/orders/{id}/invoices — attach vendor invoice
- GET /api/v1/purchase/orders/{id}/match — get 3-way match status

### Internal Orders (Branch-to-Warehouse)
- GET /api/v1/internal-orders — list orders (filtered by branch or warehouse)
- POST /api/v1/internal-orders — create branch order (multi-item)
- GET /api/v1/internal-orders/{id} — get order detail with lines
- PUT /api/v1/internal-orders/{id} — update order (draft only)
- POST /api/v1/internal-orders/{id}/submit — submit to warehouse
- POST /api/v1/internal-orders/{id}/lines/{line_id}/allocate — warehouse allocates qty
- POST /api/v1/internal-orders/{id}/dispatch — warehouse dispatches
- POST /api/v1/internal-orders/{id}/receive — branch confirms receipt with actual qtys
- GET /api/v1/internal-orders/pending — get all pending unresolved lines

### Inventory / Products
- GET /api/v1/products — list products (with stock levels)
- POST /api/v1/products — create product
- GET /api/v1/products/{id} — product detail + stock
- GET /api/v1/stock/levels — stock by location/branch
- POST /api/v1/stock/adjust — manual stock adjustment
- GET /api/v1/stock/locations — list warehouses + locations

### HR / Employees
- GET /api/v1/employees — list employees (paginated, filtered)
- POST /api/v1/employees — create employee
- GET /api/v1/employees/{id} — full employee profile
- PUT /api/v1/employees/{id} — update profile
- POST /api/v1/employees/{id}/documents — upload HR document
- GET /api/v1/employees/{id}/payslips — list payslips
- GET /api/v1/employees/{id}/leaves — leave balance + history

### Attendance
- POST /api/v1/attendance/checkin — web/mobile check-in
- POST /api/v1/attendance/checkout — web/mobile check-out
- GET /api/v1/attendance/status/{employee_id} — current in/out status
- GET /api/v1/attendance/history — attendance log
- POST /api/v1/attendance/devices/{device_id}/sync — push ZK device events

### Leave
- GET /api/v1/leaves — list leave requests
- POST /api/v1/leaves — submit leave request
- GET /api/v1/leaves/{id} — leave request detail
- POST /api/v1/leaves/{id}/approve — approve
- POST /api/v1/leaves/{id}/refuse — refuse
- GET /api/v1/leaves/balances/{employee_id} — leave balances

### Payroll
- GET /api/v1/payslips — list payslips
- POST /api/v1/payslips/batch — generate batch payslips
- GET /api/v1/payslips/{id} — payslip detail
- GET /api/v1/payslips/{id}/download — download payslip PDF/XLSX

### POS
- GET /api/v1/pos/sessions — list sessions
- POST /api/v1/pos/sessions — open session
- POST /api/v1/pos/sessions/{id}/close — close session
- POST /api/v1/pos/orders — create POS order
- POST /api/v1/pos/orders/{id}/advance — create advance order
- GET /api/v1/pos/reports/z — Z-report for session

### Reference Platform Mobile API Routes (CyCom-native equivalents needed)
Source: api_routes.csv — anabtawi_mobile_api (16 endpoints)
CyCom must implement equivalent functionality under /api/v1/mobile/:
- POST /api/v1/mobile/auth/login
- GET /api/v1/mobile/auth/me
- POST /api/v1/mobile/auth/logout
- POST /api/v1/mobile/auth/otp
- GET /api/v1/mobile/employee/profile
- GET /api/v1/mobile/attendance/status
- POST /api/v1/mobile/attendance/action (check in/out)
- GET /api/v1/mobile/attendance/history
- GET /api/v1/mobile/leaves/balances
- POST /api/v1/mobile/leaves/create
- GET /api/v1/mobile/leaves/list
- GET /api/v1/mobile/overtime/categories
- POST /api/v1/mobile/overtime/create
- GET /api/v1/mobile/overtime/list

### Device Integration
- POST /api/v1/devices/attendance/push — ZK device attendance push (replaces hs_zk_attendance_bridge)
- GET /api/v1/devices/attendance/ping — device health check
- POST /api/v1/devices/face/images/{employee_id} — face recognition images (replaces sttl_face_attendance)

## API Design Standards

All CyCom APIs must follow:
- Versioned prefix: /api/v1/
- Authentication: Bearer JWT on all non-public endpoints
- Pagination: ?page=1&limit=50 on list endpoints
- Filtering: ?field=value on list endpoints
- Sorting: ?order=field:desc on list endpoints
- Response envelope: { success: bool, data: any, meta: {total, page, limit}, error?: string }
- Idempotency: POST endpoints accept Idempotency-Key header for bulk operations
- Bulk response: { total: N, valid: N, invalid: N, errors: [{row, field, message}] }
