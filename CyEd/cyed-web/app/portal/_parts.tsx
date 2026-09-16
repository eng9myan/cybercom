"use client";

/**
 * Pieces shared by the parent and student portals.
 *
 * Everything here is built from the existing design-system primitives
 * (card / Panel / Badge / DataTable / RadialRing) — the portals deliberately
 * introduce no new visual language, they just point the same components at a
 * family's own data.
 */

import React from "react";
import { BellRing, CalendarCheck, CheckCheck } from "lucide-react";
import { Empty, ErrorNote, SkeletonRows } from "@/components/ui";
import { Panel, Badge, Segmented, IconBadge } from "@/components/kit";
import { RadialRing } from "@/components/viz";
import {
  attendanceStats,
  displayName,
  fmtDate,
  fmtDateTime,
  type AttendanceMarkRow,
  type NotificationRow,
  type RollCallRow,
} from "@/lib/portal";

/* ── Who am I looking at ─────────────────────────────────────────────────── */

export type Person = { id: string; first_name?: string; last_name?: string; full_name?: string; year_level?: number };

/**
 * Child / student picker. One person needs no control at all; a handful fit in
 * a segmented control; a long list (a staff account previewing the portal sees
 * the whole school) falls back to a select so the header cannot blow out.
 */
export function PersonSwitcher({
  people,
  value,
  onChange,
  label = "Viewing",
}: {
  people: Person[];
  value: string;
  onChange: (id: string) => void;
  label?: string;
}) {
  if (people.length === 0) return null;

  if (people.length === 1) {
    const only = people[0];
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <span className="label">{label}</span>
        <span className="pill" style={{ fontSize: "0.75rem" }}>
          {displayName(only)}
          {only.year_level != null ? ` · Year ${only.year_level}` : ""}
        </span>
      </div>
    );
  }

  if (people.length <= 4) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <span className="label">{label}</span>
        <Segmented
          value={value}
          onChange={onChange}
          options={people.map((p) => ({ value: p.id, label: displayName(p).split(" ")[0] }))}
        />
      </div>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
      <label className="label" htmlFor="portal-person">
        {label}
      </label>
      <select
        id="portal-person"
        className="input"
        style={{ maxWidth: 260 }}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {people.map((p) => (
          <option key={p.id} value={p.id}>
            {displayName(p)}
            {p.year_level != null ? ` — Year ${p.year_level}` : ""}
          </option>
        ))}
      </select>
    </div>
  );
}

/* ── Attendance ──────────────────────────────────────────────────────────── */

const ABSENT_STATUSES = ["absent", "late", "excused", "left_early"];

/**
 * Attendance ring plus the days that were missed. Roll-call dates live on a
 * separate endpoint, so `rollCalls` maps roll_call id → the call itself; a mark
 * whose roll call did not come back still shows, just without a date.
 */
