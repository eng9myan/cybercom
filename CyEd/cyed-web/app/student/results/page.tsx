"use client";

import { useEffect, useMemo, useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import type { Grade, Assessment } from "@/lib/types";

/**
 * A student's results, assembled.
 *
 * `gradebook/grades/` was already student-scoped but returned bare rows with
 * no assessment attached, so a student could fetch their marks and still not
 * know what any of them were for. This joins the two and shows the percentage,
 * which is the number they are actually looking for.
 */
export default function StudentResultsPage() {
  const [grades, setGrades] = useState<Grade[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [g, a] = await Promise.all([
          cyed.list<Grade>("gradebook/grades/"),
          cyed.list<Assessment>("gradebook/assessments/"),
        ]);
        setGrades(g);
        setAssessments(a);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load your results");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const rows = useMemo(() => {
    const byId = new Map(assessments.map((a) => [a.id, a]));
    return grades
      .map((g) => {
        const a = byId.get(g.assessment);
        const max = Number(a?.max_score ?? 0);
        const score = g.score === null || g.score === undefined ? null : Number(g.score);
        return {
          id: g.id,
          name: a?.name ?? "Assessment",
          max,
          score,
          percent: score !== null && max > 0 ? Math.round((score / max) * 1000) / 10 : null,
          level: g.achievement_level,
          comment: g.comment,
          due: a?.due_date ?? null,
        };
      })
      .sort((x, y) => (y.due ?? "").localeCompare(x.due ?? ""));
  }, [grades, assessments]);

  const average = useMemo(() => {
    const marked = rows.filter((r) => r.percent !== null);
    if (!marked.length) return null;
    return Math.round((marked.reduce((n, r) => n + (r.percent ?? 0), 0) / marked.length) * 10) / 10;
  }, [rows]);

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Results" subtitle="Your marked work" />

      {average !== null && (
        <Panel>
          <div style={{ display: "grid", gap: "0.3rem" }}>
            <span className="label">Average across marked work</span>
            <div style={{ fontSize: "2.25rem", fontWeight: 900 }}>{average}%</div>
          </div>
        </Panel>
      )}

      {rows.length === 0 ? (
        <Empty label="Nothing has been marked yet." />
      ) : (
        <Panel pad={false}>
          {rows.map((r) => (
            <div
              key={r.id}
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
              <div style={{ minWidth: "12rem" }}>
                <div style={{ fontWeight: 650 }}>{r.name}</div>
                {r.comment && (
                  <div style={{ fontSize: "0.82rem", color: "var(--muted)", marginTop: 2 }}>
                    {r.comment}
                  </div>
                )}
              </div>
              <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
                {r.level && <Badge value={r.level} />}
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontWeight: 800 }}>
                    {r.score === null ? "—" : `${r.score}/${r.max}`}
                  </div>
                  {r.percent !== null && (
                    <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{r.percent}%</div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </Panel>
      )}
    </div>
  );
}
