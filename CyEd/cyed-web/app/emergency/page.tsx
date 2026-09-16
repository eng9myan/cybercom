"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Siren, Users } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";

/**
 * Emergency roll — fire drills, evacuations, lockdowns.
 *
 * Designed for one situation: standing in a car park, on a phone, with an alarm
 * going. That drives every choice here.
 *
 * * **Big tap targets, one action.** Marking a student safe is a single tap on
 *   a full-width row. No modals, no confirmations — a confirmation dialog
 *   during an evacuation is an obstacle, and the action is trivially reversible.
 * * **Unaccounted is the whole screen.** Safe students disappear from the list.
 *   The only question that matters is who has not been seen, and a list that
 *   keeps everyone visible buries it.
 * * **Medical alerts are loud and first.** If someone is missing and carries an
 *   EpiPen, the person searching needs that before they set off.
 * * **The board polls.** Several staff mark different students at once from
 *   different phones; a stale screen sends two people after the same child.
 */

type DrillEntry = {
  student: string;
  name: string;
  class_section: string;
  medical_alert: boolean;
};

type Board = {
  drill: string;
  kind: string;
  started_at: string;
  ended_at: string | null;
  expected: number;
  safe: number;
  missing: number;
  unaccounted: number;
  all_clear: boolean;
  still_unaccounted: DrillEntry[];
};

type OnSiteStudent = {
  student: string;
  name: string;
  class_section: string;
  medical_alert?: { type: string; severity: string; medication: string; medication_location: string };
};

type OnSite = {
  on_site_count: number;
  off_site_count: number;
  medical_alerts: number;
  sections: { class_section: string; count: number; students: OnSiteStudent[] }[];
  visitors: { visitor: string; name: string; organisation: string }[];
};

const KINDS = [
  { value: "fire_drill", label: "Fire drill" },
  { value: "evacuation", label: "Evacuation" },
  { value: "lockdown", label: "Lockdown" },
  { value: "lockout", label: "Lockout" },
];

