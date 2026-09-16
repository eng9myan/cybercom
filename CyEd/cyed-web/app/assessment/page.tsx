"use client";

import { useEffect, useMemo, useState } from "react";
import { ClipboardList, Clock, CheckCircle2, AlertTriangle } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Loading, Field, SkeletonRows } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge, Segmented, Modal } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { AU_LOCALE } from "@/lib/portal";

type MineRow = {
  student: string;
  assignment: string;
  title: string;
  due_at: string | null;
  is_overdue: boolean;
  allow_late: boolean;
  max_score: string;
  curriculum_code?: string;
  status: string;
  submission: string | null;
  score: string | null;
};

type Assignment = {
  id: string;
  title: string;
  due_at?: string | null;
  max_score?: string;
  is_published?: boolean;
  curriculum_code?: string;
  class_section?: string;
};

type SubmissionRow = {
  id: string;
  student: string;
  student_name?: string;
  status: string;
  score?: string | null;
  submitted_at?: string | null;
  text_response?: string;
};

type View = "mine" | "teach";

export default function AssessmentPage() {
  const [view, setView] = useState<View>("mine");
  return (
    <div>
      <PageHeader
        title="Assessment"
        subtitle="Assignments, submissions and auto-marked quizzes. Marks flow through to the gradebook."
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "mine", label: "My work" },
              { value: "teach", label: "Teaching" },
            ]}
          />
        }
      />
      {view === "mine" ? <MyWork onSwitchToTeaching={() => setView("teach")} /> : <Teaching />}
    </div>
  );
}

