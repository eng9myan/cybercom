"use client";

import { useEffect, useMemo, useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Segmented } from "@/components/kit";
import { DAY_LABELS, DAY_ORDER, clock, type TimetableSlot } from "@/lib/portal";

/**
 * A student's timetable.
 *
 * Defaults to today, because that is the question being asked ninety per cent
 * of the time — "what have I got now?" The week is one tap away for planning.
 */
export default function StudentTodayPage() {
  const [slots, setSlots] = useState<TimetableSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const todayCode = DAY_ORDER[(new Date().getDay() + 6) % 7];
  const [day, setDay] = useState<string>(todayCode);

  const [notAStudent, setNotAStudent] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const rows = await cyed.get<TimetableSlot[]>("timetable/slots/mine/");
        setSlots(Array.isArray(rows) ? rows : []);
        setError(null);
      } catch (e) {
        const message = e instanceof Error ? e.message : "Could not load your timetable";
        // A staff account opening the student portal hits the teacher branch
        // and is told about staff records. True, but meaningless here — say
        // what it actually means instead of forwarding the API's wording.
        if (message.includes("staff record") || message.includes("pass ?student")) {
          setNotAStudent(true);
        } else {
          setError(message);
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

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;
  if (notAStudent) {
    return (
      <Empty label="This is the student view. Sign in as a student to see your timetable — staff can view a student's day from the Students page." />
    );
  }

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title={day === todayCode ? "Today" : DAY_LABELS[day]}
        subtitle="Your timetable"
      />

      <div style={{ overflowX: "auto" }}>
        <Segmented
          value={day}
          onChange={setDay}
          options={DAY_ORDER.slice(0, 5).map((d) => ({
            value: d,
            label: DAY_LABELS[d].slice(0, 3),
          }))}
        />
      </div>

      <Panel>
        {shown.length === 0 ? (
          <Empty label="Nothing timetabled." />
        ) : (
          <div>
            {shown.map((s) => (
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
    </div>
  );
}
