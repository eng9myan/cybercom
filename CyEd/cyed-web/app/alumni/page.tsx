"use client";

import { useCallback, useEffect, useState } from "react";
import { GraduationCap, FileCheck2, AlertTriangle, CheckCircle2 } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { fmtDate } from "@/lib/portal";

/**
 * Leaving, and having left.
 *
 * Exiting a student is the one irreversible thing the office does routinely, so
 * the checks are shown *before* the button and each one says whether it can be
 * overridden. Unpaid fees and unreturned books block an exit; overriding either
 * demands a written reason, because "we let them go owing $800" is a decision
 * someone will be asked about later.
 */

type Check = { check: string; passed: boolean; detail: string; waivable: boolean };

type Student = {
  id: string;
  first_name: string;
  last_name: string;
  year_level: number;
  enrolment_status: string;
};

type AlumniRow = {
  student: string;
  name: string;
  status: string;
  year_level_at_exit: number;
  exit_date: string | null;
  exit_reason: string;
  destination: string;
  email: string;
};

const CHECK_LABELS: Record<string, string> = {
  fees: "Fees",
  library: "Library",
  class_enrolments: "Class enrolments",
};

export default function AlumniPage() {
  const [view, setView] = useState<"alumni" | "exit">("alumni");
  const [rows, setRows] = useState<AlumniRow[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const [chosen, setChosen] = useState("");
  const [checks, setChecks] = useState<Check[] | null>(null);
  const [reason, setReason] = useState("graduated");
  const [destination, setDestination] = useState("");
  const [override, setOverride] = useState("");

  const loadAlumni = useCallback(async () => {
    try {
      const d = await cyed.get<{ results: AlumniRow[] }>("sis/students/alumni/");
      setRows(d.results ?? []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load alumni");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAlumni();
    (async () => {
      try {
        const all = await cyed.list<Student>("sis/students/");
        setStudents(all.filter((s) => s.enrolment_status === "enrolled"));
      } catch {
        // Exiting degrades to unavailable; the alumni list still works.
      }
    })();
  }, [loadAlumni]);

  useEffect(() => {
    setChecks(null);
    setOverride("");
    if (!chosen) return;
    cyed
      .get<Check[] | { checks: Check[] }>(`sis/students/${chosen}/exit-checks/`)
      .then((d) => setChecks(Array.isArray(d) ? d : d.checks ?? []))
      .catch((e) => toast.push(e instanceof Error ? e.message : "Could not run the exit checks"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chosen]);

  const blocking = (checks ?? []).filter((c) => !c.passed && c.waivable);

  const exit = async () => {
    if (!chosen) return;
    if (blocking.length > 0 && !override.trim()) {
      toast.push("Outstanding fees or books block this exit. Give a reason to override.");
      return;
    }
    const student = students.find((s) => s.id === chosen);
    if (!window.confirm(`Exit ${student?.first_name} ${student?.last_name}? This closes their enrolment.`)) {
      return;
    }
    setBusy(true);
    try {
      await cyed.action(`sis/students/${chosen}/exit/`, {
        reason,
        graduated: reason === "graduated",
        destination,
        override_reason: override,
      });
      toast.push("Student exited.");
      setChosen("");
      setChecks(null);
      setDestination("");
      setOverride("");
      setStudents((list) => list.filter((s) => s.id !== chosen));
      await loadAlumni();
      setView("alumni");
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not exit that student");
    } finally {
      setBusy(false);
    }
  };

  const certificate = async (studentId: string, name: string) => {
    setBusy(true);
    try {
      await cyed.action(`sis/students/${studentId}/transfer-certificate/`, {});
      toast.push(`Transfer certificate issued for ${name}.`);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not issue that certificate");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Leavers and alumni"
        subtitle="Exit a student, issue a transfer certificate, keep the record"
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "alumni", label: `Alumni (${rows.length})` },
              { value: "exit", label: "Exit a student" },
            ]}
          />
        }
      />

      {view === "exit" && (
        <>
          <Panel title="Who is leaving">
            <div
              style={{
                display: "grid",
                gap: "0.9rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(12rem, 1fr))",
              }}
            >
              <Field label="Student">
                <select className="input" value={chosen} onChange={(e) => setChosen(e.target.value)}>
                  <option value="">Choose…</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.first_name} {s.last_name} — Year {s.year_level}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Reason">
                <select className="input" value={reason} onChange={(e) => setReason(e.target.value)}>
                  <option value="graduated">Graduated</option>
                  <option value="transferred">Transferred to another school</option>
                  <option value="moved">Family moved</option>
                  <option value="withdrawn">Withdrawn</option>
                </select>
              </Field>
              <Field label="Where they are going">
                <input
                  className="input"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="e.g. Parramatta High School"
                />
              </Field>
            </div>
          </Panel>

          {chosen && checks && (
            <Panel title="Before they go">
              <div style={{ display: "grid", gap: "0.5rem" }}>
                {checks.map((c) => (
                  <div
                    key={c.check}
                    style={{ display: "flex", gap: 10, alignItems: "flex-start" }}
                  >
                    {c.passed ? (
                      <CheckCircle2
                        size={16}
                        style={{ color: "var(--green, #34d399)", flexShrink: 0, marginTop: 2 }}
                      />
                    ) : (
                      <AlertTriangle
                        size={16}
                        style={{ color: "var(--amber, #fbbf24)", flexShrink: 0, marginTop: 2 }}
                      />
                    )}
                    <span>
                      <strong>{CHECK_LABELS[c.check] ?? c.check}</strong>
                      <span style={{ color: "var(--muted)", fontSize: "0.86rem" }}>
                        {" "}— {c.detail}
                      </span>
                      {!c.passed && c.waivable && (
                        <span style={{ color: "var(--faint)", fontSize: "0.8rem" }}>
                          {" "}(blocks the exit unless overridden)
                        </span>
                      )}
                    </span>
                  </div>
                ))}
              </div>

              {blocking.length > 0 && (
                <div style={{ marginTop: "0.9rem" }}>
                  <Field label="Override reason — recorded against the exit">
                    <input
                      className="input"
                      value={override}
                      onChange={(e) => setOverride(e.target.value)}
                      placeholder="e.g. Principal agreed to write off the balance on hardship grounds"
                    />
                  </Field>
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.9rem" }}>
                <button
                  className="btn btn-primary"
                  disabled={busy || (blocking.length > 0 && !override.trim())}
                  onClick={exit}
                >
                  <GraduationCap size={15} style={{ marginRight: 6 }} />
                  Exit student
                </button>
              </div>
            </Panel>
          )}
        </>
      )}

      {view === "alumni" &&
        (rows.length === 0 ? (
          <Empty label="No former students yet." />
        ) : (
          <Panel pad={false}>
            {rows.map((row) => (
              <div
                key={row.student}
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "0.8rem 1.1rem",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <div>
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                    <strong>{row.name}</strong>
                    <Badge value={row.status} />
                  </div>
                  <div style={{ fontSize: "0.83rem", color: "var(--muted)", marginTop: 2 }}>
                    Left {fmtDate(row.exit_date)} from Year {row.year_level_at_exit}
                    {row.exit_reason && ` · ${row.exit_reason}`}
                    {row.destination && ` · to ${row.destination}`}
                  </div>
                </div>
                <button
                  className="btn"
                  disabled={busy}
                  onClick={() => certificate(row.student, row.name)}
                >
                  <FileCheck2 size={14} style={{ marginRight: 4 }} />
                  Transfer certificate
                </button>
              </div>
            ))}
          </Panel>
        ))}
    </div>
  );
}
