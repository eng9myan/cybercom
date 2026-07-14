# Anabtawi Functional Reference Analysis

This document outlines the custom operational functionality mapped from the Anabtawi ERP repository as a functional reference.

## 1. Mapped Custom Capabilities
* **POS Advance Orders & Deposits:** Advance orders capturing customer downpayments and tray/pledge deposit tracking (e.g., returnable catering trays).
* **Aggregator Campaign Mappings:** Mappings for online aggregators (e.g., Talabat, Hungerstation) with campaign contributions, delivery collections, commissions, and weekly settlement reconciliations.
* **Biometric Device Logs:** Multi-device attendance ingestion service pulling ZKTeco IP events, deduplicating stamps, and normalising check-in/out logs.
* **Low-Code Workflow Engine:** Rules engine matching criteria (like departments, branches, or amount thresholds) to sequential approval lists.
* **Document Approval Workflows:** Document verification (Passport, trade licenses, etc.) with custom email/SMS notifications and warning triggers.
* **Audit ledger checks:** Cryptographic ledger verification using block hashing (SHA-256) to ensure historical double-entry entries have not been tampered with.
