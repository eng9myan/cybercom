"use client";

import { useEffect, useMemo, useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Segmented } from "@/components/kit";
import { AU_LOCALE } from "@/lib/portal";

/**
 * Leadership dashboard.
 *
 * Whole-school aggregates for a principal or a group executive: how attendance
 * is trending, which year levels are dragging it down, who is below the line,
 * how achievement is spread, and what behaviour looks like.
 *
 * Two rules carried up from the backend and made visible rather than silent:
 * cohorts under five are suppressed (a rate over four students is one child's
 * record with a label on it), and the chronic-absence list names children — so
 * it is a list of names to act on, not a number to report.
 */

type TrendPoint = { week: string | null; total: number; attended: number; rate: number | null };
type YearRow = {
  year_level: number;
  students: number;
  total_marks: number;
  rate: number | null;
  suppressed: boolean;
};
type ChronicRow = {
  student: string;
  name: string;
  year_level: number;
  rate: number;
  sessions: number;
  missed: number;
};
type BehaviourWeek = { week: string | null; positive: number; minor: number; major: number };

type Overview = {
  weeks: number;
  attendance_rate_recent: number | null;
  attendance_trend: TrendPoint[];
  attendance_by_year_level: YearRow[];
  chronic_absence: { threshold: number; count: number; results: ChronicRow[] };
  achievement: { total: number; distribution: { level: string; count: number; percent: number }[] };
  behaviour: {
    weeks: BehaviourWeek[];
    by_year_level: { student__year_level: number; positive: number; negative: number }[];
  };
};

type CampusRow = {
  campus: string;
  name: string;
  students: number;
  attendance_rate: number | null;
  suppressed: boolean;
};

const WEEK_OPTIONS = [
  { value: "10", label: "10 weeks" },
  { value: "20", label: "20 weeks" },
  { value: "40", label: "40 weeks" },
];

const shortWeek = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString(AU_LOCALE, { day: "numeric", month: "short" }) : "";

/** Colour a rate the way a school reads it, not on a continuous scale. */
const rateTone = (rate: number | null) => {
  if (rate === null) return "var(--muted)";
  if (rate >= 92) return "var(--green, #34d399)";
  if (rate >= 88) return "var(--amber, #fbbf24)";
  return "var(--red, #f87171)";
};

