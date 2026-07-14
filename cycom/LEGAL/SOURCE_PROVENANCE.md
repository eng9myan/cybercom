# Source Provenance Record

This file documents the clean-room origin of all code paths inside CyCom ERP.

---

## 1. Frontend Web App (`/cycom-erp`)
* **Origin:** 100% clean-room Tailwind & Next.js implementation developed from scratch using the CyberCom design system.
* **Branding:** Uses CyCom ERP logos, typography, and menus.
* **Separation:** Exposes ZERO Odoo views directly; all communication runs via clean REST/JSON-RPC protocols.

---

## 2. Micro-Kernel Services (`/core-kernel`)
* **Origin:** CyberCom proprietary integrations for JoFotara tax XML generation, NLP-based bank reconciliation matching, low-code conditional workflow rule evaluation, and cryptographic ledger verification.
* **Separation:** Decoupled from Odoo runtime and executed in separate python environments.

---

## 3. Custom Modules (`/cycom-platform/addons/cycom_modules`)
* **Origin:** Jordanian localizations and branch management logic derived from reference systems but audited to ensure all prohibited names are purged.
* **Attribution:** Original legal authorship notices are preserved inside module-level LICENSE files without applying CyberCom copyright to third-party code.