/* ── Student / parent view ─────────────────────────────────────────────── */
function MyWork({ onSwitchToTeaching }: { onSwitchToTeaching: () => void }) {
  const [rows, setRows] = useState<MineRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // "My work" is a learner/parent view. A staff account has no work of its own,
  // and the API says so with a 400 — show them the way across rather than an error.
  const [staffOnly, setStaffOnly] = useState(false);
  const [openFor, setOpenFor] = useState<MineRow | null>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const data = await cyed.get<{ results: MineRow[] }>("assessment/assignments/mine/");
      setRows(data.results || []);
      setError(null);
      setStaffOnly(false);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to load your assignments";
      if (msg.includes("Staff must pass")) {
        setStaffOnly(true);
        setError(null);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const stats = useMemo(() => {
    const outstanding = rows.filter((r) => r.status === "outstanding").length;
    const overdue = rows.filter((r) => r.status === "outstanding" && r.is_overdue).length;
    const graded = rows.filter((r) => r.status === "graded").length;
    return { total: rows.length, outstanding, overdue, graded };
  }, [rows]);

  const hand_in = async () => {
    if (!openFor) return;
    setBusy(true);
    try {
      // A submission row must exist before it can be handed in.
      let submissionId = openFor.submission;
      if (!submissionId) {
        const created = await cyed.create<{ id: string }>("assessment/submissions/", {
          assignment: openFor.assignment,
          student: openFor.student,
          text_response: text,
        });
        submissionId = created.id;
      }
      await cyed.action(`assessment/submissions/${submissionId}/submit/`, { text_response: text });
      toast.push(`“${openFor.title}” handed in`);
      setOpenFor(null);
      setText("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not hand in", "bad");
    } finally {
      setBusy(false);
    }
  };

  const columns: Column<MineRow & { id: string }>[] = [
    { key: "title", header: "Assignment", render: (r) => <span style={{ fontWeight: 600 }}>{r.title}</span> },
    {
      key: "due",
      header: "Due",
      width: 160,
      render: (r) => (
        <span style={{ color: r.is_overdue && r.status === "outstanding" ? "var(--bad)" : "var(--muted)" }}>
          {r.due_at ? new Date(r.due_at).toLocaleDateString(AU_LOCALE) : "—"}
        </span>
      ),
    },
    { key: "acara", header: "ACARA", width: 120, render: (r) => (r.curriculum_code ? <span className="pill grad-text" style={{ fontWeight: 700 }}>{r.curriculum_code}</span> : "—") },
    { key: "status", header: "Status", width: 140, render: (r) => <Badge value={r.status} /> },
    {
      key: "score",
      header: "Mark",
      width: 100,
      align: "right",
      render: (r) => (r.score != null ? `${r.score} / ${r.max_score}` : <span style={{ color: "var(--faint)" }}>—</span>),
    },
    {
      key: "action",
      header: "",
      align: "right",
      render: (r) =>
        r.status === "outstanding" ? (
          <button
            className="btn btn-primary"
            disabled={r.is_overdue && !r.allow_late}
            title={r.is_overdue && !r.allow_late ? "Past the deadline — late submissions are not accepted" : undefined}
            onClick={() => {
              setOpenFor(r);
              setText("");
            }}
          >
            Hand in
          </button>
        ) : null,
    },
  ];

  if (loading) return <Loading label="Loading your assignments…" />;
  if (error) return <ErrorNote error={error} />;
  if (staffOnly) {
    return (
      <Panel title="My work">
        <div style={{ fontSize: 13, color: "var(--muted)", maxWidth: 520 }}>
          You&rsquo;re signed in as staff, so there is no student work of your own here. Use{" "}
          <strong>Teaching</strong> to see who has handed in and to mark submissions.
        </div>
        <button className="btn btn-primary mt-4" onClick={onSwitchToTeaching}>
          Go to Teaching →
        </button>
      </Panel>
    );
  }

  return (
    <div>
      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Assignments" value={stats.total} accent="cyan" icon={<ClipboardList size={17} />} />
        <StatCard label="Outstanding" value={stats.outstanding} accent="blue" icon={<Clock size={17} />} />
        <StatCard label="Overdue" value={stats.overdue} accent="violet" icon={<AlertTriangle size={17} />} />
        <StatCard label="Marked" value={stats.graded} accent="cyan" icon={<CheckCircle2 size={17} />} />
      </div>

      <DataTable
        columns={columns}
        rows={rows.map((r) => ({ ...r, id: r.assignment }))}
        filterKeys={["title"]}
        emptyLabel="Nothing assigned yet."
      />

      <Modal open={!!openFor} onClose={() => setOpenFor(null)} title={openFor?.title || "Hand in"}>
        <div className="space-y-3">
          {openFor?.is_overdue && (
            <div className="status status-warn">past the due date — this will be marked late</div>
          )}
          <Field label="Your response">
            <textarea className="input" rows={7} value={text} onChange={(e) => setText(e.target.value)} autoFocus />
          </Field>
          <div className="flex justify-end gap-2">
            <button className="btn btn-ghost" onClick={() => setOpenFor(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={hand_in} disabled={busy || !text.trim()}>
              {busy ? "Handing in…" : "Hand in"}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

/* ── Teacher view ──────────────────────────────────────────────────────── */
function Teaching() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [selected, setSelected] = useState<Assignment | null>(null);
  const [subs, setSubs] = useState<SubmissionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [gradeFor, setGradeFor] = useState<SubmissionRow | null>(null);
  const [score, setScore] = useState("");
  const [feedback, setFeedback] = useState("");
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      setAssignments(await cyed.list<Assignment>("assessment/assignments/"));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load assignments");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const open = async (a: Assignment) => {
    setSelected(a);
    try {
      const data = await cyed.get<{ results?: SubmissionRow[] } | SubmissionRow[]>(
        `assessment/assignments/${a.id}/submissions/`
      );
      setSubs(Array.isArray(data) ? data : data.results || []);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not load submissions", "bad");
    }
  };

  const grade = async () => {
    if (!gradeFor) return;
    try {
      await cyed.action(`assessment/submissions/${gradeFor.id}/grade/`, {
        score: Number(score),
        feedback,
      });
      toast.push("Marked — written through to the gradebook");
      setGradeFor(null);
      setScore("");
      setFeedback("");
      if (selected) await open(selected);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not mark", "bad");
    }
  };

  if (loading) return <Loading label="Loading assignments…" />;
  if (error) return <ErrorNote error={error} />;

  const subCols: Column<SubmissionRow>[] = [
    { key: "student", header: "Student", render: (s) => <span style={{ fontWeight: 600 }}>{s.student_name || s.student}</span> },
    { key: "status", header: "Status", width: 130, render: (s) => <Badge value={s.status} /> },
    {
      key: "submitted",
      header: "Handed in",
      width: 150,
      render: (s) => <span style={{ color: "var(--muted)" }}>{s.submitted_at ? new Date(s.submitted_at).toLocaleString(AU_LOCALE) : "—"}</span>,
    },
    { key: "score", header: "Mark", width: 90, align: "right", render: (s) => (s.score ?? "—") },
    {
      key: "action",
      header: "",
      align: "right",
      render: (s) => (
        <button
          className="btn btn-ghost"
          onClick={() => {
            setGradeFor(s);
            setScore(s.score ?? "");
            setFeedback("");
          }}
        >
          Mark
        </button>
      ),
    },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
      <Panel title="Assignments" pad={false}>
        {assignments.length === 0 ? (
          <div style={{ padding: 16, fontSize: 13, color: "var(--muted)" }}>No assignments yet.</div>
        ) : (
          <div className="table-scroll">
            <table>
              <tbody>
                {assignments.map((a) => (
                  <tr
                    key={a.id}
                    onClick={() => open(a)}
                    style={{
                      cursor: "pointer",
                      boxShadow: selected?.id === a.id ? "inset 3px 0 0 var(--cyan)" : undefined,
                      background: selected?.id === a.id ? "var(--panel-2)" : undefined,
                    }}
                  >
                    <td>
                      <div style={{ fontWeight: 600 }}>{a.title}</div>
                      <div style={{ fontSize: 11, color: "var(--faint)" }}>
                        {a.is_published ? "published" : "draft"}
                        {a.due_at ? ` · due ${new Date(a.due_at).toLocaleDateString(AU_LOCALE)}` : ""}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <div>
        {!selected ? (
          <Panel title="Submissions">
            <div style={{ fontSize: 13, color: "var(--muted)" }}>Select an assignment to see who has handed in.</div>
          </Panel>
        ) : (
          <DataTable columns={subCols} rows={subs} emptyLabel="Nobody has handed in yet." />
        )}
      </div>

      <Modal open={!!gradeFor} onClose={() => setGradeFor(null)} title="Mark submission">
        <div className="space-y-3">
          {gradeFor?.text_response && (
            <div className="card p-3" style={{ background: "var(--panel-2)", maxHeight: 220, overflow: "auto", fontSize: 13 }}>
              {gradeFor.text_response}
            </div>
          )}
          <Field label={`Score (out of ${selected?.max_score ?? "?"})`}>
            <input className="input" type="number" value={score} onChange={(e) => setScore(e.target.value)} autoFocus />
          </Field>
          <Field label="Feedback">
            <textarea className="input" rows={4} value={feedback} onChange={(e) => setFeedback(e.target.value)} />
          </Field>
          <div className="flex justify-end gap-2">
            <button className="btn btn-ghost" onClick={() => setGradeFor(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={grade} disabled={score === ""}>Save mark</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
