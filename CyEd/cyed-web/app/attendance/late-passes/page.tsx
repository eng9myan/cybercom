"use client";

import { useEffect, useMemo, useState } from "react";
import { Printer, Search, UserCheck } from "lucide-react";
import { cyed, cyedUrl } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { clock } from "@/lib/portal";
import type { ClassSection, LatePass, Student } from "@/lib/types";

const REASONS: { value: string; label: string }[] = [
  { value: "transport", label: "Transport / traffic" },
  { value: "medical", label: "Medical appointment" },
  { value: "family", label: "Family reason" },
  { value: "overslept", label: "Overslept" },
  { value: "other", label: "Other" },
];

function nowHHMM() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/**
 * Front-office kiosk: issue a printed slip when a student signs in late.
 *
 * Deliberately does not touch the roll-call/attendance-mark screens — a
 * student at reception hasn't walked into a specific in-progress roll a
 * clerk has context for. See LatePass's own docstring in the backend.
 */
export default function LatePassesPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [sections, setSections] = useState<ClassSection[]>([]);
  const [todaysPasses, setTodaysPasses] = useState<LatePass[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const [query, setQuery] = useState("");
  const [studentId, setStudentId] = useState("");
  const [time, setTime] = useState(nowHHMM());
  const [reason, setReason] = useState("transport");
  const [detail, setDetail] = useState("");
  const [classSection, setClassSection] = useState("");
  const [issuing, setIssuing] = useState(false);
  const [lastIssued, setLastIssued] = useState<LatePass | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [studentRows, sectionRows, passRows] = await Promise.all([
        cyed.list<Student>("sis/students/"),
        cyed.list<ClassSection>("sis/class-sections/"),
        cyed.list<LatePass>(`attendance/late-passes/?date=${new Date().toISOString().slice(0, 10)}`),
      ]);
      setStudents(studentRows);
      setSections(sectionRows);
      setTodaysPasses(passRows);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return students
      .filter((s) => `${s.first_name} ${s.last_name}`.toLowerCase().includes(q))
      .slice(0, 8);
  }, [query, students]);

  const selectedStudent = students.find((s) => s.id === studentId) || null;

  const issue = async () => {
    if (!studentId) {
      toast.push("Search for and select the student first", "bad");
      return;
    }
    setIssuing(true);
    try {
      const created = await cyed.create<LatePass>("attendance/late-passes/", {
        student: studentId,
        arrival_time: `${time}:00`,
        reason,
        reason_detail: detail,
        class_section: classSection || null,
      });
      toast.push(`Late pass issued for ${created.student_name}`);
      setLastIssued(created);
      setStudentId("");
      setQuery("");
      setDetail("");
      setClassSection("");
      setTime(nowHHMM());
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not issue the pass", "bad");
    } finally {
      setIssuing(false);
    }
  };

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Late Passes" subtitle="Front-office kiosk — sign in a late-arriving student and print their pass" />

      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 20, alignItems: "start" }}>
        <Panel title={<div className="flex items-center gap-2"><UserCheck size={15} /><span className="label">Sign a student in</span></div>}>
          <div className="space-y-3">
            <Field label="Find student">
              <div style={{ position: "relative" }}>
                <input
                  className="input"
                  value={selectedStudent ? `${selectedStudent.first_name} ${selectedStudent.last_name}` : query}
                  onChange={(e) => { setQuery(e.target.value); setStudentId(""); }}
                  placeholder="Type a name…"
                />
                {!studentId && matches.length > 0 && (
                  <div
                    style={{
                      position: "absolute", top: "100%", left: 0, right: 0, zIndex: 10,
                      background: "var(--card, #fff)", border: "1px solid var(--border)",
                      borderRadius: 8, marginTop: 4, maxHeight: 220, overflowY: "auto",
                    }}
                  >
                    {matches.map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => { setStudentId(s.id); setQuery(""); }}
                        style={{
                          display: "block", width: "100%", textAlign: "left", padding: "0.5rem 0.75rem",
                          background: "transparent", border: "none", cursor: "pointer", fontSize: 13,
                        }}
                      >
                        {s.first_name} {s.last_name} <span style={{ color: "var(--muted)" }}>· Y{s.year_level}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </Field>

            <Field label="Arrival time">
              <input className="input" type="time" value={time} onChange={(e) => setTime(e.target.value)} />
            </Field>

            <Field label="Reason">
              <select className="input" value={reason} onChange={(e) => setReason(e.target.value)}>
                {REASONS.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </Field>

            <Field label="Notes (optional)">
              <input className="input" value={detail} onChange={(e) => setDetail(e.target.value)} />
            </Field>

            <Field label="Heading to (optional)">
              <select className="input" value={classSection} onChange={(e) => setClassSection(e.target.value)}>
                <option value="">—</option>
                {sections.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </Field>

            <button
              className="btn btn-primary"
              style={{ width: "100%", justifyContent: "center" }}
              disabled={issuing || !studentId}
              onClick={issue}
            >
              {issuing ? "Issuing…" : "Issue pass"}
            </button>

            {lastIssued && (
              <a
                href={cyedUrl(`attendance/late-passes/${lastIssued.id}/print_view/`)}
                target="_blank"
                rel="noreferrer"
                className="btn"
                style={{ width: "100%", justifyContent: "center" }}
              >
                <Printer size={14} /> Print {lastIssued.pass_number}
              </a>
            )}
          </div>
        </Panel>

        <Panel title="Today's late arrivals">
          {loading ? (
            <SkeletonRows rows={5} />
          ) : error ? (
            <ErrorNote error={error} />
          ) : todaysPasses.length === 0 ? (
            <Empty label="No late passes issued today." />
          ) : (
            todaysPasses.map((p) => (
              <div
                key={p.id}
                style={{
                  display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "center",
                  justifyContent: "space-between", padding: "0.6rem 0", borderBottom: "1px solid var(--border)",
                }}
              >
                <div>
                  <div style={{ fontWeight: 650 }}>{p.student_name}</div>
                  <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                    {clock(p.arrival_time)} · {p.reason_display}
                    {p.class_section_name ? ` · ${p.class_section_name}` : ""}
                  </div>
                </div>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  <Badge value={p.printed_at ? "printed" : "not printed"} />
                  <a
                    href={cyedUrl(`attendance/late-passes/${p.id}/print_view/`)}
                    target="_blank"
                    rel="noreferrer"
                    className="btn"
                  >
                    <Search size={13} />
                  </a>
                </div>
              </div>
            ))
          )}
        </Panel>
      </div>
    </div>
  );
}
