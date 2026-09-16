"use client";

import { useEffect, useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { AttendanceSummary, Note, PersonSwitcher } from "@/app/portal/_parts";
import { useMyChildren, type AttendanceMarkRow, type RollCallRow } from "@/lib/portal";

/**
 * A child's attendance record.
 *
 * Each mark carries its own date and class, so nothing is joined client-side.
 * The alternative — fetching roll calls and matching by id — needs every roll
 * call in the school, and quietly shows blank dates for any that fall past the
 * first page.
 */
export default function PortalAttendancePage() {
  const { children, selected, setSelected, loading, error } = useMyChildren();
  const [marks, setMarks] = useState<AttendanceMarkRow[]>([]);
  const [loadingMarks, setLoadingMarks] = useState(false);
  const [markError, setMarkError] = useState<string | null>(null);

  useEffect(() => {
    if (!selected) return;
    setLoadingMarks(true);
    (async () => {
      try {
        setMarks(await cyed.list<AttendanceMarkRow>(`attendance/marks/?student=${selected}`));
        setMarkError(null);
      } catch (e) {
        setMarkError(e instanceof Error ? e.message : "Could not load the attendance record");
      } finally {
        setLoadingMarks(false);
      }
    })();
  }, [selected]);

  // `_parts.AttendanceSummary` takes a roll-call lookup; build it from the
  // marks themselves rather than a second request.
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
  if (!children.length) return <Empty label="No children are linked to this account yet." />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Attendance" subtitle="Your child's record this year" />
      <PersonSwitcher people={children} value={selected} onChange={setSelected} label="Viewing" />

      <AttendanceSummary
        marks={marks}
        rollCalls={rollCalls}
        loading={loadingMarks}
        error={markError}
      />

      <Note>
        If an absence looks wrong, message the school from the Messages tab — attendance is a legal
        record and is corrected by the office, not here.
      </Note>
    </div>
  );
}
