"use client";

import { useEffect, useState } from "react";
import { cyed, cyedUrl } from "@/lib/cyed";
import { PageHeader, Loading, ErrorNote, Empty, Field } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { Student, ReportCard, ReportCardDocument } from "@/lib/types";

type Entry = {
  id: string;
  subject: string;
  achievement: string;
  effort: string;
  comment?: string;
};

const ACH = ["A", "B", "C", "D", "E"];
const EFF = ["high", "consistent", "developing", "low"];

export default function ReportsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [studentId, setStudentId] = useState("");
  const [cards, setCards] = useState<ReportCard[]>([]);
  const [selected, setSelected] = useState<ReportCard | null>(null);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [doc, setDoc] = useState<ReportCardDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [term, setTerm] = useState("Semester 1");
  const [eSubject, setESubject] = useState("Mathematics");
  const [eAch, setEAch] = useState("B");
  const [eEff, setEEff] = useState("high");
  const [eComment, setEComment] = useState("");
  const toast = useToast();

  useEffect(() => {
    (async () => {
      try {
        const studs = await cyed.list<Student>("sis/students/");
        setStudents(studs);
        if (studs.length) setStudentId(studs[0].id);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load students");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const loadCards = async (sid: string) => {
    if (!sid) return;
    try {
      setCards(await cyed.list<ReportCard>(`reporting/report-cards/?student=${sid}`));
      setSelected(null);
      setDoc(null);
      setEntries([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load report cards");
    }
  };

  useEffect(() => {
    loadCards(studentId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studentId]);

  const openCard = async (c: ReportCard) => {
    setSelected(c);
    setDoc(null);
    try {
      setEntries(await cyed.list<Entry>(`reporting/entries/?report_card=${c.id}`));
      if (c.status === "published") {
        try {
          setDoc(await cyed.get<ReportCardDocument>(`reporting/report-cards/${c.id}/document/`));
        } catch {
          /* no doc */
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load entries");
    }
  };

  const createCard = async () => {
    if (!studentId) return;
    try {
      await cyed.create("reporting/report-cards/", { student: studentId, term });
      toast.push(`Report card created for ${term}`);
      await loadCards(studentId);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Failed to create report card", "bad");
    }
  };

  const addEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || !eSubject) return;
    try {
      await cyed.create("reporting/entries/", {
        report_card: selected.id, subject: eSubject, achievement: eAch, effort: eEff, comment: eComment,
      });
      setEComment("");
      await openCard(selected);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add entry");
    }
  };

  const publish = async () => {
    if (!selected) return;
    try {
      await cyed.action(`reporting/report-cards/${selected.id}/publish/`);
      await loadCards(studentId);
      const refreshed = { ...selected, status: "published" };
      setSelected(refreshed);
      setDoc(await cyed.get<ReportCardDocument>(`reporting/report-cards/${selected.id}/document/`));
      toast.push("Report card published — tamper-evident PDF sealed");
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Publish failed", "bad");
    }
  };

  const acknowledge = async () => {
    if (!selected) return;
    try {
      setDoc(await cyed.action<ReportCardDocument>(`reporting/report-cards/${selected.id}/acknowledge/`));
      toast.push("Receipt acknowledged");
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Acknowledge failed", "bad");
    }
  };

  if (loading) return <Loading label="Loading reports…" />;

  return (
    <div>
      <PageHeader title="Report Cards" subtitle="Build, publish, and view tamper-evident report cards" />
      {error && <ErrorNote error={error} />}

      <div style={{ display: "flex", gap: 12, alignItems: "end", marginBottom: 16 }}>
        <div style={{ width: 280 }}>
          <Field label="Student">
            <select className="input" value={studentId} onChange={(e) => setStudentId(e.target.value)}>
              {students.map((s) => (
                <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>
              ))}
            </select>
          </Field>
        </div>
        <div style={{ width: 160 }}>
          <Field label="New report — term">
            <input className="input" value={term} onChange={(e) => setTerm(e.target.value)} />
          </Field>
        </div>
        <button className="btn btn-ghost" onClick={createCard} disabled={!studentId}>Create report card</button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 20, alignItems: "start" }}>
        <div className="card p-2">
          {cards.length === 0 ? <Empty label="No report cards yet." /> : (
            <table>
              <thead><tr><th>Term</th><th>Status</th></tr></thead>
              <tbody>
                {cards.map((c) => (
                  <tr key={c.id} onClick={() => openCard(c)} style={{ cursor: "pointer",
                    boxShadow: selected?.id === c.id ? "inset 3px 0 0 var(--cyan)" : undefined,
                    background: selected?.id === c.id ? "var(--panel-2)" : "transparent" }}>
                    <td>{c.term}</td>
                    <td><Badge value={c.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div>
          {!selected ? (
            <Empty label="Select a report card." />
          ) : (
            <div className="space-y-4">
              <div className="card p-4">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div className="font-semibold flex items-center gap-2">{selected.term} <Badge value={selected.status} /></div>
                  <div style={{ display: "flex", gap: 8 }}>
                    {selected.status !== "published" && (
                      <button className="btn btn-primary" onClick={publish}>Publish</button>
                    )}
                    {selected.status === "published" && (
                      <a className="btn btn-ghost" href={cyedUrl(`reporting/report-cards/${selected.id}/pdf/`)} target="_blank" rel="noreferrer">Open PDF</a>
                    )}
                  </div>
                </div>
                <table style={{ marginTop: 10 }}>
                  <thead><tr><th>Subject</th><th>Achievement</th><th>Effort</th><th>Comment</th></tr></thead>
                  <tbody>
                    {entries.map((en) => (
                      <tr key={en.id}>
                        <td>{en.subject}</td>
                        <td><span className="pill">{en.achievement || "—"}</span></td>
                        <td style={{ color: "var(--muted)" }}>{en.effort || "—"}</td>
                        <td style={{ color: "var(--muted)" }}>{en.comment || "—"}</td>
                      </tr>
                    ))}
                    {entries.length === 0 && <tr><td colSpan={4} style={{ color: "var(--muted)" }}>No subjects yet.</td></tr>}
                  </tbody>
                </table>

                {selected.status !== "published" && (
                  <form onSubmit={addEntry} style={{ display: "flex", gap: 8, alignItems: "end", marginTop: 12, flexWrap: "wrap" }}>
                    <div style={{ width: 150 }}><Field label="Subject"><input className="input" value={eSubject} onChange={(e) => setESubject(e.target.value)} /></Field></div>
                    <div style={{ width: 90 }}><Field label="Grade"><select className="input" value={eAch} onChange={(e) => setEAch(e.target.value)}>{ACH.map((a) => <option key={a}>{a}</option>)}</select></Field></div>
                    <div style={{ width: 120 }}><Field label="Effort"><select className="input" value={eEff} onChange={(e) => setEEff(e.target.value)}>{EFF.map((a) => <option key={a}>{a}</option>)}</select></Field></div>
                    <div style={{ flex: 1, minWidth: 160 }}><Field label="Comment"><input className="input" value={eComment} onChange={(e) => setEComment(e.target.value)} /></Field></div>
                    <button className="btn btn-primary" type="submit">Add subject</button>
                  </form>
                )}
              </div>

              {selected.status === "published" && (
                <div className="card p-4 space-y-3">
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    {doc && <span className={`status ${doc.verified ? "status-ok" : "status-bad"}`}>{doc.verified ? "Verified · untampered" : "TAMPERED"}</span>}
                    {doc && <span className="pill">v{doc.version}</span>}
                    {doc?.acknowledged_by
                      ? <span className="status status-ok">Acknowledged</span>
                      : <button className="btn btn-ghost" onClick={acknowledge}>Acknowledge receipt</button>}
                  </div>
                  {doc && <div className="text-xs" style={{ color: "var(--muted)", wordBreak: "break-all" }}>SHA-256: {doc.content_hash}</div>}
                  <iframe
                    title="Report card PDF"
                    src={cyedUrl(`reporting/report-cards/${selected.id}/pdf/`)}
                    style={{ width: "100%", height: 620, border: "1px solid var(--border)", borderRadius: 10, background: "#fff" }}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
