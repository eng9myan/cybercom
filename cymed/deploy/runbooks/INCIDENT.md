# CyMed — Incident response runbook

Severity levels, response commitments, and the templates the on-call engineer
uses to open a war-room, communicate outward, and file the RCA. This runbook
governs both platform and product outages.

---

## Severity matrix

| SEV | Definition                                                                                  | Ack time | Comms cadence | Escalation                            |
|-----|---------------------------------------------------------------------------------------------|----------|---------------|---------------------------------------|
| SEV1| Full outage: patients cannot receive care; PHI at risk; payments halted account-wide         | 5 min    | Every 30 min  | Page CTO + CISO + Head of Product     |
| SEV2| Major degradation: one country/tenant down, one core module (RCM/EHR/Pharmacy) unavailable   | 15 min   | Every 60 min  | Page engineering manager + product on-call |
| SEV3| Minor degradation: single non-critical feature broken, workaround exists                    | 1 hour   | Twice daily   | Notify engineering channel            |
| SEV4| Cosmetic / latency: no user-visible outage, or below SLO but still functional               | 1 bus. day | Daily stand-up| File ticket, triage in weekly grooming|

Response times are for **acknowledgement**, not resolution. Once ack'd, the
on-call engineer switches to war-room mode for SEV1/SEV2.

---

## On-call template — first 15 minutes

Post the following in the incident channel the moment you page:

```
INCIDENT DECLARED — SEV{1|2|3|4}
Title:            <short description>
Started:          <UTC timestamp>
Detected by:      <alert | user report | oncall | third party>
Symptoms:         <what users/monitors are seeing>
Suspected scope:  <tenant / country / global>
Suspected cause:  <hypothesis, if any — otherwise "unknown">
Comms lead:       <name>
IC (incident commander): <name>
Scribe:           <name>
Bridge:           <link — see War-room template below>
Status page:      <will update by HH:MM UTC>
```

Then, in parallel:

1. Open the war-room bridge (below) and post the link.
2. Freeze deploys: `kubectl -n cymed annotate deploy/cymed-api deploy.freeze=incident-<id> --overwrite`
3. Snapshot the current state: `kubectl -n cymed get pods -o wide > /tmp/inc-<id>-pods.txt`
4. Start collecting logs: `stern -n cymed --since 30m > /tmp/inc-<id>-logs.txt &`
5. If DB is suspect, `kubectl -n cymed exec deploy/cymed-api -- python manage.py dbshell` and gather `pg_stat_activity`.

---

## War-room bridge template

```
CyMed Incident War Room — INC-<yyyy>-<mm>-<dd>-<seq>
Video:      https://<meet-provider>/cymed-incident-<id>
Chat:       #inc-<id> (Slack)
Docs:       https://<wiki>/incidents/INC-<id>
Runbooks:   deploy/runbooks/*.md

Roles for this incident
- IC (Incident Commander):      <name> — owns decisions and comms
- Ops lead:                     <name> — drives the mitigation
- Comms lead:                   <name> — writes status page + emails
- Scribe:                       <name> — captures timeline in the doc
- Subject-matter experts:       <list>

Ground rules
- One voice at a time on the bridge.
- All decisions logged in the timeline by the scribe.
- If it's not in the timeline, it didn't happen.
- IC calls "hands off keyboard" for any risky mitigation.
```

---

## External comms template

Post to the status page and, for SEV1 or customer-affecting SEV2, email the
customer distribution list within 30 minutes of declaration.

### Initial

```
Subject: [CyMed] Investigating service disruption (SEV{1|2})

We are investigating an issue affecting <affected surface — e.g. "the RCM
module for tenants in Jordan" | "all API traffic to api.cymed.example.com">.

Detected at:   <UTC timestamp>
Impact:        <what users see / cannot do>
Current status: Engineers are investigating. We will provide the next update
by <UTC timestamp + 30 min>.

We are sorry for the disruption.
```

### Update

```
Subject: [CyMed] Update on service disruption (SEV{1|2})

We continue to investigate <symptom>. So far we have:

- Confirmed that <fact>
- Ruled out <fact>
- Started <mitigation>

Impact: <unchanged | now limited to X | now fully restored>
Next update by: <UTC timestamp + cadence>
```

### Resolved

```
Subject: [CyMed] Resolved: service disruption (SEV{1|2})

The issue affecting <surface> was resolved at <UTC timestamp>. Total impact
duration: <hh:mm>.

Root cause (preliminary): <one sentence>
Remediation applied: <one sentence>
Follow-up: A full post-mortem will be published within 5 business days.

Thank you for your patience.
```

---

## Timeline (scribe fills during incident)

| Time (UTC) | Actor | Event                                                    |
|------------|-------|----------------------------------------------------------|
| 14:03      | Alert | PagerDuty fires "api-p95-latency > 2s"                   |
| 14:04      | On-call | Acknowledges page                                      |
| 14:06      | IC    | Declares SEV2, opens war room, freezes deploys           |
| 14:12      | Ops   | Confirms elevated latency correlates with new RDS query  |
| 14:20      | Ops   | Rolls back API to sha-<prev>; latency recovers within 3m |
| 14:23      | Comms | Posts status page update: mitigated                      |
| 14:35      | IC    | Declares incident resolved; keeps war room open 60 min   |
| 15:35      | IC    | Closes incident. Assigns RCA owner and due date.         |

---

## Root Cause Analysis (RCA) template

Publish within 5 business days of SEV1 or SEV2. Distribute to
`engineering@`, `product@`, and the customer distribution list.

```
# INC-<id> — <one-line title>

**Status:** resolved
**Severity:** SEV{1|2|3|4}
**Impact window:** <start> - <end> UTC (<hh:mm>)
**Impact surface:** <what/who was affected, quantified where possible>
**IC:** <name>
**Authors:** <names>

## Summary
One paragraph, executive-readable, no jargon.

## Impact
- Users affected: <count / percentage>
- Tenants affected: <list>
- Data at risk (yes/no): <explanation>
- Revenue impact (est.): <if applicable>

## Timeline
(Copy the scribe's timeline verbatim; expand each entry as needed.)

## Root cause
Answer the "why" chain until you bottom out on a systemic fact. Do not stop at
"human error" — human error means the system permitted the error.

## What went well
- <list — e.g. "alert fired within 60s", "rollback worked first try">

## What went wrong
- <list — e.g. "no canary; bad code hit 100% of traffic within 90s">

## Where we got lucky
- <list — e.g. "off-peak hour, so only 30% of usual load hit the bug">

## Action items
| ID | Description | Owner | Due | Priority |
|----|-------------|-------|-----|----------|
| AI-1 | <do-this-thing> | <owner> | <YYYY-MM-DD> | P0 |
| AI-2 | ...                                                           |

Each P0/P1 action item MUST have a Jira ticket linked. Assigned engineer
signs off on the ticket, not on the RCA.

## Lessons learned
Two or three paragraphs. Focus on what the org learned; avoid blame.
```

---

## Post-incident review meeting

Schedule within 5 business days. Attendees:

- IC, ops lead, scribe from the incident
- Engineering manager for the affected service
- Head of platform or CTO for SEV1
- Product owner for the affected surface
- CISO for anything touching PHI

Agenda (60 min):

1. Walk the timeline (10 min).
2. Discuss the root cause and confirm the "why" chain (15 min).
3. Review action items and challenge each: what's the blast radius if this AI
   is not done? (15 min).
4. Assign owners and due dates (10 min).
5. Blameless discussion of what we'd change about the response itself (10 min).
