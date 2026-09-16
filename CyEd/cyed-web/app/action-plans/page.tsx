"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Search } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";

/**
 * Medical action plans — anaphylaxis, asthma, diabetes, seizure.
 *
 * Optimised for retrieval under pressure. A teacher opening this has a child in
 * front of them, so: search is the first thing on the page and focused on load,
 * the steps are shown in full without expanding anything, and where the
 * medication is kept sits next to what it is.
 *
 * Expired plans are shown with a warning rather than filtered out. A lapsed
 * anaphylaxis plan is the most important row on the page — the reaction does
 * not wait for the paperwork.
 */

type Plan = {
  plan: string;
  student: string;
  name: string;
  year_level: number;
  plan_type: string;
  plan_type_display: string;
  severity: string;
  triggers: string;
  emergency_steps: string;
  medication: string;
  medication_location: string;
  status: string;
  review_due: string | null;
};

export default function ActionPlansPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [view, setView] = useState<"critical" | "review">("critical");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    (async () => {
      try {
        const path =
          view === "critical"
            ? "health/action-plans/critical/"
            : "health/action-plans/needing-review/";
        const data = await cyed.get<{ results: Plan[] }>(path);
        setPlans(data.results ?? []);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load action plans");
      } finally {
        setLoading(false);
      }
    })();
  }, [view]);

  const shown = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return plans;
    return plans.filter(
      (p) =>
        p.name.toLowerCase().includes(needle) ||
        p.plan_type_display.toLowerCase().includes(needle) ||
        p.triggers.toLowerCase().includes(needle),
    );
  }, [plans, query]);

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Action plans"
        subtitle="Emergency medical plans"
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "critical", label: "Current" },
              { value: "review", label: "Needs review" },
            ]}
          />
        }
      />

      <div style={{ position: "relative" }}>
        <Search
          size={16}
          style={{
            position: "absolute",
            left: 12,
            top: "50%",
            transform: "translateY(-50%)",
            color: "var(--muted)",
          }}
        />
        {/* Focused on load: the first thing a teacher does here is type a name. */}
        <input
          className="input"
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by student, condition or trigger…"
          style={{ width: "100%", paddingLeft: 36 }}
        />
      </div>

      {shown.length === 0 ? (
        <Empty
          label={
            view === "critical"
              ? "No life-threatening action plans are recorded."
              : "Every plan is current."
          }
        />
      ) : (
        shown.map((plan) => {
          const lapsed = plan.status === "expired";
          return (
            <Panel
              key={plan.plan}
              title={
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  {lapsed && <AlertTriangle size={16} style={{ color: "var(--red, #f87171)" }} />}
                  <strong style={{ fontSize: "1rem" }}>{plan.name}</strong>
                  <span className="pill" style={{ fontSize: "0.72rem" }}>
                    Year {plan.year_level}
                  </span>
                </span>
              }
              action={
                <span style={{ display: "flex", gap: "0.4rem", alignItems: "center" }}>
                  <Badge value={plan.severity} />
                  <Badge value={plan.status} />
                </span>
              }
              className={lapsed ? "card-hover" : undefined}
            >
              <div style={{ display: "grid", gap: "0.75rem" }}>
                <div>
                  <span className="label">{plan.plan_type_display}</span>
                  {plan.triggers && (
                    <div style={{ marginTop: 2 }}>
                      Triggered by: <strong>{plan.triggers}</strong>
                    </div>
                  )}
                </div>

                <div
                  style={{
                    background: "var(--panel-2)",
                    border: "1px solid var(--border)",
                    borderRadius: 12,
                    padding: "0.8rem 1rem",
                  }}
                >
                  <div className="label" style={{ marginBottom: 6 }}>
                    What to do
                  </div>
                  {/* Whitespace preserved: these are numbered steps read aloud. */}
                  <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6, fontSize: "1rem" }}>
                    {plan.emergency_steps}
                  </div>
                </div>

                {plan.medication && (
                  <div>
                    <span className="label">Medication</span>
                    <div style={{ marginTop: 2 }}>
                      <strong>{plan.medication}</strong>
                      {plan.medication_location && (
                        <span style={{ color: "var(--muted)" }}> — {plan.medication_location}</span>
                      )}
                    </div>
                  </div>
                )}

                {lapsed && (
                  <div style={{ color: "var(--red, #f87171)", fontSize: "0.85rem" }}>
                    This plan was due for review on {plan.review_due}. Follow it, and ask the
                    office to get an updated one from the family.
                  </div>
                )}
              </div>
            </Panel>
          );
        })
      )}
    </div>
  );
}
