"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Bus, CheckCircle2, Users } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { AU_LOCALE } from "@/lib/portal";

/**
 * Excursions.
 *
 * Organised around the question the feature exists to answer: who is allowed on
 * the bus. Readiness is the landing view, students who are *not* cleared are on
 * top, and each one says what is missing so the chase list writes itself.
 *
 * The roll is a separate tab because it is read at a different moment, by a
 * different person, usually on a phone in a car park — and it carries the
 * medical plans in full rather than a link to them.
 */

type Event = {
  id: string;
  name: string;
  event_type: string;
  start_at: string | null;
  location: string;
  cost: string;
  requires_consent: boolean;
  charge_students: boolean;
  permission_deadline: string | null;
  invited_count: number;
  is_excursion: boolean;
};

type ReadinessRow = {
  participation: string;
  student: string;
  name: string;
  year_level: number;
  cleared: boolean;
  fee_waived: boolean;
  missing: string[];
};

type Readiness = {
  invited: number;
  cleared: number;
  not_ready: number;
  permission_deadline: string | null;
  results: ReadinessRow[];
};

type RollStudent = {
  student: string;
  name: string;
  year_level: number;
  emergency_contact: string;
  medical?: {
    condition: string;
    severity: string;
    triggers: string;
    steps: string;
    medication: string;
    medication_location: string;
  };
};

