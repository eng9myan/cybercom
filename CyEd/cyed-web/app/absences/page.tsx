"use client";

import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { fmtDate } from "@/lib/portal";

/**
 * The office's absence-explanation queue.
 *
 * Accepting excuses the marks the explanation covers — it edits the attendance
 * record the department audits, which is why this is staff-only and why the
 * effect is stated on the button rather than left implicit.
 *
 * Declining requires a reason: a family told "no" with no explanation rings the
 * office, which is the call this feature exists to prevent.
 */

type Explanation = {
  id: string;
  student: string;
  student_name: string;
  kind: string;
  start_date: string;
  end_date: string;
  reason: string;
  detail: string;
  status: string;
  submitted_by_name: string;
  submitted_by_email: string;
  day_count: number;
  marks_updated: number;
};

export default function AbsenceQueuePage() {
  const [rows, setRows] = useState<Explanation[]>([]);
  const [view, setView] = useState<"submitted" | "all">("submitted");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [declining, setDeclining] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const path =
        view === "submitted"
          ? "attendance/explanations/?status=submitted"
          : "attendance/explanations/";
      setRows(await cyed.list<Explanation>(path));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load the queue");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view]);

  const accept = async (row: Explanation) => {
    setBusy(row.id);
    try {
      const resp = await cyed.action<{ marks_excused: number; planned: boolean }>(
        `attendance/explanations/${row.id}/accept/`,
      );
      toast.push(
        resp.planned
          ? "Accepted. It will be applied when the roll is taken."
          : `Accepted — ${resp.marks_excused} mark(s) excused.`,
      );
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not accept that");
    } finally {
      setBusy(null);
    }
  };

  const decline = async (row: Explanation) => {
    if (!note.trim()) return;
    setBusy(row.id);
    try {
      await cyed.action(`attendance/explanations/${row.id}/decline/`, { note });
      toast.push("Declined. The family can see your reason.");
      setDeclining(null);
      setNote("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not decline that");
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <SkeletonRows rows={6} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Absence explanations"
        subtitle="Accepting excuses the marks it covers"
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "submitted", label: "To review" },
              { value: "all", label: "All" },
            ]}
          />
        }
      />

      {rows.length === 0 ? (
        <Empty
          label={
            view === "submitted"
              ? "Nothing waiting to be reviewed."
              : "No explanations have been submitted yet."
          }
        />
      ) : (
        <Panel pad={false}>
          {rows.map((row) => (
            <div
              key={row.id}
              style={{ padding: "1rem 1.1rem", borderBottom: "1px solid var(--border)" }}
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
                <div style={{ minWidth: "14rem" }}>
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                    <strong>{row.student_name}</strong>
                    <Badge value={row.status} />
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: 2 }}>
                    {fmtDate(row.start_date)}
                    {row.end_date !== row.start_date && ` – ${fmtDate(row.end_date)}`}
                    {row.day_count > 1 && ` · ${row.day_count} days`} · {row.reason}
                  </div>
                  {row.detail && (
                    <div style={{ fontSize: "0.85rem", marginTop: 4 }}>{row.detail}</div>
                  )}
                  <div style={{ fontSize: "0.78rem", color: "var(--faint)", marginTop: 4 }}>
                    from {row.submitted_by_name || row.submitted_by_email}
                  </div>
                </div>

                {row.status === "submitted" && (
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button
                      className="btn btn-primary"
                      disabled={busy !== null}
                      onClick={() => accept(row)}
                    >
                      <Check size={15} style={{ marginRight: 4 }} />
                      Accept
                    </button>
                    <button
                      className="btn"
                      disabled={busy !== null}
                      onClick={() => {
                        setDeclining(declining === row.id ? null : row.id);
                        setNote("");
                      }}
                    >
                      <X size={15} style={{ marginRight: 4 }} />
                      Decline
                    </button>
                  </div>
                )}

                {row.status === "accepted" && row.marks_updated > 0 && (
                  <span style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                    {row.marks_updated} mark(s) excused
                  </span>
                )}
              </div>

              {declining === row.id && (
                <div style={{ marginTop: "0.75rem", display: "grid", gap: "0.5rem" }}>
                  <textarea
                    className="input"
                    rows={2}
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Why is this being declined? The family will see this."
                    style={{ width: "100%", resize: "vertical" }}
                  />
                  <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
                    <button className="btn" onClick={() => setDeclining(null)}>
                      Cancel
                    </button>
                    <button
                      className="btn btn-primary"
                      disabled={!note.trim() || busy !== null}
                      onClick={() => decline(row)}
                    >
                      Send decline
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </Panel>
      )}
    </div>
  );
}