export default function EmergencyPage() {
  const [onSite, setOnSite] = useState<OnSite | null>(null);
  const [board, setBoard] = useState<Board | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const toast = useToast();

  const loadOnSite = useCallback(async () => {
    try {
      setOnSite(await cyed.get<OnSite>("attendance/emergency-drills/on-site/"));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load who is on site");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOnSite();
  }, [loadOnSite]);

  // Several staff mark different students from different phones. Without this
  // two people go looking for the same child while a third is never searched for.
  useEffect(() => {
    if (!board || board.ended_at) return;
    const timer = setInterval(async () => {
      try {
        setBoard(await cyed.get<Board>(`attendance/emergency-drills/${board.drill}/board/`));
      } catch {
        // A dropped poll on school wifi is expected; the next one recovers.
      }
    }, 5000);
    return () => clearInterval(timer);
  }, [board]);

  const start = async (kind: string) => {
    setBusy("start");
    try {
      setBoard(await cyed.action<Board>("attendance/emergency-drills/open/", { kind }));
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not start the drill");
    } finally {
      setBusy(null);
    }
  };

  const markSafe = async (studentId: string) => {
    if (!board) return;
    setBusy(studentId);
    try {
      const next = await cyed.action<Board & { updated: number }>(
        `attendance/emergency-drills/${board.drill}/account-for/`,
        { students: [studentId], state: "safe" },
      );
      setBoard(next);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not mark that student");
    } finally {
      setBusy(null);
    }
  };

  const close = async () => {
    if (!board) return;
    setBusy("close");
    try {
      setBoard(await cyed.action<Board>(`attendance/emergency-drills/${board.drill}/close/`, {}));
      toast.push("Drill closed.");
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not close the drill");
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  // ── live drill ────────────────────────────────────────────────────────────
  if (board) {
    const done = Boolean(board.ended_at);
    return (
      <div style={{ display: "grid", gap: "1rem" }}>
        <PageHeader
          title={KINDS.find((k) => k.value === board.kind)?.label ?? "Drill"}
          subtitle={done ? "Closed" : "In progress"}
          action={
            done ? (
              <button className="btn" onClick={() => setBoard(null)}>
                Done
              </button>
            ) : (
              <button className="btn" disabled={busy !== null} onClick={close}>
                {busy === "close" ? "Closing…" : "Close drill"}
              </button>
            )
          }
        />

        <div
          style={{
            display: "grid",
            gap: "0.6rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(8rem, 1fr))",
          }}
        >
          <Count label="Unaccounted" value={board.unaccounted} tone={board.unaccounted ? "bad" : "ok"} />
          <Count label="Safe" value={board.safe} tone="ok" />
          <Count label="Expected" value={board.expected} />
        </div>

        {board.all_clear ? (
          <Panel>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                color: "var(--green, #34d399)",
                fontSize: "1.25rem",
                fontWeight: 800,
              }}
            >
              <CheckCircle2 size={28} />
              All clear — everyone accounted for
            </div>
          </Panel>
        ) : (
          <Panel title={`Still unaccounted (${board.still_unaccounted.length})`} pad={false}>
            {board.still_unaccounted.map((entry) => (
              <button
                key={entry.student}
                onClick={() => markSafe(entry.student)}
                disabled={busy !== null || done}
                style={{
                  display: "flex",
                  width: "100%",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "1rem",
                  // Deliberately large: this is tapped with cold hands, in a
                  // hurry, possibly while holding something else.
                  padding: "1.1rem 1.1rem",
                  border: 0,
                  borderBottom: "1px solid var(--border)",
                  background: entry.medical_alert
                    ? "color-mix(in srgb, var(--red, #f87171) 12%, transparent)"
                    : "transparent",
                  color: "inherit",
                  font: "inherit",
                  textAlign: "left",
                  cursor: done ? "default" : "pointer",
                }}
              >
                <span style={{ minWidth: 0 }}>
                  <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    {entry.medical_alert && (
                      <AlertTriangle size={18} style={{ color: "var(--red, #f87171)", flexShrink: 0 }} />
                    )}
                    <strong style={{ fontSize: "1.05rem" }}>{entry.name}</strong>
                  </span>
                  <span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                    {entry.class_section || "—"}
                    {entry.medical_alert && " · medical alert"}
                  </span>
                </span>
                {!done && <span className="btn btn-primary">Safe</span>}
              </button>
            ))}
          </Panel>
        )}
      </div>
    );
  }

  // ── before a drill ────────────────────────────────────────────────────────
  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Emergency" subtitle="Roll for drills, evacuations and lockdowns" />

      <Panel>
        <div style={{ display: "grid", gap: "0.6rem" }}>
          <div style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
            <Users size={18} style={{ color: "var(--muted)" }} />
            <strong style={{ fontSize: "1.5rem" }}>{onSite?.on_site_count ?? 0}</strong>
            <span style={{ color: "var(--muted)" }}>students on site</span>
          </div>
          <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            {onSite?.off_site_count ?? 0} marked absent today ·{" "}
            {onSite?.visitors.length ?? 0} visitor(s) signed in ·{" "}
            {onSite?.medical_alerts ?? 0} with a medical alert
          </div>
        </div>
      </Panel>

      <Panel title="Start a roll">
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem" }}>
          {KINDS.map((kind) => (
            <button
              key={kind.value}
              className="btn btn-primary"
              disabled={busy !== null}
              onClick={() => start(kind.value)}
              style={{ padding: "0.8rem 1.2rem", fontSize: "1rem" }}
            >
              <Siren size={16} style={{ marginRight: 6 }} />
              {kind.label}
            </button>
          ))}
        </div>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: "0.8rem" }}>
          Starting a roll freezes who is on site at that moment, so the list does not shift
          while people are being counted.
        </p>
      </Panel>

      {onSite && onSite.sections.length > 0 && (
        <Panel title="On site now">
          {onSite.sections.map((section) => (
            <div key={section.class_section} style={{ marginBottom: "0.9rem" }}>
              <div className="label" style={{ marginBottom: 4 }}>
                {section.class_section} · {section.count}
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
                {section.students.map((student) => (
                  <span
                    key={student.student}
                    className="pill"
                    style={{
                      fontSize: "0.78rem",
                      borderColor: student.medical_alert
                        ? "color-mix(in srgb, var(--red, #f87171) 45%, var(--border))"
                        : undefined,
                    }}
                    title={
                      student.medical_alert
                        ? `${student.medical_alert.type} — ${student.medical_alert.medication} (${student.medical_alert.medication_location})`
                        : undefined
                    }
                  >
                    {student.medical_alert && "⚠ "}
                    {student.name}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </Panel>
      )}

      {onSite && onSite.on_site_count === 0 && (
        <Empty label="No attendance has been recorded today, so there is nobody to count. Take the roll first." />
      )}
    </div>
  );
}

function Count({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "ok" | "bad";
}) {
  const colour =
    tone === "bad" ? "var(--red, #f87171)" : tone === "ok" ? "var(--green, #34d399)" : undefined;
  return (
    <div className="card p-5" style={{ display: "grid", gap: "0.2rem" }}>
      <span className="label">{label}</span>
      <strong style={{ fontSize: "2rem", color: colour }}>{value}</strong>
    </div>
  );
}
