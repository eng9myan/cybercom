# Data Model Gap Analysis

This document identifies data structure gaps between standard relational models and localized operational needs.

## 1. Mapped Structural Gaps

### A. Point of Sale (POS) Orders
* **Gap:** Standard POS models do not track catering tray deposits or online aggregator commissions.
* **Resolution:** Mapped `deposit_held`, `aggregator_campaign_id`, and `delivery_charge` columns to double-entry ledger rules.

### B. Fleet & Vehicle Odometer
* **Gap:** Default vehicle listings lack absolute odometer lock bounds, letting drivers enter duplicate/invalid mileage entries.
* **Resolution:** Added `odometer_locked` and `last_mileage` checks inside `fleet.vehicle` logs to prevent out-of-order logs.

### C. Health Insurance Tiers
* **Gap:** HR models lack grade classifications matching JOD deduction configurations.
* **Resolution:** Created `hr.employee.insurance` schema supporting grade tiers and automated monthly deduction rules.
