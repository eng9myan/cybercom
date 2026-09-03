# Admin Runbook — Tenant Operations

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Head of SRE — TBD>` |
| Review cadence | Quarterly |

---

## 0. Scope and safety

This runbook covers routine administrative operations performed by CyMed staff and by Customer-side tenant admins. Every action is **audit-logged**; sensitive actions require a documented reason. Do not perform actions on production tenants without a ticket or change record.

Prerequisites for every procedure:
- Named actor with a valid CyMed staff SSO / Customer admin login.
- MFA satisfied within the last 15 minutes.
- Just-in-time elevation approved (for CyMed staff on Customer tenants).
- Reason string captured in the audit trail.

Commands below assume the CyMed CLI (`cymedctl`) or the equivalent admin console flow; both hit the same authenticated APIs.

---

## 1. Creating a Tenant

**When:** New Customer signs; new environment (staging / DR) required.

**Preconditions:** Signed Order Form; tenant plan configuration; hosting region confirmed; DPO informed if a new region is involved.

**Steps:**
1. Open ticket `TENANT-CREATE-<customer>-<env>`; attach Order Form.
2. Run
   ```
   cymedctl tenant create \
     --name "<Customer legal name>" \
     --slug <slug> \
     --region <me-central-1|eu-central-1|us-east-1|...> \
     --plan <edition:tier> \
     --billing-account <acct-id> \
     --dpa-status active \
     --baa-status <active|not-required> \
     --reason "TICKET-<id>"
   ```
3. Verify tenant appears in the control plane with expected editions + tier.
4. Provision baseline: default org unit, default facility, first admin invite.
5. Send admin invite to Customer contact via secure link (expires in 72 h).
6. Update tenant register (`ops/tenant_register.yaml`).

**Postconditions:** Tenant status = `provisioning-complete`; audit log entry present.

---

## 2. Provisioning / Changing Editions

**When:** Customer buys an additional edition or moves between Pilot/Standard/Enterprise.

**Preconditions:** Order Form amendment on file; billing updated.

**Steps:**
1. Confirm entitlement change in the billing system.
2. Run
   ```
   cymedctl tenant plan set --tenant <slug> \
     --add-edition <lab|imaging|pharmacy|ecosystem> \
     --tier <pilot|standard|enterprise> \
     --effective <YYYY-MM-DD> \
     --reason "TICKET-<id>"
   ```
3. Verify feature flags flipped correctly per the Feature Matrix.
4. Notify Customer admin + CSM. If SLA tier changed, update the SLA monitor targets.
5. For tier downgrades: confirm no active hypercare or open SEV1 tickets before applying.

---

## 3. Resetting a User's MFA

**When:** User has lost their MFA device; needs to re-enroll.

**Preconditions:** Requestor identity verified by tenant admin per Customer's identity policy (usually via a verified callback to the person's registered phone).

**Steps:**
1. Locate user: `cymedctl user find --tenant <slug> --email <email>`.
2. Confirm the last 4 digits of the user's registered phone with the requestor (do **not** read it out).
3. Reset:
   ```
   cymedctl user mfa reset --tenant <slug> --user <user-id> \
     --reason "ID-verified callback OK, TICKET-<id>"
   ```
4. Force session revoke (see §4) if account compromise is suspected.
5. User receives a re-enrollment email with a short-lived link; MFA re-enroll must complete within 30 minutes.
6. Confirm re-enrollment via audit log. Close ticket.

**Never** reset MFA based on an email or chat request alone. **Never** communicate MFA codes.

---

## 4. Revoking Sessions

**When:** Lost device, suspected compromise, terminated employee, or as follow-up to MFA reset.

**Steps:**
1. Immediately:
   ```
   cymedctl user sessions revoke --tenant <slug> --user <user-id> \
     --reason "TICKET-<id>"
   ```
2. If broader compromise suspected (e.g., stolen laptop with cached tokens):
   ```
   cymedctl user tokens revoke-all --tenant <slug> --user <user-id> \
     --include-refresh --include-api-tokens \
     --reason "TICKET-<id>"
   ```
3. Force password rotation on next login.
4. If account was privileged, run access review: list objects modified in the last 24 h; report to CySec.

---

## 5. Exporting Audit Logs

**When:** Customer request (regulator, internal investigation, HR); CyMed internal investigation.

**Preconditions:** Customer request has a valid ticket + tenant-admin authorisation. For CyMed-internal exports on a Customer tenant: written Customer authorisation or an active DPA / BAA reason (e.g., breach investigation) documented in the ticket.

**Steps:**
1. Scope the request: tenant, actor(s), object types, date range.
2. Run
   ```
   cymedctl audit export --tenant <slug> \
     --from <ISO-8601> --to <ISO-8601> \
     --actor <optional> --object-type <optional> \
     --format <csv|jsonl> \
     --out s3://<tenant-exports-bucket>/audit/<ticket-id>.jsonl.gz \
     --reason "TICKET-<id> — <requestor + purpose>"
   ```
3. Encrypted export lands in the Customer's exports bucket; share via signed link with expiry ≤ 7 days.
4. Deliver a chain-of-custody note (query, filters, timestamp, actor, hash of export).
5. Purge signed link on receipt confirmation.

**Never** export audit logs to a personal device or unmanaged endpoint.

---

## 6. Freezing Accounts

**When:** Compromise investigation, terminated employee (long-lead offboarding), or per Customer request pending investigation.

**Steps:**
1. Freeze:
   ```
   cymedctl user freeze --tenant <slug> --user <user-id> \
     --reason "TICKET-<id>"
   ```
   Freeze prevents login but preserves the user record and their attributions in clinical / financial documents.
2. Revoke sessions and tokens (§4).
3. If clinical: reassign open encounters, unsigned notes, and pending orders per Customer clinical governance.
4. To unfreeze:
   ```
   cymedctl user unfreeze --tenant <slug> --user <user-id> \
     --reason "TICKET-<id> — investigation complete, cleared"
   ```

**Do not delete** clinical users. Deletion breaks legal attribution and audit chains. Freeze + rename via HR flow only.

---

## 7. Break-glass Access

**When:** Emergency access needed to serve a patient; normal role does not authorise.

**Steps:**
1. User clicks **Break-glass**, selects patient, enters clinical reason.
2. System grants time-boxed access (default 4 h) with an enhanced audit event.
3. Notification pushed to CustClin, CustCompl, and the on-call medical director.
4. Post-event review within 5 business days; documented in the incident register.

Admins **cannot** disable break-glass reviews.

---

## 8. Emergency Suspension / Ejection

**When:** Confirmed active PHI exfiltration, ransomware indicators, or explicit regulator directive.

**Steps:**
1. Incident Commander declared per IR plan.
2. Suspend tenant writes:
   ```
   cymedctl tenant readonly on --tenant <slug> --reason "IR-<id>"
   ```
3. Preserve state: forensic snapshot of DB, object store, and event stream (retention ≥ 90 days).
4. Coordinate notifications per DPA / BAA / regulatory obligations.
5. Return to normal only on IR Commander + CISO + Customer Executive Sponsor written approval.

---

## 9. Routine change hygiene

- **Change windows:** significant changes (schema migrations, tenant plan changes, region moves) run in the low-traffic window declared for the tenant.
- **Two-person rule:** production destructive operations require two-person approval logged in the ticket.
- **No secrets in tickets:** paste hashes / IDs only.
- **Test in staging first:** all migrations run in the tenant's staging clone before production.
