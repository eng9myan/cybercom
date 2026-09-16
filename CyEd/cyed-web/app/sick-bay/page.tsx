"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, HeartPulse, Phone } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { AU_LOCALE } from "@/lib/portal";

/**
 * The sick bay.
 *
 * Two jobs, and the screen opens on the one that is live: who is here right
 * now, and how long they have been. A first-aid officer is interrupted
 * constantly, so the current list is the landing state and admitting someone
 * is one form away rather than the other way round.
 *
 * Closing a visit is where the parent alert happens. The outcome buttons say
 * what they will do — "Send home (alerts guardians)" — because a person
 * choosing an outcome should know a message goes out before they click, not
 * after.
 */

type Visit = {
  visit: string;
  student: string;
  name: string;
  year_level: number;
  arrived_at: string;
  minutes_present: number;
  complaint: string;
  referred_by: string;
  guardians_notified: number;
  has_action_plan: boolean;
};

type DayRow = {
  visit: string;
  name: string;
  arrived_at: string;
  departed_at: string | null;
  minutes_present: number;
  complaint: string;
  outcome: string;
  collected_by: string;
  guardians_notified: number;
};

type Student = { id: string; first_name: string; last_name: string; year_level: number };

const clock = (iso: string) =>
  new Date(iso).toLocaleTimeString(AU_LOCALE, { hour: "numeric", minute: "2-digit" });