export default function ExcursionsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [selected, setSelected] = useState<Event | null>(null);
  const [view, setView] = useState<"readiness" | "roll">("readiness");
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [roll, setRoll] = useState<{ count: number; with_medical_plans: number; students: RollStudent[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [waiving, setWaiving] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const toast = useToast();

  useEffect(() => {
    (async () => {
      try {
        const rows = await cyed.list<Event>("events/events/");
        const excursions = rows.filter((e) => e.is_excursion);
        setEvents(excursions);
        setSelected((current) => excursions.find((e) => e.id === current?.id) ?? excursions[0] ?? null);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load excursions");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const load = useCallback(async () => {
    if (!selected) return;
    try {
      if (view === "readiness") {
        setReadiness(await cyed.get<Readiness>(`events/events/${selected.id}/readiness/`));
      } else {
        setRoll(await cyed.get(`events/events/${selected.id}/roll/`));
      }
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not load that excursion");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, view]);

  useEffect(() => {
    load();
  }, [load]);

  const waive = async (row: ReadinessRow) => {
    if (!reason.trim()) return;
    setBusy(row.participation);
    try {
      await cyed.action(`events/participations/${row.participation}/waive-fee/`, { reason });
      toast.push("Fee waived — the student is cleared.");
      setWaiving(null);
      setReason("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not waive that fee");
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;
  if (!selected) {
    return (
      <div style={{ display: "grid", gap: "1.25rem" }}>
        <PageHeader title="Excursions" subtitle="Consent, payment and the roll" />
        <Empty label="No excursions yet. Create an event with consent or a cost to see it here." />
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Excursions"
        subtitle={selected.name}
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "readiness", label: "Readiness" },
              { value: "roll", label: "The roll" },
            ]}
          />
        }
      />

      {events.length > 1 && (
        <select
          className="input"
          style={{ maxWidth: 360 }}
          value={selected.id}
          onChange={(e) => setSelected(events.find((x) => x.id === e.target.value) ?? selected)}
        >
          {events.map((e) => (
            <option key={e.id} value={e.id}>
              {e.name}
              {e.start_at ? ` — ${new Date(e.start_at).toLocaleDateString(AU_LOCALE)}` : ""}
            </option>
          ))}
        </select>
      )}

      {view === "readiness" && readiness && (
        <>
          <div
            style={{
              display: "grid",
              gap: "0.6rem",
              gridTemplateColumns: "repeat(auto-fit, minmax(9rem, 1fr))",
            }}
          >
            <Count label="Not ready" value={readiness.not_ready} tone={readiness.not_ready ? "bad" : "ok"} />
            <Count label="Cleared" value={readiness.cleared} tone="ok" />
            <Count label="Invited" value={readiness.invited} />
          </div>

          {readiness.permission_deadline && (
            <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
              Permissions due {new Date(readiness.permission_deadline).toLocaleDateString(AU_LOCALE)}.
            </p>
          )}

          {readiness.results.length === 0 ? (
            <Empty label="Nobody has been invited yet." />
          ) : (
            <Panel pad={false}>
              {readiness.results.map((row) => (
                <div
                  key={row.participation}
                  style={{ padding: "0.9rem 1.1rem", borderBottom: "1px solid var(--border)" }}
                >
                  <div
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: "0.75rem",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        {row.cleared ? (
                          <CheckCircle2 size={16} style={{ color: "var(--green, #34d399)" }} />
                        ) : (
                          <AlertTriangle size={16} style={{ color: "var(--amber, #fbbf24)" }} />
                        )}
                        <strong>{row.name}</strong>
                        <span className="pill" style={{ fontSize: "0.72rem" }}>
                          Year {row.year_level}
                        </span>
                        {row.fee_waived && <Badge value="fee waived" />}
                      </div>
                      {!row.cleared && (
                        <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: 2 }}>
                          Waiting on: {row.missing.join(", ")}
                        </div>
                      )}
                    </div>

                    {!row.cleared && row.missing.includes("fee unpaid") && (
                      <button
                        className="btn"
                        disabled={busy !== null}
                        onClick={() => {
                          setWaiving(waiving === row.participation ? null : row.participation);
                          setReason("");
                        }}
                      >
                        Waive fee
                      </button>
                    )}
                  </div>

                  {waiving === row.participation && (
                    <div style={{ marginTop: "0.7rem", display: "grid", gap: "0.5rem" }}>
                      <input
                        className="input"
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        placeholder="Why is the fee being waived? This is recorded."
                      />
                      <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                        <button className="btn" onClick={() => setWaiving(null)}>
                          Cancel
                        </button>
                        <button
                          className="btn btn-primary"
                          disabled={!reason.trim() || busy !== null}
                          onClick={() => waive(row)}
                        >
                          Waive
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </Panel>
          )}
        </>
      )}

      {view === "roll" && roll && (
        <>
          <Panel>
            <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
              <div>
                <span className="label">On the bus</span>
                <div style={{ fontSize: "1.75rem", fontWeight: 800 }}>{roll.count}</div>
              </div>
              <div>
                <span className="label">Medical plans</span>
                <div
                  style={{
                    fontSize: "1.75rem",
                    fontWeight: 800,
                    color: roll.with_medical_plans ? "var(--amber, #fbbf24)" : undefined,
                  }}
                >
                  {roll.with_medical_plans}
                </div>
              </div>
            </div>
          </Panel>

          {roll.count === 0 ? (
            <Empty label="Nobody is cleared yet, so the roll is empty. Check the Readiness tab." />
          ) : (
            roll.students.map((student) => (
              <Panel
                key={student.student}
                title={
                  <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    {student.medical && (
                      <AlertTriangle size={16} style={{ color: "var(--red, #f87171)" }} />
                    )}
                    <strong style={{ fontSize: "1rem" }}>{student.name}</strong>
                    <span className="pill" style={{ fontSize: "0.72rem" }}>
                      Year {student.year_level}
                    </span>
                  </span>
                }
              >
                {student.emergency_contact && (
                  <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                    Emergency contact: {student.emergency_contact}
                  </div>
                )}
                {student.medical && (
                  <div
                    style={{
                      marginTop: "0.6rem",
                      background: "var(--panel-2)",
                      border: "1px solid var(--border)",
                      borderRadius: 12,
                      padding: "0.8rem 1rem",
                    }}
                  >
                    <div className="label" style={{ marginBottom: 4 }}>
                      {student.medical.condition}
                      {student.medical.triggers && ` — ${student.medical.triggers}`}
                    </div>
                    <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
                      {student.medical.steps}
                    </div>
                    {student.medical.medication && (
                      <div style={{ marginTop: 6, fontSize: "0.88rem" }}>
                        <strong>{student.medical.medication}</strong>
                        {student.medical.medication_location &&
                          ` — ${student.medical.medication_location}`}
                      </div>
                    )}
                  </div>
                )}
              </Panel>
            ))
          )}
        </>
      )}
    </div>
  );
}

function Count({ label, value, tone }: { label: string; value: number; tone?: "ok" | "bad" }) {
  const colour =
    tone === "bad" ? "var(--red, #f87171)" : tone === "ok" ? "var(--green, #34d399)" : undefined;
  return (
    <div className="card p-5" style={{ display: "grid", gap: "0.2rem" }}>
      <span className="label">{label}</span>
      <strong style={{ fontSize: "1.9rem", color: colour }}>{value}</strong>
    </div>
  );
}
