"use client";

import { useEffect, useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { Note, PersonSwitcher } from "@/app/portal/_parts";
import { useToast } from "@/components/Toast";
import { fmtDate, useMyChildren } from "@/lib/portal";

/**
 * Explaining an absence.
 *
 * The most-used parent action in a school system. Two things the form has to
 * make honest:
 *
 * * Submitting does not change the attendance record — the office accepts it
 *   first. Saying so up front prevents "I explained it, why does it still say
 *   absent?".
 * * A future date is allowed and is the *better* path: telling the school
 *   before Tuesday stops Tuesday's alert being sent at all.
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
  review_note: string;
  day_count: number;
};

const REASONS = [
  { value: "illness", label: "Illness" },
  { value: "medical", label: "Medical or dental appointment" },
  { value: "family", label: "Family reason" },
  { value: "bereavement", label: "Bereavement" },
  { value: "religious", label: "Religious observance" },
  { value: "travel", label: "Travel" },
  { value: "other", label: "Other" },
];

const KINDS = [
  { value: "absence", label: "Away for the day" },
  { value: "late", label: "Arriving late" },
  { value: "early_departure", label: "Leaving early" },
];

const today = () => new Date().toISOString().slice(0, 10);

export default function PortalAbsencesPage() {
  const { children, selected, setSelected, loading, error } = useMyChildren();
  const [rows, setRows] = useState<Explanation[]>([]);
  const [listError, setListError] = useState<string | null>(null);

  const [kind, setKind] = useState("absence");
  const [start, setStart] = useState(today());
  const [end, setEnd] = useState(today());
  const [reason, setReason] = useState("illness");
  const [detail, setDetail] = useState("");
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const load = async () => {
    if (!selected) return;
    try {
      setRows(await cyed.list<Explanation>(`attendance/explanations/?student=${selected}`));
      setListError(null);
    } catch (e) {
      setListError(e instanceof Error ? e.message : "Could not load your explanations");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);

  const submit = async () => {
    setSaving(true);
    try {
      await cyed.create("attendance/explanations/", {
        student: selected,
        kind,
        start_date: start,
        // A single day is the common case; the form keeps both fields so a
        // week of illness is one submission rather than five.
        end_date: end < start ? start : end,
        reason,
        detail,
      });
      toast.push("Sent to the school office.");
      setDetail("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not send that");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;
  if (!children.length) return <Empty label="No children are linked to this account yet." />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Absences" subtitle="Tell the school why your child is away" />
      <PersonSwitcher people={children} value={selected} onChange={setSelected} label="For" />

      <Panel title="Explain an absence">
        <div style={{ display: "grid", gap: "0.9rem" }}>
          <Field label="What is happening">
            <select className="input" value={kind} onChange={(e) => setKind(e.target.value)}>
              {KINDS.map((k) => (
                <option key={k.value} value={k.value}>
                  {k.label}
                </option>
              ))}
            </select>
          </Field>

          <div style={{ display: "grid", gap: "0.9rem", gridTemplateColumns: "1fr 1fr" }}>
            <Field label="First day">
              <input
                className="input"
                type="date"
                value={start}
                onChange={(e) => {
                  setStart(e.target.value);
                  if (end < e.target.value) setEnd(e.target.value);
                }}
              />
            </Field>
            <Field label="Last day">
              <input
                className="input"
                type="date"
                value={end}
                min={start}
                onChange={(e) => setEnd(e.target.value)}
              />
            </Field>
          </div>

          <Field label="Reason">
            <select className="input" value={reason} onChange={(e) => setReason(e.target.value)}>
              {REASONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Anything else the school should know (optional)">
            <textarea
              className="input"
              rows={3}
              value={detail}
              onChange={(e) => setDetail(e.target.value)}
              placeholder="e.g. Home with a temperature, back Thursday."
              style={{ width: "100%", resize: "vertical" }}
            />
          </Field>

          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button className="btn btn-primary" disabled={saving || !selected} onClick={submit}>
              {saving ? "Sending…" : "Send to the school"}
            </button>
          </div>
        </div>
      </Panel>

      <Note>
        Sending this does not change the attendance record on its own — the office reviews it
        first. If you know about an absence in advance, tell us before the day and we will not
        send you an alert about it.
      </Note>

      {listError && <ErrorNote error={listError} />}

      {rows.length > 0 && (
        <Panel title="What you have sent" pad={false}>
          {rows.map((row) => (
            <div
              key={row.id}
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
                <div style={{ fontWeight: 650 }}>
                  {fmtDate(row.start_date)}
                  {row.end_date !== row.start_date && ` – ${fmtDate(row.end_date)}`}
                  {row.day_count > 1 && ` (${row.day_count} days)`}
                </div>
                <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                  {REASONS.find((r) => r.value === row.reason)?.label ?? row.reason}
                  {row.detail && ` — ${row.detail}`}
                </div>
                {row.status === "declined" && row.review_note && (
                  <div style={{ fontSize: "0.82rem", color: "var(--red, #f87171)", marginTop: 3 }}>
                    School: {row.review_note}
                  </div>
                )}
              </div>
              <Badge value={row.status} />
            </div>
          ))}
        </Panel>
      )}
    </div>
  );
}