export function AttendanceSummary({
  marks,
  rollCalls,
  loading,
  error,
  title = "Attendance",
  limit = 12,
}: {
  marks: AttendanceMarkRow[];
  rollCalls: Record<string, RollCallRow>;
  loading?: boolean;
  error?: string | null;
  title?: string;
  limit?: number;
}) {
  const stats = attendanceStats(marks);

  const missed = marks
    .filter((m) => ABSENT_STATUSES.includes(m.status))
    .map((m) => ({ mark: m, call: rollCalls[m.roll_call] }))
    .sort((a, b) => (b.call?.date || "").localeCompare(a.call?.date || ""))
    .slice(0, limit);

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: "minmax(220px, 280px) 1fr", alignItems: "start" }}>
      <Panel title={title}>
        {stats.total === 0 ? (
          <div style={{ fontSize: 13, color: "var(--muted)" }}>No attendance has been recorded yet.</div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
            <RadialRing value={stats.rate} size={104} label="Attendance" sublabel="attended" gradient="cyan" />
            <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.9 }}>
              <div>
                <strong style={{ color: "var(--ink)" }}>{stats.attended}</strong> of {stats.total} sessions
              </div>
              <div>
                <span className="status status-bad">{stats.absent} absent</span>
              </div>
              <div>
                <span className="status status-warn">{stats.late} late</span>
              </div>
            </div>
          </div>
        )}
      </Panel>

      <Panel title="Absences & lateness">
        {missed.length === 0 ? (
          <div style={{ fontSize: 13, color: "var(--muted)" }}>
            {stats.total === 0
              ? "Nothing recorded yet."
              : "No absences on record — a full attendance history."}
          </div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Class</th>
                  <th>Status</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {missed.map(({ mark, call }) => (
                  <tr key={mark.id}>
                    <td style={{ whiteSpace: "nowrap" }}>{call ? fmtDate(call.date) : "—"}</td>
                    <td style={{ color: "var(--muted)" }}>{call?.class_section_name || "—"}</td>
                    <td>
                      <Badge value={mark.status} />
                    </td>
                    <td style={{ color: "var(--muted)" }}>
                      {mark.note || (mark.minutes_late ? `${mark.minutes_late} min late` : "—")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}

/* ── Notices ─────────────────────────────────────────────────────────────── */

const CATEGORY_COLOR: Record<string, string> = {
  attendance: "var(--blue)",
  billing: "var(--violet)",
  wellbeing: "#34d399",
  announcement: "var(--cyan)",
  general: "var(--cyan)",
};

/** Inbox of school notices, newest first, with a mark-as-read affordance. */
export function NoticeInbox({
  rows,
  loading,
  error,
  onMarkRead,
  busyId,
  emptyLabel = "No notices from the school yet.",
}: {
  rows: NotificationRow[];
  loading?: boolean;
  error?: string | null;
  onMarkRead: (n: NotificationRow) => void;
  busyId?: string | null;
  emptyLabel?: string;
}) {
  if (loading) return <SkeletonRows rows={4} />;
  if (error) return <ErrorNote error={error} />;
  if (rows.length === 0) return <Empty label={emptyLabel} />;

  return (
    <div className="space-y-3 stagger">
      {rows.map((n) => {
        const unread = n.status !== "read";
        return (
          <article
            key={n.id}
            className="card card-hover p-4"
            style={{
              borderColor: unread ? "color-mix(in srgb, var(--cyan) 32%, var(--border))" : undefined,
            }}
          >
            <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
              <IconBadge color={CATEGORY_COLOR[n.category] || "var(--cyan)"}>
                <BellRing size={16} />
              </IconBadge>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  <span style={{ fontWeight: 700 }}>{n.subject}</span>
                  <Badge value={n.category} />
                  {unread && <span className="status status-warn">unread</span>}
                </div>
                {n.body && (
                  <p style={{ fontSize: 13, color: "var(--muted)", marginTop: 6, whiteSpace: "pre-wrap" }}>
                    {n.body}
                  </p>
                )}
                <div style={{ fontSize: 11, color: "var(--faint)", marginTop: 6 }}>
                  {fmtDateTime(n.created_at)}
                </div>
              </div>
            </div>
            {unread && (
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 10 }}>
                <button className="btn btn-ghost" onClick={() => onMarkRead(n)} disabled={busyId === n.id}>
                  <CheckCheck size={14} /> {busyId === n.id ? "Marking…" : "Mark as read"}
                </button>
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}

/* ── Small shared bits ───────────────────────────────────────────────────── */

/** A quiet explanatory note — used where the portal has to tell the truth about
    something the backend cannot do yet. */
export function Note({ children, tone = "info" }: { children: React.ReactNode; tone?: "info" | "warn" }) {
  const color = tone === "warn" ? "var(--warn)" : "var(--cyan)";
  return (
    <div
      className="card p-4"
      style={{
        fontSize: 13,
        color: "var(--muted)",
        borderColor: `color-mix(in srgb, ${color} 30%, var(--border))`,
      }}
    >
      {children}
    </div>
  );
}

/** Header row for a day of the timetable. */
export function DayHeading({ label, today }: { label: string; today?: boolean }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
      <CalendarCheck size={15} style={{ color: today ? "var(--cyan)" : "var(--faint)" }} />
      <span style={{ fontWeight: 700, fontSize: "0.9rem" }}>{label}</span>
      {today && <span className="status status-ok">today</span>}
    </div>
  );
}
