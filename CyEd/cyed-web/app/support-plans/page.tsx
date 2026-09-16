"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, ShieldCheck } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { fmtDate } from "@/lib/portal";

/**
 * Individual education plans.
 *
 * Built around the two questions a learning-support coordinator is actually
 * asked: *which plans are overdue for review*, and *would our NCCD return
 * survive an audit*. Both are landing views rather than reports buried behind
 * a plan list, because both are the reason someone opens this screen.
 *
 * Rows with thin evidence are shown with what is missing named. A count of
 * "12 substantial adjustments" tells a school nothing about which of those
 * twelve it could actually defend.
 */

type ReviewRow = {
  plan: string;
  student: string;
  name: string;
  plan_type: string;
  review_due: string | null;
  state: string;
  days_overdue: number;
  coordinator: string;
  last_review: string | null;
};

type EvidenceRow = {
  student: string;
  name: string;
  year_level: number;
  adjustment_level: string;
  adjustment_count: number;
  categories: string[];
  family_consulted_on: string | null;
  last_review: string | null;
  evidence_complete: boolean;
};

type Evidence = {
  year: number;
  count: number;
  incomplete_evidence: number;
  by_level: Record<string, number>;
  results: EvidenceRow[];
};

// Acronyms, not words: a badge reading "Iep" tells a coordinator the label was
// generated rather than written.
const PLAN_LABELS: Record<string, string> = {
  iep: "IEP",
  ilp: "ILP",
  behaviour: "Behaviour plan",
  risk: "Risk plan",
  eald: "EAL/D plan",
};

const LEVEL_LABELS: Record<string, string> = {
  qdtp: "Quality differentiated teaching",
  supplementary: "Supplementary",
  substantial: "Substantial",
  extensive: "Extensive",
};

export default function SupportPlansPage() {
  const [view, setView] = useState<"review" | "nccd">("review");
  const [reviews, setReviews] = useState<ReviewRow[]>([]);
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    (async () => {
      try {
        if (view === "review") {
          const data = await cyed.get<{ results: ReviewRow[] }>(
            "wellbeing/support-plans/needing-review/",
          );
          setReviews(data.results ?? []);
        } else {
          setEvidence(await cyed.get<Evidence>("wellbeing/support-plans/nccd-evidence/"));
        }
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load support plans");
      } finally {
        setLoading(false);
      }
    })();
  }, [view]);

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Support plans"
        subtitle="Individual education plans and NCCD evidence"
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "review", label: "Needs review" },
              { value: "nccd", label: "NCCD evidence" },
            ]}
          />
        }
      />

      {view === "review" &&
        (reviews.length === 0 ? (
          <Empty label="Every active plan is within its review window." />
        ) : (
          <Panel pad={false}>
            {reviews.map((row) => (
              <div
                key={row.plan}
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.9rem 1.1rem",
                  borderBottom: "1px solid var(--border)",
                  background:
                    row.state === "overdue"
                      ? "color-mix(in srgb, var(--red, #f87171) 8%, transparent)"
                      : undefined,
                }}
              >
                <div>
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                    {row.state === "overdue" && (
                      <AlertTriangle size={16} style={{ color: "var(--red, #f87171)" }} />
                    )}
                    <strong>{row.name}</strong>
                    <Badge value={PLAN_LABELS[row.plan_type] ?? row.plan_type} />
                  </div>
                  <div style={{ fontSize: "0.83rem", color: "var(--muted)", marginTop: 2 }}>
                    {row.review_due
                      ? `Review due ${fmtDate(row.review_due)}`
                      : "No review date set"}
                    {row.days_overdue > 0 && ` · ${row.days_overdue} days overdue`}
                    {row.last_review
                      ? ` · last reviewed ${fmtDate(row.last_review)}`
                      : " · never reviewed"}
                    {row.coordinator && ` · ${row.coordinator}`}
                  </div>
                </div>
                <Badge value={row.state} />
              </div>
            ))}
          </Panel>
        ))}

      {view === "nccd" && evidence && (
        <>
          <div
            style={{
              display: "grid",
              gap: "0.6rem",
              gridTemplateColumns: "repeat(auto-fit, minmax(10rem, 1fr))",
            }}
          >
            <div className="card p-5">
              <span className="label">Students reported</span>
              <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{evidence.count}</div>
            </div>
            <div className="card p-5">
              <span className="label">Thin evidence</span>
              <div
                style={{
                  fontSize: "1.9rem",
                  fontWeight: 800,
                  color: evidence.incomplete_evidence
                    ? "var(--amber, #fbbf24)"
                    : "var(--green, #34d399)",
                }}
              >
                {evidence.incomplete_evidence}
              </div>
            </div>
            {Object.entries(evidence.by_level).map(([level, count]) => (
              <div key={level} className="card p-5">
                <span className="label">{LEVEL_LABELS[level] ?? level}</span>
                <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{count}</div>
              </div>
            ))}
          </div>

          {evidence.incomplete_evidence > 0 && (
            <div
              className="card p-4"
              style={{
                fontSize: 13,
                color: "var(--muted)",
                borderColor: "color-mix(in srgb, var(--amber, #fbbf24) 35%, var(--border))",
              }}
            >
              {evidence.incomplete_evidence} student(s) are reported with adjustments that lack a
              recorded family consultation or a review meeting. Those rows are the ones an
              auditor would question first — they are listed at the top.
            </div>
          )}

          {evidence.results.length === 0 ? (
            <Empty label="No active plans carry an adjustment level, so nothing would be reported." />
          ) : (
            <Panel pad={false}>
              {evidence.results.map((row) => (
                <div
                  key={row.student}
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
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                      {row.evidence_complete ? (
                        <ShieldCheck size={16} style={{ color: "var(--green, #34d399)" }} />
                      ) : (
                        <AlertTriangle size={16} style={{ color: "var(--amber, #fbbf24)" }} />
                      )}
                      <strong>{row.name}</strong>
                      <span className="pill" style={{ fontSize: "0.72rem" }}>
                        Year {row.year_level}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.83rem", color: "var(--muted)", marginTop: 2 }}>
                      {row.adjustment_count} adjustment(s) · {row.categories.join(", ")}
                      {row.family_consulted_on
                        ? ` · family consulted ${fmtDate(row.family_consulted_on)}`
                        : " · no family consultation recorded"}
                      {row.last_review
                        ? ` · reviewed ${fmtDate(row.last_review)}`
                        : " · no review recorded"}
                    </div>
                  </div>
                  <Badge value={LEVEL_LABELS[row.adjustment_level] ?? row.adjustment_level} />
                </div>
              ))}
            </Panel>
          )}
        </>
      )}
    </div>
  );
}
