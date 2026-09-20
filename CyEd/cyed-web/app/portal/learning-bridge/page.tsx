"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, BookOpenCheck, Clock, Download, GraduationCap } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { PersonSwitcher } from "@/app/portal/_parts";
import { fmtDateTime, useMyChildren, type LearningBridgeSummary } from "@/lib/portal";

/**
 * School-Home Learning Bridge.
 *
 * Deliberately not a new system: missed/upcoming work and learning progress
 * are the same assignment/gradebook data already powering the student and
 * staff screens, just composed for a family view (see
 * products/cyed/learning_bridge/services.py). The two genuinely new things
 * here are teacher-curated family resources and offline activity packs.
 */
export default function LearningBridgePage() {
  const { children, selected, setSelected, loading: childrenLoading, error: childrenError } = useMyChildren();
  const [summary, setSummary] = useState<LearningBridgeSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    cyed
      .get<LearningBridgeSummary>(`learning-bridge/summary/?student=${selected}`)
      .then((data) => {
        setSummary(data);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load the Learning Bridge"))
      .finally(() => setLoading(false));
  }, [selected]);

  if (childrenLoading) return <SkeletonRows rows={6} />;
  if (childrenError) return <ErrorNote error={childrenError} />;
  if (!children.length) {
    return <Empty label="No children are linked to this account yet. Contact the school office." />;
  }

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Learning Bridge"
        subtitle="Learning targets, progress, and ways to help at home"
      />

      <PersonSwitcher people={children} value={selected} onChange={setSelected} label="Viewing" />

      {loading ? (
        <SkeletonRows rows={5} />
      ) : error ? (
        <ErrorNote error={error} />
      ) : !summary ? null : (
        <>
          {summary.missed_assignments.length > 0 && (
            <Panel
              title={
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--red, #f87171)" }}>
                  <AlertTriangle size={16} />
                  <span className="label">Missed work</span>
                </div>
              }
            >
              {summary.missed_assignments.map((a) => (
                <div key={a.id} style={{ display: "flex", justifyContent: "space-between", padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{a.title}</div>
                    <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{a.class_section}</div>
                  </div>
                  <span style={{ fontSize: "0.8rem", color: "var(--red, #f87171)" }}>Was due {fmtDateTime(a.due_at)}</span>
                </div>
              ))}
            </Panel>
          )}

          <Panel
            title={
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Clock size={16} />
                <span className="label">Upcoming</span>
              </div>
            }
          >
            {summary.upcoming_assignments.length === 0 ? (
              <Empty label="Nothing due in the next two weeks." />
            ) : (
              summary.upcoming_assignments.map((a) => (
                <div key={a.id} style={{ display: "flex", justifyContent: "space-between", padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{a.title}</div>
                    <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{a.class_section}</div>
                  </div>
                  <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>Due {fmtDateTime(a.due_at)}</span>
                </div>
              ))
            )}
          </Panel>

          <Panel
            title={
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <GraduationCap size={16} />
                <span className="label">Recent progress</span>
              </div>
            }
          >
            {summary.learning_progress.length === 0 ? (
              <Empty label="No recent results yet." />
            ) : (
              summary.learning_progress.map((r, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{r.assessment}</div>
                    <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                      {r.class_section}{r.curriculum_code ? ` · ${r.curriculum_code}` : ""}
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                    {r.achievement_level && <Badge value={r.achievement_level} />}
                    {r.score !== null && <strong>{r.score}/{r.max_score}</strong>}
                  </div>
                </div>
              ))
            )}
          </Panel>

          <Panel
            title={
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <BookOpenCheck size={16} />
                <span className="label">Family resources</span>
              </div>
            }
          >
            {summary.resources.length === 0 ? (
              <Empty label="No resources published for this year level yet." />
            ) : (
              summary.resources.map((r) => (
                <div key={r.id} style={{ padding: "0.6rem 0", borderBottom: "1px solid var(--border)" }}>
                  <div style={{ fontWeight: 600 }}>{r.title}</div>
                  {r.subject && <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>{r.subject}</div>}
                  {r.description && <p style={{ fontSize: "0.85rem", margin: "0.35rem 0" }}>{r.description}</p>}
                  {r.external_url && (
                    <a href={r.external_url} target="_blank" rel="noreferrer" style={{ fontSize: "0.85rem" }}>
                      Open resource →
                    </a>
                  )}
                </div>
              ))
            )}
          </Panel>

          <Panel
            title={
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Download size={16} />
                <span className="label">Offline activity packs</span>
              </div>
            }
          >
            {summary.offline_packs.length === 0 ? (
              <Empty label="No offline packs available for this year level yet." />
            ) : (
              summary.offline_packs.map((p) => (
                <details key={p.id} style={{ padding: "0.6rem 0", borderBottom: "1px solid var(--border)" }}>
                  <summary style={{ cursor: "pointer", fontWeight: 600 }}>
                    {p.title}{p.subject ? ` — ${p.subject}` : ""}
                  </summary>
                  {p.description && <p style={{ fontSize: "0.85rem", marginTop: "0.4rem" }}>{p.description}</p>}
                  {p.content && (
                    <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem", marginTop: "0.4rem", fontFamily: "inherit" }}>
                      {p.content}
                    </pre>
                  )}
                </details>
              ))
            )}
          </Panel>
        </>
      )}
    </div>
  );
}
