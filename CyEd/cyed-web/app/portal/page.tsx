"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CalendarDays, FileText, MessageSquare, Receipt } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { PersonSwitcher } from "@/app/portal/_parts";
import {
  DAY_LABELS,
  DAY_ORDER,
  clock,
  fullName,
  money,
  useMyChildren,
  type FamilyStatement,
  type PortalThread,
  type TimetableSlot,
} from "@/lib/portal";

/**
 * The family home screen.
 *
 * Answers the four questions a parent actually opens this for: what does my
 * child have today, is anything owed, has a report been published, and has
 * the school messaged me. Anything else belongs a tap deeper.
 */
export default function PortalHome() {
  const { children, selected, setSelected, child, loading, error } = useMyChildren();
  const [slots, setSlots] = useState<TimetableSlot[]>([]);
  const [statement, setStatement] = useState<FamilyStatement | null>(null);
  const [threads, setThreads] = useState<PortalThread[]>([]);
  const [detailError, setDetailError] = useState<string | null>(null);

  useEffect(() => {
    if (!selected) return;
    (async () => {
      try {
        const [timetable, inbox] = await Promise.all([
          cyed.get<TimetableSlot[]>(`timetable/slots/mine/?student=${selected}`),
          cyed.get<{ results: PortalThread[] }>("messaging/threads/inbox/"),
        ]);
        setSlots(Array.isArray(timetable) ? timetable : []);
        setThreads(inbox.results ?? []);
        setDetailError(null);
      } catch (e) {
        setDetailError(e instanceof Error ? e.message : "Could not load your child's day");
      }
    })();
  }, [selected]);

  useEffect(() => {
    (async () => {
      try {
        // The statement is a household view, so it does not change with the
        // selected child — fetched once, off the first family we can see.
        const families = await cyed.list<{ id: string }>("sis/families/");
        if (families[0]) {
          setStatement(await cyed.get<FamilyStatement>(`billing/families/${families[0].id}/statement/`));
        }
      } catch {
        // Fees are shown on their own page with a proper error; a failure
        // here should not blank the whole home screen.
      }
    })();
  }, []);

  const unread = threads.reduce((n, t) => n + t.unread, 0);
  const owing = Number(statement?.totals.balance ?? 0);
  const overdue = Number(statement?.totals.overdue ?? 0);

  const today = DAY_ORDER[(new Date().getDay() + 6) % 7];
  const todaySlots = slots
    .filter((s) => s.day_of_week === today)
    .sort((a, b) => a.start_time.localeCompare(b.start_time));

  if (loading) return <SkeletonRows rows={6} />;
  if (error) return <ErrorNote error={error} />;
  if (!children.length) {
    return (
      <Empty label="No children are linked to this account yet. Contact the school office." />
    );
  }

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title={`Hello${child ? `, ${child.first_name}'s family` : ""}`}
        subtitle="Your child's day, fees and messages"
      />

      <PersonSwitcher people={children} value={selected} onChange={setSelected} label="Viewing" />

      {detailError && <ErrorNote error={detailError} />}

      <div
        style={{
          display: "grid",
          gap: "0.75rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(13rem, 1fr))",
        }}
      >
        <QuickLink
          href="/portal/fees"
          icon={<Receipt size={18} />}
          label={overdue > 0 ? "Fees overdue" : "Fees"}
          value={statement ? money(owing) : "—"}
          tone={overdue > 0 ? "bad" : owing > 0 ? "warn" : "ok"}
        />
        <QuickLink
          href="/portal/messages"
          icon={<MessageSquare size={18} />}
          label="Messages"
          value={unread ? `${unread} unread` : "Up to date"}
          tone={unread ? "warn" : "ok"}
        />
        <QuickLink
          href="/portal/attendance"
          icon={<CalendarDays size={18} />}
          label="Attendance"
          value="View record"
        />
        <QuickLink
          href="/portal/reports"
          icon={<FileText size={18} />}
          label="Reports"
          value="View & download"
        />
      </div>

      <Panel title={`${child ? fullName(child) : "Today"} — ${DAY_LABELS[today] ?? "Today"}`}>
        {todaySlots.length === 0 ? (
          <Empty label="No classes timetabled today." />
        ) : (
          <div>
            {todaySlots.map((s) => (
              <div key={s.id} className="portal-day">
                <div className="when">
                  {clock(s.start_time)}
                  <br />
                  {clock(s.end_time)}
                </div>
                <div>
                  <div className="what">{s.class_section_name || s.period_label}</div>
                  <div className="where">
                    {[s.teacher_display, s.room].filter(Boolean).join(" · ") || "—"}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>

      {threads.length > 0 && (
        <Panel
          title="Recent messages"
          action={
            <Link href="/portal/messages" className="btn">
              All messages
            </Link>
          }
        >
          <div style={{ display: "grid", gap: "0.6rem" }}>
            {threads.slice(0, 3).map((t) => (
              <Link
                key={t.thread}
                href="/portal/messages"
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div style={{ display: "flex", gap: "0.75rem", alignItems: "baseline" }}>
                  <strong style={{ fontSize: "0.95rem" }}>{t.subject}</strong>
                  {t.unread > 0 && <Badge value="unread" />}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                  {t.last_sender}: {t.last_message_preview}
                </div>
              </Link>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}

function QuickLink({
  href,
  icon,
  label,
  value,
  tone,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
  value: string;
  tone?: "ok" | "warn" | "bad";
}) {
  const colour =
    tone === "bad" ? "var(--red, #f87171)" : tone === "warn" ? "var(--amber, #fbbf24)" : undefined;
  return (
    <Link href={href} style={{ textDecoration: "none", color: "inherit" }}>
      <div className="card card-hover p-5" style={{ display: "grid", gap: "0.35rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--muted)" }}>
          {icon}
          <span className="label">{label}</span>
        </div>
        <div style={{ fontSize: "1.35rem", fontWeight: 800, color: colour }}>{value}</div>
      </div>
    </Link>
  );
}
