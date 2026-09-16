"use client";

import { useCallback, useEffect, useState } from "react";
import { KeyRound, ShieldCheck, ShieldAlert, Copy } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { fmtDateTime } from "@/lib/portal";

/**
 * Two-factor authentication.
 *
 * Enrolment is for the signed-in account only — every endpoint behind this
 * screen derives its subject from the token, and there is no field anywhere to
 * name someone else. An admin cannot enrol or disable a factor on a colleague's
 * behalf from here, which is the property that stops a stolen session
 * stripping someone's second factor.
 *
 * The coverage panel is the leadership view: what proportion of staff actually
 * have one. It names nobody, because the useful action is a policy, not a
 * conversation about an individual.
 */

type Status = {
  enrolled: boolean;
  confirmed: boolean;
  label?: string;
  confirmed_at?: string | null;
  last_verified_at?: string | null;
  backup_codes_remaining: number;
  step_up_active: boolean;
  locked_out: boolean;
};

type Coverage = {
  active_staff: number;
  with_mfa: number;
  without_mfa: number;
  coverage_pct: number;
};

type SecurityEvent = {
  id: string;
  event_type: string;
  severity: string;
  actor_email: string;
  actor_roles: string;
  ip: string;
  detail: string;
  created_at: string;
};

export default function SecurityPage() {
  const [view, setView] = useState<"mine" | "coverage" | "events">("mine");
  const [status, setStatus] = useState<Status | null>(null);
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [secret, setSecret] = useState<string | null>(null);
  const [uri, setUri] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null);
  const toast = useToast();

  const loadStatus = useCallback(async () => {
    try {
      setStatus(await cyed.get<Status>("security/mfa/status/"));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not read your MFA status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    if (view === "coverage") {
      cyed
        .get<Coverage>("security/enrollments/coverage/")
        .then(setCoverage)
        .catch(() => setCoverage(null));
    }
    if (view === "events") {
      cyed
        .list<SecurityEvent>("security/events/")
        .then(setEvents)
        .catch(() => setEvents([]));
    }
  }, [view]);

  const enrol = async () => {
    setBusy(true);
    try {
      const r = await cyed.action<{ secret: string; otpauth_uri: string }>("security/mfa/enroll/");
      setSecret(r.secret);
      setUri(r.otpauth_uri);
      toast.push("Secret issued. Add it to your authenticator, then confirm.");
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not start enrolment");
    } finally {
      setBusy(false);
    }
  };

  const confirm = async () => {
    if (code.trim().length < 6) return;
    setBusy(true);
    try {
      const r = await cyed.action<{ backup_codes: string[] }>("security/mfa/confirm/", { code });
      // Shown exactly once — the server keeps only hashes from here.
      setBackupCodes(r.backup_codes);
      setSecret(null);
      setUri(null);
      setCode("");
      toast.push("Two-factor authentication is on.");
      await loadStatus();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "That code was not accepted");
    } finally {
      setBusy(false);
    }
  };

  const regenerate = async () => {
    if (code.trim().length < 6) {
      toast.push("Enter a current code from your authenticator first.");
      return;
    }
    setBusy(true);
    try {
      const r = await cyed.action<{ backup_codes: string[] }>("security/mfa/backup-codes/", { code });
      setBackupCodes(r.backup_codes);
      setCode("");
      toast.push("New codes issued. The previous set no longer works.");
      await loadStatus();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not issue new codes");
    } finally {
      setBusy(false);
    }
  };

  const disable = async () => {
    if (code.trim().length < 6) {
      toast.push("Turning MFA off requires a current code — a stolen session must not strip it.");
      return;
    }
    if (!window.confirm("Turn off two-factor authentication for your account?")) return;
    setBusy(true);
    try {
      await cyed.action("security/mfa/disable/", { code });
      setBackupCodes(null);
      setCode("");
      toast.push("Two-factor authentication is off.");
      await loadStatus();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not turn it off");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Security"
        subtitle="Two-factor authentication for your account"
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "mine", label: "My account" },
              { value: "coverage", label: "Staff coverage" },
              { value: "events", label: "Audit trail" },
            ]}
          />
        }
      />

      {view === "mine" && (
        <>
          <Panel
            title="Status"
            action={
              status?.confirmed ? (
                <Badge value="active" />
              ) : status?.enrolled ? (
                <Badge value="pending" />
              ) : (
                <Badge value="not enrolled" />
              )
            }
          >
            <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
              {status?.confirmed ? (
                <ShieldCheck size={20} style={{ color: "var(--green, #34d399)", flexShrink: 0 }} />
              ) : (
                <ShieldAlert size={20} style={{ color: "var(--amber, #fbbf24)", flexShrink: 0 }} />
              )}
              <div style={{ fontSize: "0.9rem", color: "var(--muted)" }}>
                {status?.confirmed ? (
                  <>
                    Second factor active
                    {status.confirmed_at && ` since ${fmtDateTime(status.confirmed_at)}`}.{" "}
                    {status.backup_codes_remaining} backup code(s) left.
                    {status.last_verified_at &&
                      ` Last used ${fmtDateTime(status.last_verified_at)}.`}
                  </>
                ) : status?.enrolled ? (
                  "A secret has been issued but never confirmed, so it is not protecting anything yet."
                ) : (
                  "This account has no second factor."
                )}
                {status?.locked_out && (
                  <div style={{ color: "var(--red, #f87171)", marginTop: 4 }}>
                    Locked out after repeated failures. Wait for the window to pass.
                  </div>
                )}
              </div>
            </div>
          </Panel>

          {!status?.confirmed && !secret && (
            <Panel title="Turn it on">
              <p style={{ color: "var(--muted)", fontSize: "0.88rem", marginBottom: "0.9rem" }}>
                You will be given a secret to add to an authenticator app, then asked for a code
                to prove it works. Nothing is enforced until that code is accepted.
              </p>
              <button className="btn btn-primary" disabled={busy} onClick={enrol}>
                <KeyRound size={15} style={{ marginRight: 6 }} />
                Start enrolment
              </button>
            </Panel>
          )}

          {secret && (
            <Panel title="Add this to your authenticator">
              <div style={{ display: "grid", gap: "0.9rem" }}>
                <div
                  style={{
                    fontFamily: "ui-monospace, monospace",
                    fontSize: "1.1rem",
                    letterSpacing: "0.08em",
                    padding: "0.7rem 0.9rem",
                    borderRadius: 10,
                    border: "1px solid var(--border)",
                    background: "var(--panel-2)",
                    wordBreak: "break-all",
                  }}
                >
                  {secret}
                </div>
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                  <button
                    className="btn"
                    onClick={() => {
                      navigator.clipboard?.writeText(secret);
                      toast.push("Secret copied.");
                    }}
                  >
                    <Copy size={14} style={{ marginRight: 4 }} />
                    Copy secret
                  </button>
                  {uri && (
                    <button
                      className="btn"
                      onClick={() => {
                        navigator.clipboard?.writeText(uri);
                        toast.push("otpauth:// URI copied.");
                      }}
                    >
                      Copy otpauth URI
                    </button>
                  )}
                </div>
                <Field label="Code from your authenticator">
                  <input
                    className="input"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    inputMode="numeric"
                    placeholder="123456"
                    maxLength={8}
                  />
                </Field>
                <div style={{ display: "flex", justifyContent: "flex-end" }}>
                  <button
                    className="btn btn-primary"
                    disabled={busy || code.trim().length < 6}
                    onClick={confirm}
                  >
                    Confirm
                  </button>
                </div>
              </div>
            </Panel>
          )}

          {backupCodes && (
            <Panel title="Backup codes — shown once">
              <p style={{ color: "var(--muted)", fontSize: "0.88rem", marginBottom: "0.7rem" }}>
                Each works once, and only these are stored — as hashes. If you lose them and lose
                your authenticator, nobody can recover this account for you.
              </p>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(9rem, 1fr))",
                  gap: "0.4rem",
                  fontFamily: "ui-monospace, monospace",
                }}
              >
                {backupCodes.map((c) => (
                  <div
                    key={c}
                    style={{
                      padding: "0.45rem 0.6rem",
                      border: "1px solid var(--border)",
                      borderRadius: 8,
                      textAlign: "center",
                    }}
                  >
                    {c}
                  </div>
                ))}
              </div>
              <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.9rem" }}>
                <button
                  className="btn"
                  onClick={() => {
                    navigator.clipboard?.writeText(backupCodes.join("\n"));
                    toast.push("Codes copied.");
                  }}
                >
                  <Copy size={14} style={{ marginRight: 4 }} />
                  Copy all
                </button>
                <button className="btn" onClick={() => setBackupCodes(null)}>
                  I have saved them
                </button>
              </div>
            </Panel>
          )}

          {status?.confirmed && (
            <Panel title="Manage">
              <Field label="Current code from your authenticator">
                <input
                  className="input"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  inputMode="numeric"
                  placeholder="123456"
                  maxLength={8}
                />
              </Field>
              <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.9rem", flexWrap: "wrap" }}>
                <button className="btn" disabled={busy} onClick={regenerate}>
                  New backup codes
                </button>
                <button className="btn" disabled={busy} onClick={disable}>
                  Turn off
                </button>
              </div>
              <p style={{ fontSize: "0.78rem", color: "var(--faint)", marginTop: "0.7rem" }}>
                Both actions require a working code. A bearer token on its own cannot remove your
                second factor.
              </p>
            </Panel>
          )}
        </>
      )}

      {view === "coverage" &&
        (!coverage ? (
          <Empty label="Coverage is leadership-only. Sign in as a principal to see it." />
        ) : (
          <>
            <div
              style={{
                display: "grid",
                gap: "0.6rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(10rem, 1fr))",
              }}
            >
              <div className="card p-5">
                <span className="label">Coverage</span>
                <div
                  style={{
                    fontSize: "1.9rem",
                    fontWeight: 800,
                    color:
                      coverage.coverage_pct >= 90
                        ? "var(--green, #34d399)"
                        : coverage.coverage_pct >= 50
                          ? "var(--amber, #fbbf24)"
                          : "var(--red, #f87171)",
                  }}
                >
                  {coverage.coverage_pct}%
                </div>
              </div>
              <div className="card p-5">
                <span className="label">Active staff</span>
                <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{coverage.active_staff}</div>
              </div>
              <div className="card p-5">
                <span className="label">With a second factor</span>
                <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{coverage.with_mfa}</div>
              </div>
              <div className="card p-5">
                <span className="label">Without</span>
                <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{coverage.without_mfa}</div>
              </div>
            </div>
            <div className="card p-4" style={{ fontSize: 13, color: "var(--muted)" }}>
              Enrolment here is per-account and voluntary. Making it mandatory is a policy your
              identity provider enforces at sign-in — this number tells you whether that policy is
              working, not whether it exists.
            </div>
          </>
        ))}

      {view === "events" &&
        (events.length === 0 ? (
          <Empty label="No security events recorded, or this view is leadership-only." />
        ) : (
          <Panel pad={false} title="Append-only — entries cannot be edited or deleted">
            {events.slice(0, 60).map((e) => (
              <div
                key={e.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "0.75rem",
                  flexWrap: "wrap",
                  padding: "0.6rem 1.1rem",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <span>
                  <strong>{e.event_type.replace(/_/g, " ")}</strong>
                  <span style={{ color: "var(--muted)", fontSize: "0.83rem" }}>
                    {/* Who did it is the point of the record — never omit it. */}
                    {` · ${e.actor_email || "unattributed"}`}
                    {e.actor_roles && ` (${e.actor_roles})`}
                    {e.detail && ` · ${e.detail}`}
                  </span>
                </span>
                <span style={{ fontSize: "0.78rem", color: "var(--faint)" }}>
                  {e.ip && `${e.ip} · `}
                  {fmtDateTime(e.created_at)}
                </span>
              </div>
            ))}
          </Panel>
        ))}
    </div>
  );
}