export default function SickBayPage() {
  const [view, setView] = useState<"current" | "day">("current");
  const [current, setCurrent] = useState<Visit[]>([]);
  const [day, setDay] = useState<{ count: number; by_outcome: Record<string, number>; results: DayRow[] } | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const toast = useToast();

  const [studentId, setStudentId] = useState("");
  const [complaint, setComplaint] = useState("");
  const [closing, setClosing] = useState<Visit | null>(null);
  const [collectedBy, setCollectedBy] = useState("");
  const [treatment, setTreatment] = useState("");

  const load = useCallback(async () => {
    try {
      if (view === "current") {
        const data = await cyed.get<{ results: Visit[] }>("health/sick-bay/current/");
        setCurrent(data.results ?? []);
      } else {
        setDay(await cyed.get("health/sick-bay/day/"));
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load the sick bay");
    } finally {
      setLoading(false);
    }
  }, [view]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    (async () => {
      try {
        setStudents(await cyed.list<Student>("sis/students/"));
      } catch {
        // The admit form degrades to unusable rather than breaking the page.
      }
    })();
  }, []);

  const admit = async () => {
    if (!studentId) return;
    setBusy("admit");
    try {
      await cyed.create("health/sick-bay/", { student: studentId, complaint });
      toast.push("Admitted.");
      setComplaint("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not admit that student");
    } finally {
      setBusy(null);
    }
  };

  const close = async (visit: Visit, outcome: string) => {
    // "Send home" needs a named collector; ask before sending rather than
    // bouncing the request back with an error.
    if (outcome === "sent_home" && !collectedBy.trim()) {
      setClosing(visit);
      return;
    }
    setBusy(visit.visit);
    try {
      const resp = await cyed.action<{ guardians_notified: number }>(
        `health/sick-bay/${visit.visit}/close/`,
        { outcome, collected_by: collectedBy, treatment },
      );
      toast.push(
        resp.guardians_notified
          ? `Closed — ${resp.guardians_notified} guardian(s) messaged.`
          : "Closed.",
      );
      setClosing(null);
      setCollectedBy("");
      setTreatment("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not close that visit");
    } finally {
      setBusy(null);
    }
  };

  const warn = async (visit: Visit) => {
    setBusy(visit.visit);
    try {
      const resp = await cyed.action<{ notified: number }>(
        `health/sick-bay/${visit.visit}/notify-guardians/`,
      );
      toast.push(`${resp.notified} guardian(s) messaged.`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not message the guardians");
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Sick bay"
        subtitle="Who is here, and what happened today"
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "current", label: "Here now" },
              { value: "day", label: "Today" },
            ]}
          />
        }
      />

      {view === "current" && (
        <>
          {current.length === 0 ? (
            <Empty label="Nobody is in the sick bay." />
          ) : (
            <Panel pad={false}>
              {current.map((visit) => (
                <div
                  key={visit.visit}
                  style={{
                    padding: "1rem 1.1rem",
                    borderBottom: "1px solid var(--border)",
                    background: visit.has_action_plan
                      ? "color-mix(in srgb, var(--amber, #fbbf24) 10%, transparent)"
                      : undefined,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: "0.75rem",
                      alignItems: "flex-start",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        {visit.has_action_plan && (
                          <AlertTriangle size={16} style={{ color: "var(--amber, #fbbf24)" }} />
                        )}
                        <strong>{visit.name}</strong>
                        <span className="pill" style={{ fontSize: "0.72rem" }}>
                          Year {visit.year_level}
                        </span>
                        {visit.guardians_notified > 0 && <Badge value="family told" />}
                      </div>
                      <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: 2 }}>
                        In since {clock(visit.arrived_at)} · {visit.minutes_present} min
                        {visit.referred_by && ` · sent by ${visit.referred_by}`}
                      </div>
                      {visit.complaint && (
                        <div style={{ fontSize: "0.88rem", marginTop: 4 }}>{visit.complaint}</div>
                      )}
                      {visit.has_action_plan && (
                        <div
                          style={{
                            fontSize: "0.82rem",
                            color: "var(--amber, #fbbf24)",
                            marginTop: 4,
                          }}
                        >
                          This student has a medical action plan — check it before treating.
                        </div>
                      )}
                    </div>

                    <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                      <button
                        className="btn"
                        disabled={busy !== null}
                        onClick={() => warn(visit)}
                        title="Tell the family now, without closing the visit"
                      >
                        <Phone size={14} style={{ marginRight: 4 }} />
                        Warn family
                      </button>
                      <button
                        className="btn"
                        disabled={busy !== null}
                        onClick={() => close(visit, "returned_to_class")}
                      >
                        Back to class
                      </button>
                      <button
                        className="btn btn-primary"
                        disabled={busy !== null}
                        onClick={() => close(visit, "sent_home")}
                      >
                        Send home (alerts family)
                      </button>
                    </div>
                  </div>

                  {closing?.visit === visit.visit && (
                    <div style={{ marginTop: "0.8rem", display: "grid", gap: "0.6rem" }}>
                      <Field label="Who is collecting them">
                        <input
                          className="input"
                          value={collectedBy}
                          onChange={(e) => setCollectedBy(e.target.value)}
                          placeholder="e.g. Hoa Tran (mother)"
                        />
                      </Field>
                      <Field label="Treatment given (optional)">
                        <input
                          className="input"
                          value={treatment}
                          onChange={(e) => setTreatment(e.target.value)}
                        />
                      </Field>
                      <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                        <button className="btn" onClick={() => setClosing(null)}>
                          Cancel
                        </button>
                        <button
                          className="btn btn-primary"
                          disabled={!collectedBy.trim() || busy !== null}
                          onClick={() => close(visit, "sent_home")}
                        >
                          Send home and alert family
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </Panel>
          )}

          <Panel title="Admit a student">
            <div
              style={{
                display: "grid",
                gap: "0.9rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(13rem, 1fr))",
                alignItems: "end",
              }}
            >
              <Field label="Student">
                <select
                  className="input"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                >
                  <option value="">Choose…</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.first_name} {s.last_name} — Year {s.year_level}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="What is wrong">
                <input
                  className="input"
                  value={complaint}
                  onChange={(e) => setComplaint(e.target.value)}
                  placeholder="e.g. Headache, feels hot"
                />
              </Field>
              <button
                className="btn btn-primary"
                disabled={!studentId || busy !== null}
                onClick={admit}
              >
                <HeartPulse size={15} style={{ marginRight: 6 }} />
                Admit
              </button>
            </div>
          </Panel>
        </>
      )}

      {view === "day" && day && (
        <>
          <Panel>
            <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
              <div>
                <span className="label">Visits today</span>
                <div style={{ fontSize: "1.75rem", fontWeight: 800 }}>{day.count}</div>
              </div>
              {Object.entries(day.by_outcome).map(([outcome, count]) => (
                <div key={outcome}>
                  <span className="label">{outcome.replace(/_/g, " ")}</span>
                  <div style={{ fontSize: "1.75rem", fontWeight: 800 }}>{count}</div>
                </div>
              ))}
            </div>
          </Panel>

          {day.results.length === 0 ? (
            <Empty label="No visits recorded today." />
          ) : (
            <Panel pad={false}>
              {day.results.map((row) => (
                <div
                  key={row.visit}
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "0.75rem",
                    justifyContent: "space-between",
                    padding: "0.85rem 1.1rem",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <div>
                    <strong>{row.name}</strong>
                    <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                      {clock(row.arrived_at)}
                      {row.departed_at && ` – ${clock(row.departed_at)}`} ·{" "}
                      {row.minutes_present} min
                      {row.complaint && ` · ${row.complaint}`}
                      {row.collected_by && ` · collected by ${row.collected_by}`}
                    </div>
                  </div>
                  <Badge value={row.outcome} />
                </div>
              ))}
            </Panel>
          )}
        </>
      )}
    </div>
  );
}
