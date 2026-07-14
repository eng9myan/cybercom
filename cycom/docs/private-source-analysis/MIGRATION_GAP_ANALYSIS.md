# Migration Gap Analysis

This document outlines structural mapping requirements for transferring legacy double-entry entries and HR records.

## 1. Migration Scopes
* **Chart of Accounts:** Maps legacy IDs to standard Unified COA codes. Stores original references in private migration tables.
* **Employee Directory:** Standardises National ID, English/Arabic names, bank IBAN formats, and department/contract mappings.
* **Inventory Balance Import:** Maps product codes, branch SKU balances, minimum/maximum safety stock parameters, and price lists.

## 2. Integrity Checks
* **Maker-Checker Constraint:** Double-entry journal imports must balance (`sum(Debit) == sum(Credit)`) on each transaction block.
* **National ID Validation:** Enforces structural validations to detect duplicate records.
