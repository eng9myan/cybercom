# CyMed — Disaster Recovery plan

Recovery objectives, quarterly drill schedule, and step-by-step restore
procedure for the CyMed production environment.

---

## Objectives

| Objective | Target                                                                 |
|-----------|------------------------------------------------------------------------|
| RTO       | 4 hours (time from disaster declaration to production traffic resumed) |
| RPO       | 15 minutes (max acceptable data loss)                                  |

RPO is met by continuous WAL archiving for Postgres (see `BACKUP.md`) and
15-minute RDS automated backups. RTO is met by the pre-provisioned warm
standby in the DR region + this runbook practised quarterly.

---

## Failure scenarios covered

1. **AZ failure** — single AZ in primary region goes dark. Handled by
   Multi-AZ RDS, ElastiCache with Multi-AZ, EKS node group across three AZs.
   No DR invocation needed; operations continue.
2. **Region failure** — entire primary AWS region unavailable. DR invocation
   required (this document).
3. **Data corruption** — table dropped, wrong migration applied, ransomware.
   Restore in place via PITR (see `BACKUP.md` §PITR restore).
4. **KMS key deletion** — CMK schedules deletion. 30-day window; halt the
   scheduled deletion and rotate application to a new CMK.
5. **S3 bucket loss** — versioning + cross-region replication saves us
   (see `BACKUP.md`).

---

## DR region topology

- **Primary:** `us-east-1`
- **DR:** `us-west-2`

Pre-provisioned in DR:

- VPC + subnets (matching CIDRs but different AZs)
- EKS cluster scaled to 1 node group, 1 node (warm)
- RDS read replica of primary DB (cross-region), promotable to standalone
- S3 bucket with cross-region replication from `cymed-artifacts-prod-*`
- KMS CMKs mirrored (per data class)
- Route53 secondary record set with failover policy pointing at DR ALB
- Sealed-secrets controller installed; sealed secrets committed in overlay
  `deploy/k8s/overlays/dr/`

---

## Quarterly DR drill schedule

Drill happens the last Friday of the quarter, 09:00 local time. Duration
budget: half a day. Owner: SRE on-call rotation lead.

| Quarter | Scope                                                          | Owner        |
|---------|----------------------------------------------------------------|--------------|
| Q1      | Restore RDS from snapshot to DR region into a scratch instance | SRE + DBA    |
| Q2      | Full DNS cut to DR, run smoke suite, cut back                  | SRE + Product|
| Q3      | Restore latest S3 backup to a scratch bucket, verify hashes    | SRE          |
| Q4      | End-to-end DR: assume primary region is gone; run this doc     | Entire team  |

Drill outputs: filled `DR-DRILL-<yyyy-qN>.md` in the runbooks folder covering
timing per step vs. RTO, gaps found, and action items.

---

## Restore procedure — region failure

Follow in order. Every step ends with a checkpoint the IC must confirm.

### T+0: Declare and activate

- [ ] IC declares "DR-INVOKE" in the incident channel and pages CTO + CISO.
- [ ] Confirm primary region status via AWS Health Dashboard.
- [ ] Post initial customer comm (see `INCIDENT.md` external template),
      explicitly stating "we are failing over to our secondary region".
- [ ] Freeze all deploys.

### T+10 min: Promote RDS read replica in DR

- [ ] `aws rds promote-read-replica --region us-west-2 --db-instance-identifier cymed-dr-pg`
- [ ] Poll status until "available": `aws rds describe-db-instances --region us-west-2 --db-instance-identifier cymed-dr-pg --query 'DBInstances[0].DBInstanceStatus'`
- [ ] Capture the new writer endpoint. Update the sealed `DATABASE_URL`
      secret in `deploy/k8s/overlays/dr/sealed-secret.env.yaml` (already
      pre-sealed with the DR endpoint — verify).

### T+20 min: Verify S3 replication is caught up

- [ ] Compare object counts between prod and DR bucket:
      `aws s3 ls s3://cymed-artifacts-prod-<acct>/ --recursive --summarize`
      vs. `... --region us-west-2 s3://cymed-artifacts-dr-<acct>/ --recursive --summarize`
- [ ] If lag > 15 min, note it in the timeline (RPO exceeded — will be an
      RCA action item).

### T+30 min: Scale EKS DR cluster to production size

- [ ] `aws eks update-nodegroup-config --region us-west-2 --cluster-name cymed-dr --nodegroup-name default --scaling-config desiredSize=3,minSize=2,maxSize=10`
- [ ] Wait for nodes: `kubectl --context cymed-dr get nodes --watch`

### T+40 min: Apply the DR overlay

- [ ] `kubectl --context cymed-dr apply -k deploy/k8s/overlays/dr`
- [ ] `kubectl --context cymed-dr -n cymed rollout status deploy/cymed-api --timeout=10m`
- [ ] Same for `cymed-worker` and `cymed-beat`.
- [ ] Verify: `kubectl --context cymed-dr -n cymed get pods`

### T+60 min: Run migrations & smoke tests

- [ ] `kubectl --context cymed-dr -n cymed exec deploy/cymed-api -- python manage.py migrate --check`
      (should already be up-to-date — the promoted replica has all migrations)
- [ ] Run smoke suite against internal ALB:
      `curl -f https://<dr-alb>/health` and the read-only paths in the smoke
      test collection.

### T+90 min: Cut DNS to DR

- [ ] Update Route53 primary record: change the alias from
      `cymed-prod-alb` to `cymed-dr-alb`, or manually flip the failover
      policy to make DR the active target.
- [ ] TTL is 60 seconds — expect propagation within 2 minutes globally.
- [ ] Verify externally: `dig api.cymed.example.com +short` from multiple
      locations.

### T+120 min: Enable writes and confirm

- [ ] Post customer comm: "DR site is live; service is restored".
- [ ] Monitor for 30 minutes at DR before scaling back monitors.
- [ ] Keep war room open for at least 2 hours after cut.

### T+2-24 hr: Stabilise

- [ ] Bring HPA up to normal min/max.
- [ ] Confirm Celery beat is running (singleton lock acquired in DR Redis).
- [ ] Confirm all scheduled tasks fired on their next window.
- [ ] Verify object storage writes are landing in the DR bucket.

### Failback (once primary region recovers)

Failback is a planned change, not an incident. Schedule during a maintenance
window with the customer distribution list notified 48h in advance.

- [ ] Re-establish primary as the passive site: create a new RDS read replica
      in `us-east-1` from the (now-primary) DR instance.
- [ ] Wait for replica lag < 30 seconds.
- [ ] Freeze writes for 5 minutes at the app layer (feature flag).
- [ ] Promote the `us-east-1` replica.
- [ ] Cut DNS back to the primary ALB.
- [ ] Unfreeze writes.
- [ ] Re-establish cross-region replication in the original direction.

---

## Post-DR RCA

Same template as `INCIDENT.md`, plus these DR-specific sections:

- Actual RTO vs. target (4h)
- Actual RPO vs. target (15 min)
- Deviations from this runbook (each is an action item)
- Data-consistency check outcome (any orphaned records? partial writes?)
