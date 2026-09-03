# CyMed — Rollback runbook

Fast, low-drama procedure to unwind a bad release. Covers code rollout,
database schema restore, feature-flag emergency-off, and the comms plan.

Choose the first section that fits your situation. When in doubt, go with the
faster reversible option (feature flag off, then rollout undo) before touching
the database.

---

## Decision tree

```
Is the site down or actively harming users right now?
├── YES -> Skip to §1 Feature flag emergency-off. If no flag covers it,
│          §2 Kubectl rollout undo. Comms in §5.
└── NO  -> Is the bad release causing subtle errors (bad calc, missing data)?
    ├── YES -> §2 Kubectl rollout undo first; do NOT restore the DB unless
    │          the release also wrote bad data. If it did, §3 DB restore.
    └── NO  -> Investigate more, this isn't a rollback situation.
```

---

## 1. Feature flag emergency-off

The safest, fastest rollback — no pod restarts, no DB touching.

- [ ] Identify the flag(s) governing the broken feature. Flag registry lives
      in `products/cymed/platform/feature_flags.py`.
- [ ] Set the flag off via the admin API:
      `curl -X POST https://api.cymed.example.com/api/admin/flags/<flag-name> \
        -H "Authorization: Bearer $BREAKGLASS_TOKEN" \
        -d '{"enabled": false, "reason": "emergency-off INC-<id>"}'`
- [ ] Confirm rollout by hitting the affected endpoint from an unaffected
      account.
- [ ] Log the change in `#incidents` channel and the war room timeline.

If no flag exists for the broken code path, that's an RCA action item — every
new feature ships behind a flag.

---

## 2. `kubectl rollout undo`

Rolls the API/worker/beat Deployments back to the last known-good revision.
Takes ~60-120 seconds per Deployment.

Pre-flight:

- [ ] `kubectl -n cymed rollout history deployment/cymed-api` — confirm the
      previous revision exists and identify the target REVISION number.
- [ ] Freeze new deploys:
      `kubectl -n cymed annotate deployment/cymed-api deploy.freeze=rollback-INC-<id> --overwrite`
- [ ] Freeze the image tag in the overlay so re-applies don't re-forward.

Roll back API first, then workers, then beat (least-write-risk order):

```bash
# API
kubectl -n cymed rollout undo deployment/cymed-api --to-revision=<REV>
kubectl -n cymed rollout status deployment/cymed-api --timeout=5m

# Workers — mid-flight tasks will finish under old code
kubectl -n cymed rollout undo deployment/cymed-worker --to-revision=<REV>
kubectl -n cymed rollout status deployment/cymed-worker --timeout=5m

# Beat (singleton — brief scheduling gap during pod swap)
kubectl -n cymed rollout undo deployment/cymed-beat --to-revision=<REV>
kubectl -n cymed rollout status deployment/cymed-beat --timeout=2m
```

Verify:

- [ ] `kubectl -n cymed get pods -o wide` — all pods running the old image.
- [ ] `curl -f https://api.cymed.example.com/health` still 200.
- [ ] Smoke test the broken workflow — confirm it's no longer broken.
- [ ] Check Sentry / logs for the error signature that triggered the incident;
      confirm rate drops to zero within 5 minutes.

Update Kustomize overlay so redeploy doesn't re-forward:

- [ ] Edit `deploy/k8s/overlays/prod/kustomization.yaml` `images:` block; pin
      the `newTag` back to the previous good SHA.
- [ ] Commit and push with message `revert: pin to sha-<prev> after INC-<id>`.

---

## 3. Database restore point selection

Only touch the DB if the rolled-back code wrote data that is now
inconsistent, or if a migration destroyed data.

- [ ] Confirm with the DBA (or on-call platform engineer) that a DB restore
      is warranted.
- [ ] If the bad release included a schema migration:
      `kubectl -n cymed exec deploy/cymed-api -- python manage.py showmigrations`
      to see what applied.

### Option A: Reverse the schema migration (preferred)

- [ ] Identify the migration to reverse. Roll back to the last good migration
      number:
      `kubectl -n cymed exec deploy/cymed-api -- python manage.py migrate <app_label> <previous_migration_number>`
- [ ] Verify: `python manage.py showmigrations <app_label>` shows the target
      migration as unapplied.
- [ ] If the migration was non-reversible or data-destructive, do NOT use
      Option A — jump to Option B.

### Option B: PITR to just-before-bad-release

Follow `BACKUP.md` §"PITR to the primary DB (data corruption in place)".

- [ ] Freeze writes (feature flag `MAINT_READ_ONLY=1`).
- [ ] Pick the restore point 60 seconds before the bad release started
      rolling out.
- [ ] Restore, cut endpoint, unfreeze.

### Option C: Selective row-level recovery

Use when only a handful of records were affected and the rest of the DB is
fine. Follow `BACKUP.md` §"PITR to a scratch DB (data recovery only)" and
apply a manual patch.

---

## 4. Verify recovery

- [ ] All health endpoints 200.
- [ ] The specific error signature that triggered the incident stopped
      appearing in the last 15 minutes of logs.
- [ ] End-to-end smoke test of the affected workflow passes.
- [ ] HPA scale-down complete (if the incident spiked replicas).
- [ ] Celery queue depth back to steady-state.
- [ ] No unexpected user reports in the last 15 minutes.

Only when all six boxes are checked does the IC declare the incident
mitigated.

---

## 5. Comms plan

### Internal

- [ ] Post in `#incidents` at each stage: rollback started, rollback done,
      verification passed, mitigated.
- [ ] War-room scribe logs the exact commands and revisions used.

### External

Use the templates in `INCIDENT.md`. Specific to a rollback:

- Initial notice mentions "we are rolling back the change" not "we are
  investigating" — customers appreciate specificity.
- Update notice states the mitigation is applied and users should see
  recovery within N minutes.
- Resolved notice references the RCA due date.

Example resolved notice:

```
Subject: [CyMed] Resolved: service disruption

The issue affecting <surface> was resolved at <UTC timestamp> by rolling
back the deployment that introduced it. Total impact: <hh:mm>.

Root cause (preliminary): a change to <area> shipped in release <sha-XXXX>
introduced a regression that <one-sentence description>.

Remediation: rolled back to release <sha-YYYY>. A follow-up fix is being
developed and will be re-released with additional testing.

Full post-mortem within 5 business days.
```

---

## 6. Post-rollback

- [ ] Un-freeze deploys:
      `kubectl -n cymed annotate deployment/cymed-api deploy.freeze-`
      (only after the fix is verified in staging).
- [ ] File the RCA using the template in `INCIDENT.md`.
- [ ] Add action items for:
  - What CI check would have caught this?
  - Was a canary in place? If not, why?
  - Was the change guarded by a feature flag? If not, why?
- [ ] Update this runbook if any step didn't work as documented.
