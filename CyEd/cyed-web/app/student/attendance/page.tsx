"use client";

import { useEffect, useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { AttendanceSummary, Note } from "@/app/portal/_parts";
import type { AttendanceMarkRow, RollCallRow } from "@/lib/portal";

/**
 * A student's own attendance.
 *
 * The same summary component parents see — a student checking their rate is
 * asking the same question their family is, and two different renderings of
 * one number invite arguments about which is right.
 */
export default function StudentAttendancePage() {
  const [marks, setMarks] = useState<AttendanceMarkRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        // Already scoped server-side: a student's own rows and nobody else's.
        setMarks(await cyed.list<AttendanceMarkRow>("attendance/marks/"));
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load your attendance");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const rollCalls: Record<string, RollCallRow> = Object.fromEntries(
    marks
      .filter((m) => m.date)
      .map((m) => [
        m.roll_call,
        {
          id: m.roll_call,
          date: m.date as string,
          class_section_name: m.class_section_name,
          period_label: m.period_label,
        },
      ]),
  );

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;
  if (marks.length === 0) {
    return <Empty label="No attendance has been recorded for you yet." />;
  }

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="My attendance" subtitle="Your record this year" />
      <AttendanceSummary marks={marks} rollCalls={rollCalls} />
      <Note>
        Absences are explained by a parent or carer through their portal. If something here
        looks wrong, ask them to contact the office.
      </Note>
    </div>
  );
}