export default function LeadershipPage() {
  const [weeks, setWeeks] = useState<"10" | "20" | "40">("20");
  const [data, setData] = useState<Overview | null>(null);
  const [campuses, setCampuses] = useState<CampusRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    (async () => {
      try {
        const [overview, comparison] = await Promise.all([
          cyed.get<Overview>(`analytics/dashboard/?weeks=${weeks}`),
          cyed.get<{ results: CampusRow[] }>(`analytics/campus-comparison/?weeks=${weeks}`),
        ]);
        setData(overview);
        setCampuses(comparison.results ?? []);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load the dashboard");
      } finally {
        setLoading(false);
      }
    })();
  }, [weeks]);

  const trend = useMemo(() => {
    const points = (data?.attendance_trend ?? []).filter((p) => p.rate !== null);
    if (points.length === 0) return null;
    const rates = points.map((p) => p.rate as number);
    // A fixed 0–100 axis flattens the only movement that matters: schools live
    // between about 85 and 96. Frame the axis on the data, with a floor of 5
    // points so a flat term does not render as noise.
    const lo = Math.min(...rates);
    const hi = Math.max(...rates);
    const pad = Math.max(5 - (hi - lo), 1) / 2;
    return { points, min: Math.max(0, lo - pad), max: Math.min(100, hi + pad) };
  }, [data]);

  if (loading) return <SkeletonRows rows={6} />;
  if (error) return <ErrorNote error={error} />;
  if (!data) return <Empty label="No data yet." />;

  const suppressedYears = data.attendance_by_year_level.filter((y) => y.suppressed).length;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Leadership"
        subtitle="Whole-school attendance, achievement and behaviour"
        action={
          <Segmented
            value={weeks}
            onChange={(v) => setWeeks(v as "10" | "20" | "40")}
            options={WEEK_OPTIONS as { value: "10" | "20" | "40"; label: string }[]}
          />
        }
      />

      <div
        style={{
          display: "grid",
          gap: "0.6rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(11rem, 1fr))",
        }}
      >
        <div className="card p-5">
          <span className="label">Attendance, last 4 weeks</span>
          <div
            style={{
              fontSize: "1.9rem",
              fontWeight: 800,
              color: rateTone(data.attendance_rate_recent),
            }}
          >
            {data.attendance_rate_recent === null ? "—" : `${data.attendance_rate_recent}%`}
          </div>
        </div>
        <div className="card p-5">
          <span className="label">Below {data.chronic_absence.threshold}%</span>
          <div
            style={{
              fontSize: "1.9rem",
              fontWeight: 800,
              color: data.chronic_absence.count ? "var(--red, #f87171)" : "var(--green, #34d399)",
            }}
          >
            {data.chronic_absence.count}
          </div>
        </div>
        <div className="card p-5">
          <span className="label">Marks recorded</span>
          <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{data.achievement.total}</div>
        </div>
        <div className="card p-5">
          <span className="label">Campuses</span>
          <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{campuses.length}</div>
        </div>
      </div>

      <Panel title={`Attendance rate, last ${data.weeks} weeks`}>
        {!trend ? (
          <Empty label="No attendance has been recorded in this window." />
        ) : (
          <>
            <svg
              viewBox="0 0 100 32"
              preserveAspectRatio="none"
              style={{ width: "100%", height: 160 }}
              role="img"
              aria-label={`Attendance trend over ${data.weeks} weeks`}
            >
              <polyline
                fill="none"
                stroke="var(--cyan)"
                strokeWidth="0.6"
                vectorEffect="non-scaling-stroke"
                points={trend.points
                  .map((p, i) => {
                    const x = (i / Math.max(trend.points.length - 1, 1)) * 100;
                    const y =
                      32 - (((p.rate as number) - trend.min) / (trend.max - trend.min)) * 32;
                    return `${x},${y}`;
                  })
                  .join(" ")}
              />
            </svg>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: "0.75rem",
                color: "var(--faint)",
              }}
            >
              <span>
                {shortWeek(trend.points[0].week)} · {trend.points[0].rate}%
              </span>
              <span>
                {trend.min.toFixed(1)}–{trend.max.toFixed(1)}% shown
              </span>
              <span>
                {shortWeek(trend.points[trend.points.length - 1].week)} ·{" "}
                {trend.points[trend.points.length - 1].rate}%
              </span>
            </div>
          </>
        )}
      </Panel>

      <Panel title="Attendance by year level">
        {data.attendance_by_year_level.length === 0 ? (
          <Empty label="No year-level data in this window." />
        ) : (
          <div style={{ display: "grid", gap: "0.5rem" }}>
            {data.attendance_by_year_level.map((row) => (
              <div
                key={row.year_level}
                style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}
              >
                <span style={{ width: "4.5rem", fontSize: "0.85rem" }}>Year {row.year_level}</span>
                <div
                  style={{
                    flex: 1,
                    height: 10,
                    borderRadius: 999,
                    background: "var(--panel-2)",
                    overflow: "hidden",
                  }}
                >
                  {row.rate !== null && (
                    <div
                      style={{
                        width: `${row.rate}%`,
                        height: "100%",
                        background: rateTone(row.rate),
                      }}
                    />
                  )}
                </div>
                <span
                  style={{
                    width: "8.5rem",
                    textAlign: "right",
                    fontSize: "0.83rem",
                    color: row.suppressed ? "var(--faint)" : rateTone(row.rate),
                  }}
                >
                  {row.suppressed ? "too few students" : `${row.rate}% · ${row.students}`}
                </span>
              </div>
            ))}
          </div>
        )}
        {suppressedYears > 0 && (
          <p style={{ fontSize: "0.78rem", color: "var(--faint)", marginTop: "0.7rem" }}>
            {suppressedYears} year level(s) are withheld because fewer than five students would
            sit behind the rate.
          </p>
        )}
      </Panel>

      {campuses.length > 1 && (
        <Panel title="Campuses side by side">
          <div style={{ display: "grid", gap: "0.5rem" }}>
            {campuses.map((row) => (
              <div
                key={row.campus}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "0.75rem",
                  padding: "0.5rem 0",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <span>
                  <strong>{row.name}</strong>
                  <span style={{ color: "var(--muted)", fontSize: "0.83rem" }}>
                    {" "}
                    · {row.students} students
                  </span>
                </span>
                <span style={{ color: rateTone(row.attendance_rate), fontWeight: 700 }}>
                  {row.suppressed || row.attendance_rate === null
                    ? "—"
                    : `${row.attendance_rate}%`}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      )}

      <Panel
        title={`Students below ${data.chronic_absence.threshold}%`}
        action={
          <span style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
            {data.chronic_absence.count} student(s)
          </span>
        }
      >
        {data.chronic_absence.results.length === 0 ? (
          <Empty label="Nobody is below the line in this window." />
        ) : (
          <div style={{ display: "grid", gap: "0.4rem" }}>
            {/* Worst first — the list exists to be worked down, not read. */}
            {data.chronic_absence.results.slice(0, 40).map((row) => (
              <div
                key={row.student}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "0.75rem",
                  padding: "0.45rem 0",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <span>
                  <strong>{row.name}</strong>
                  <span style={{ color: "var(--muted)", fontSize: "0.83rem" }}>
                    {" "}
                    · Year {row.year_level} · missed {row.missed} of {row.sessions}
                  </span>
                </span>
                <span style={{ color: rateTone(row.rate), fontWeight: 700 }}>{row.rate}%</span>
              </div>
            ))}
            {data.chronic_absence.results.length > 40 && (
              <p style={{ fontSize: "0.78rem", color: "var(--faint)" }}>
                Showing the 40 lowest of {data.chronic_absence.count}.
              </p>
            )}
          </div>
        )}
      </Panel>

      <Panel title="Achievement spread">
        {data.achievement.total === 0 ? (
          <Empty label="No graded work yet." />
        ) : (
          <div style={{ display: "grid", gap: "0.5rem" }}>
            {data.achievement.distribution.map((row) => (
              <div key={row.level} style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <span style={{ width: "2rem", fontWeight: 700 }}>{row.level}</span>
                <div
                  style={{
                    flex: 1,
                    height: 10,
                    borderRadius: 999,
                    background: "var(--panel-2)",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{ width: `${row.percent}%`, height: "100%", background: "var(--cyan)" }}
                  />
                </div>
                <span style={{ width: "7rem", textAlign: "right", fontSize: "0.83rem" }}>
                  {row.percent}% · {row.count}
                </span>
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel title="Behaviour">
        {data.behaviour.by_year_level.length === 0 ? (
          <Empty label="No behaviour recorded in this window." />
        ) : (
          <div style={{ display: "grid", gap: "0.5rem" }}>
            {data.behaviour.by_year_level.map((row) => {
              const total = row.positive + row.negative || 1;
              return (
                <div
                  key={row.student__year_level}
                  style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}
                >
                  <span style={{ width: "4.5rem", fontSize: "0.85rem" }}>
                    Year {row.student__year_level}
                  </span>
                  {/* Positive and negative side by side: an incident count on
                      its own tells a school it is getting worse even when
                      recognition is rising faster. */}
                  <div
                    style={{
                      flex: 1,
                      height: 10,
                      borderRadius: 999,
                      overflow: "hidden",
                      display: "flex",
                      background: "var(--panel-2)",
                    }}
                  >
                    <div
                      style={{
                        width: `${(row.positive / total) * 100}%`,
                        background: "var(--green, #34d399)",
                      }}
                    />
                    <div
                      style={{
                        width: `${(row.negative / total) * 100}%`,
                        background: "var(--red, #f87171)",
                      }}
                    />
                  </div>
                  <span style={{ width: "8.5rem", textAlign: "right", fontSize: "0.83rem" }}>
                    <span style={{ color: "var(--green, #34d399)" }}>{row.positive}</span>
                    {" / "}
                    <span style={{ color: "var(--red, #f87171)" }}>{row.negative}</span>
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </Panel>
    </div>
  );
}
