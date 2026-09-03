# CyMed — Backup runbook

Backup topology, retention, verification schedule, and restore procedures for
Postgres data, application state, and object storage.

---

## Data classes

| Class     | Scope                                   | Backup mechanism                           |
|-----------|-----------------------------------------|--------------------------------------------|
| PHI       | Postgres tables holding patient data    | RDS automated + `pg_dump` + WAL archiving  |
| Financial | Payments, invoices, RCM tables          | Same as PHI (same DB)                      |
| Config    | Django admin/models, Ready-ERP tenants  | Same as PHI (same DB)                      |
| Artefacts | Uploads, exports, PDF reports (S3)      | S3 versioning + cross-region replication   |
| Secrets   | Sealed-secrets in Git, KMS keys         | Git history + KMS scheduled-deletion halt  |

---

## Postgres backups

Three overlapping mechanisms — belt, braces, and a spare belt.

### 1. RDS automated backups (belt)

- Enabled with `backup_retention_period = 30` and `backup_window = "02:00-03:00"`.
- Provides Point-In-Time Recovery (PITR) to any second within the retention.
- Encrypted with the RDS CMK (`cymed/<env>/rds`).
- Automatically retained across snapshots on final termination of the DB.

Retention: **30 days rolling** for PITR.

### 2. Weekly base backup + continuous WAL archive (braces)

A CronJob in the `cymed` namespace runs `pg_basebackup` weekly and
continuously archives WAL segments to the S3 artefacts bucket under
`backups/pg/wal/`.

- Weekly base backup Sunday 03:30 UTC.
- WAL segments archived every 60 seconds (or 16 MB, whichever first).
- Encrypted with the S3 CMK (`cymed/<env>/s3`).
- Bucket has versioning + object-lock (COMPLIANCE mode) for 90 days.

Retention:

| Tier      | What                                       | Retention |
|-----------|--------------------------------------------|-----------|
| Hot       | Last 7 daily base backups                  | 30 days   |
| Warm      | Weekly base backups                        | 90 days   |
| Cold      | Monthly base backups (first Sunday)        | 365 days  |
| Archive   | Yearly base backup (first Sunday of Jan)   | 7 years   |

Lifecycle policy on `s3://cymed-artifacts-<env>/backups/pg/` moves objects
to `STANDARD_IA` at 30 days and `GLACIER_DEEP_ARCHIVE` at 90 days.

### 3. Daily `pg_dump` — logical (spare belt)

A separate CronJob runs `pg_dump --format=custom --compress=9` daily at
02:30 UTC and stores the dump under `backups/pg/logical/YYYY/MM/DD/`.

- Enables per-table restores.
- Enables restore to a different Postgres version.
- Encrypted with the S3 CMK.

Retention: **30 daily, 12 monthly, 7 yearly**.

---

## S3 (artefact) backups

- Versioning enabled on `cymed-artifacts-<env>-<acct>`.
- Cross-region replication to `cymed-artifacts-dr-<acct>` in `us-west-2`,
  encrypted with the DR-region CMK.
- Replication metrics + CloudWatch alarm if replication lag > 15 min.
- Non-current versions expire at 365 days.

---

## KMS envelope

- One CMK per data class (`rds`, `s3`, `secrets`).
- CMKs have automatic key rotation enabled (yearly).
- Deletion window: 30 days; any scheduled deletion pages the security oncall.
- CMK ARNs listed in `deploy/terraform/aws/outputs.tf` (`kms_key_arns`).

---

## Verification schedule

If a backup was never restored, it doesn't exist. We test the restores.

| Cadence  | What is verified                                        | Owner   |
|----------|---------------------------------------------------------|---------|
| Daily    | Automated: pg_restore to a scratch DB in the same VPC   | Platform|
| Weekly   | Random-sample table checksums after logical restore      | DBA     |
| Monthly  | S3 restore drill — recover an object from a prior day    | SRE     |
| Quarterly| Full DR restore (see `DR.md`)                            | SRE lead|

Daily verification job:

- CronJob `pg-backup-verify` fires daily 06:00 UTC.
- Spins up a scratch RDS instance (`db.t4g.medium`, no Multi-AZ) restored
  from the latest snapshot.
- Runs `SELECT COUNT(*) FROM …` on canary tables.
- Pushes result to CloudWatch metric `CyMed/Backups/RestoreOk`.
- Alerts PagerDuty if 0 successes in the last 25 hours.
- Terminates the scratch instance.

---

## Restore procedures

### PITR to the primary DB (data corruption in place)

Use when a bad migration or a bad app write corrupted data less than 30 days
ago and you want to restore in place.

- [ ] Freeze writes at the app layer: set feature flag `MAINT_READ_ONLY=1`
      and confirm workers stop enqueuing writes.
- [ ] Choose a restore point 60 seconds before the bad event:
      `T = <UTC timestamp just before the incident>`.
- [ ] `aws rds restore-db-instance-to-point-in-time --source-db-instance-identifier cymed-prod-pg --target-db-instance-identifier cymed-prod-pg-pitr --restore-time <T> --db-instance-class db.m6g.large`
- [ ] Wait until available. Do NOT delete the original.
- [ ] Point the app at the new endpoint (rotate the sealed secret in the
      overlay, re-apply, rolling restart of the API + workers).
- [ ] Confirm data is correct; unfreeze writes.
- [ ] Once verified good, schedule the old instance for retention snapshot,
      then delete.

### PITR to a scratch DB (data recovery only)

Use when you need to recover a single record without disturbing production.

- [ ] Same as above but call the scratch instance `cymed-prod-pg-scratch`.
- [ ] Restore, then `pg_dump -t <table> --data-only` the affected rows.
- [ ] `psql` the rows back into production under a manual transaction.
- [ ] Log the restore in the compliance register (PHI touch).

### Logical restore from `pg_dump`

Use when you need to restore to a fresh, empty Postgres (upgrade, migration,
scratch environment for triage).

- [ ] Pull the dump: `aws s3 cp s3://cymed-artifacts-<env>/backups/pg/logical/<yyyy>/<mm>/<dd>/cymed.dump .`
- [ ] `createdb cymed_restore`
- [ ] `pg_restore --dbname=cymed_restore --jobs=4 --no-owner --no-privileges cymed.dump`
- [ ] Verify row counts on canary tables.

### S3 object restore

Use when a specific object was overwritten or deleted.

- [ ] List versions: `aws s3api list-object-versions --bucket cymed-artifacts-<env> --prefix <key>`
- [ ] Copy the desired version to a new key or restore in place:
      `aws s3api copy-object --bucket cymed-artifacts-<env> --copy-source cymed-artifacts-<env>/<key>?versionId=<v> --key <key>`

### Full S3 bucket restore (from DR replica)

- [ ] `aws s3 sync s3://cymed-artifacts-dr-<acct>/ s3://cymed-artifacts-<env>/ --region us-east-1 --exclude "logs/*"`
- [ ] Verify object count and a sample of checksums.

---

## Compliance notes

- All backups holding PHI inherit the same HIPAA controls as the source DB.
- Access to backup buckets is via IAM roles with break-glass MFA only.
- Every restore of PHI is logged in the compliance register with:
  - who initiated the restore
  - what data was touched (schemas, tables, row count)
  - business justification
  - deletion date for any scratch copies (must be ≤ 7 days)
