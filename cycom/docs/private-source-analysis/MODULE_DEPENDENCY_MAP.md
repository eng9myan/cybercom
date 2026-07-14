# Module Dependency Map

This document tracks the dependency relationships between CyCom ERP backend models, services, and localizations.

## 1. Core Services Dependency Graph
* **CyIdentity (`core-kernel/auth.py`):** Base permission provider. Uniquely maps user contexts onto tenant DB sessions.
  * *Depends on:* None (Base Layer)
* **Double-Entry Accounting Engine (`core-kernel/rpc.py`):** Registers accounts, journals, and posted entries.
  * *Depends on:* CyIdentity (permissions, locks)
* **Inventory & Warehouse Services (`core-kernel/rpc.py`):** Validates stock levels, putaway locations, and replenishment rules.
  * *Depends on:* Double-Entry Accounting (Landed costs, COGS journals)
* **Procurement Lifecycle:**
  * *Depends on:* Inventory (reorder triggers), Accounting (vendor bills)
* **Human Resources & Payroll:**
  * *Depends on:* Attendance (check-in events), Planning (shift schedules), Accounting (payslip journal entries)

## 2. Localization Addons
* **JoFotara Tax Engine:**
  * *Depends on:* Accounting (journal invoices)
