# Data Retention Policy — CyMed

## PHI retention windows

| Data type | Region | Retention | Legal basis |
|---|---|---|---|
| Medical records (adults) | KSA | Life + 10y | Saudi Health Practice Law |
| Medical records (minors) | KSA | Until age 25 | Saudi Health Practice Law |
| Medical records (adults) | Jordan | 15y from last visit | Jordan MoH regulations |
| Medical records (adults) | EU | 10y minimum | Member-state health law |
| Financial records / bills | Global | 7y | Tax + audit |
| ZATCA e-invoices | KSA | 6y | ZATCA regulation |
| JoFotara e-invoices | Jordan | 5y | JoFotara regulation |
| Audit logs (system) | Global | 7y | HIPAA § 164.316(b)(2)(i) |
| NFC scan logs | Global | 3y after card revoked | Internal |
| Consent grants | Global | Duration + 7y | Evidence for lawful basis |
| Payment tx | Global | 7y | Financial + AML |
| Marketing opt-in | Global | Until opt-out | GDPR |

## Deletion / anonymisation

- **Soft-delete** by default (`SoftDeleteMixin`).
- **Hard-erasure wizard** (staff-triggered on GDPR Art 17 request) — cascade delete PHI + payments + records; audit trail keeps hashed identifier only.
- **Automatic purge** — nightly Celery task deletes rows past retention window and creates aggregate anonymised copy for statistics.

## Backups

- Daily snapshots retained 35 days
- Monthly snapshots retained 12 months
- Yearly snapshots retained 7 years (encrypted, offline)
- Restore drill: quarterly

## Right to erasure interaction

Requests logged to `platform.audit`. Processing SLA: 30 calendar days per GDPR Art 12(3). Denials require documented lawful basis (e.g. ongoing treatment, litigation hold).
