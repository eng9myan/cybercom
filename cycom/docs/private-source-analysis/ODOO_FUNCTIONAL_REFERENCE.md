# Odoo Functional Reference Analysis

This document outlines the functional inventory and scope mapped from Odoo 19 Community Edition as a functional reference.

## 1. Mapped Functional Domains
* **Accounting & Finance:** Double-entry journal system, fiscal localization (JOD currency, dynamic chart of accounts), customer invoice lifecycle, and vendor bill workflows.
* **Point of Sale (POS):** Offline session sync, Edge browser connectivity, multi-pricelist capabilities, and cash handover logs.
* **Human Resources (HR):** Employee directory profiles, attendance check-ins, leave requests, shift allocations, overtime rate calculations, and monthly payroll slips.
* **Procurement:** Requisitions, multi-vendor comparison sheets, Purchase Orders (PO), and goods receiving logs.
* **Inventory & Warehousing:** Double-entry stock moves, branch transfer allocations, scraps, adjustments, and cycle counting sheets.
* **Manufacturing (MRP):** Multi-level Bills of Materials (BOM), manufacturing orders, work center routing, and quality assurance templates.

## 2. Framework Mappings
Standard Odoo framework classes (`models.Model`, `fields.Char`, etc.) are mapped to CyCom equivalent SQLAlchemy models and schema definitions to ensure clear code provenance.
