"use client";

import { useEffect, useMemo, useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { AU_LOCALE } from "@/lib/portal";

type AssignmentRow = {
  student: string;
  assignment: string;
  title: string;
  due_at: string | null;
  is_overdue: boolean;
  allow_late: boolean;
  max_score: string;
  status: string;
  submission: string | null;
  submitted_at: string | null;
  score: string | null;
};

/**
 * Assignments, and handing work in.
 *
 * Outstanding work is shown first and by default — a list that opens on
 * everything ever set buries the two things due tomorrow.
 */
export default function StudentAssignmentsPage() {
  const [rows, setRows] = useState<AssignmentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"outstanding" | "all">("outstanding");
  const [notAStudent, setNotAStudent] = useState(false);
  const [openRow, setOpenRow] = useState<AssignmentRow | null>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const load = async () => {
    try {
      const data = await cyed.get<{ results: AssignmentRow[] }>("assessment/assignments/mine/");
      setRows(data.results ?? []);
      setError(null);
      setNotAStudent(false);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Could not load your assignments";
      // Staff opening the student view is not an error, and the API's own
      // wording ("Staff must pass ?student=<uuid>") is an instruction to a
      // developer, not to the person reading the screen.
      if (msg.includes("Staff must pass")) {
        setNotAStudent(true);
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

  const shown = useMemo(
    () => (filter === "all" ? rows : rows.filter((r) => r.status === "outstanding")),
    [rows, filter],
  );

  const hand_in = async () => {
    if (!openRow || !text.trim()) return;
    setBusy(true);
    try {
      // Create the submission, then submit it — two steps because a draft that
      // was never handed in is a real state, and one call would remove it.
      const submission = openRow.submission
        ? { id: openRow.submission }
        : await cyed.create<{ id: string }>("assessment/submissions/", {
            assignment: openRow.assignment,
            student: openRow.student,
            text_response: text,
          });
      if (openRow.submission) {
        await cyed.patch(`assessment/submissions/${submission.id}/`, { text_response: text });
      }
      await cyed.action(`assessment/submissions/${submission.id}/submit/`);
      toast.push("Handed in.");
      setOpenRow(null);
      setText("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not hand that in");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;
  if (notAStudent) {
    return (
      <Empty label="This is the student view. Sign in as a student to see your own assignments — staff can see who has handed in from the Assessment page." />
    );
  }

  if (openRow) {
    return (
      <div style={{ display: "grid", gap: "1rem" }}>
        <PageHeader
          title={openRow.title}
          subtitle={openRow.due_at ? `Due ${new Date(openRow.due_at).toLocaleString(AU_LOCALE)}` : "No due date"}
          action={
            <button className="btn" onClick={() => setOpenRow(null)}>
              Back
            </button>
          }
        />
        {openRow.is_overdue && !openRow.allow_late && (
          <ErrorNote error="This assignment is past its due date and the teacher has not allowed late submissions." />
        )}
        <Panel title="Your answer">
          <textarea
            className="input"
            rows={10}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type your response…"
            style={{ width: "100%", resize: "vertical" }}
          />
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.6rem" }}>
            <button className="btn btn-primary" disabled={busy || !text.trim()} onClick={hand_in}>
              {busy ? "Handing in…" : "Hand in"}
            </button>
          </div>
        </Panel>
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Assignments"
        subtitle={`${rows.filter((r) => r.status === "outstanding").length} outstanding`}
      />

      <Segmented
        value={filter}
        onChange={setFilter}
        options={[
          { value: "outstanding", label: "Outstanding" },
          { value: "all", label: "All" },
        ]}
      />

      {shown.length === 0 ? (
        <Empty label={filter === "outstanding" ? "Nothing outstanding. Well done." : "No assignments yet."} />
      ) : (
        <Panel pad={false}>
          {shown.map((r) => (
            <div
              key={r.assignment}
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "0.75rem",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0.9rem 1.1rem",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <div>
                <div style={{ fontWeight: 650 }}>{r.title}</div>
                <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                  {r.due_at ? `Due ${new Date(r.due_at).toLocaleDateString(AU_LOCALE)}` : "No due date"}
                  {r.score !== null && ` · ${r.score}/${r.max_score}`}
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
                <Badge value={r.is_overdue && r.status === "outstanding" ? "overdue" : r.status} />
                {r.status === "outstanding" && (
                  <button
                    className="btn btn-primary"
                    onClick={() => {
                      setOpenRow(r);
                      setText("");
                    }}
                  >
                    Open
                  </button>
                )}
              </div>
            </div>
          ))}
        </Panel>
      )}
    </div>
  );
}
