"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Segmented } from "@/components/kit";
import { DAY_LABELS } from "@/lib/portal";

/**
 * My timetable — the teacher's own teaching load.
 *
 * Resolved server-side from the signed-in account, so it follows cover and
 * split-class overrides rather than the class list. The same endpoint answers
 * for students and parents, which is why nothing here filters by role.
 */

type Slot = {
  id: string;
  day_of_week: string;
  period_label: string;
  start_time: string;
  end_time: string;
  room: string;
  class_section: string;
  class_section_name: string;
  subject?: string;
};

const DAYS = ["mon", "tue", "wed", "thu", "fri"];

const shortTime = (t: string) => (t || "").slice(0, 5);

export default function TimetablePage() {
  const [slots, setSlots] = useState<Slot[]>([]);
  const [day, setDay] = useState<string>(() => {
    const today = new Date().getDay();
    return DAYS[Math.min(Math.max(today - 1, 0), 4)];
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noStaffRecord, setNoStaffRecord] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setSlots(await cyed.get<Slot[]>("timetable/slots/mine/"));
        setError(null);
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Could not load your timetable";
        // Signed in as an account with no Staff row — a real state on a demo
        // instance, and not something to show as a red error.
        if (msg.includes("No staff record")) {
          setNoStaffRecord(true);
        } else {
          setError(msg);
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const shown = useMemo(
    () =>
      slots
        .filter((s) => s.day_of_week === day)
        .sort((a, b) => a.start_time.localeCompare(b.start_time)),
    [slots, day],
  );

  const load = useMemo(() => {
    const byDay: Record<string, number> = {};
    for (const s of slots) byDay[s.day_of_week] = (byDay[s.day_of_week] ?? 0) + 1;
    return byDay;
  }, [slots]);

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;
  if (noStaffRecord) {
    return (
      <div style={{ display: "grid", gap: "1.25rem" }}>
        <PageHeader title="My timetable" subtitle="Your teaching load" />
        <Empty label="This account is not linked to a staff record, so it has no teaching load. Sign in as a teacher to see one." />
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="My timetable"
        subtitle={`${slots.length} period(s) a week`}
        action={
          <Segmented
            value={day}
            onChange={setDay}
            options={DAYS.map((d) => ({
              value: d,
              label: `${(DAY_LABELS[d] ?? d).slice(0, 3)}${load[d] ? ` (${load[d]})` : ""}`,
            }))}
          />
        }
      />

      {shown.length === 0 ? (
        <Empty label={`Nothing timetabled on ${DAY_LABELS[day] ?? day}.`} />
      ) : (
        <Panel pad={false}>
          {shown.map((slot) => (
            <div
              key={slot.id}
              style={{
                display: "flex",
                gap: "1rem",
                alignItems: "center",
                padding: "0.9rem 1.1rem",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <div style={{ minWidth: "5.5rem" }}>
                <div style={{ fontWeight: 700 }}>{shortTime(slot.start_time)}</div>
                <div style={{ fontSize: "0.78rem", color: "var(--faint)" }}>
                  {shortTime(slot.end_time)}
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <strong>{slot.class_section_name}</strong>
                <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                  {slot.period_label}
                  {slot.room && ` · ${slot.room}`}
                </div>
              </div>
              <CalendarDays size={16} style={{ color: "var(--faint)" }} />
            </div>
          ))}
        </Panel>
      )}
    </div>
  );
}
