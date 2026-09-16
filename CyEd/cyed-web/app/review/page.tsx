"use client";

import { useEffect, useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, Loading, ErrorNote, Empty } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { IconBadge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { GeneratedArtifact, IntegrityReview } from "@/lib/types";
import { Wand2, ShieldAlert, Check, X, TriangleAlert } from "lucide-react";

export default function ReviewPage() {
  const [artifacts, setArtifacts] = useState<GeneratedArtifact[]>([]);
  const [reviews, setReviews] = useState<IntegrityReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [arts, revs] = await Promise.all([
        cyed.list<GeneratedArtifact>("ai/artifacts/?status=pending_review"),
        cyed.list<IntegrityReview>("ai/integrity/reviews/?decision=pending"),
      ]);
      setArtifacts(arts);
      setReviews(revs);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load review queue");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const decideArtifact = async (id: string, verb: "approve" | "reject") => {
    try {
      await cyed.action(`ai/artifacts/${id}/${verb}/`, {});
      toast.push(verb === "approve" ? "Draft approved" : "Draft rejected", verb === "approve" ? "ok" : "bad");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Action failed", "bad");
    }
  };

  const decideReview = async (id: string, decision: string) => {
    try {
      await cyed.action(`ai/integrity/reviews/${id}/decide/`, { decision });
      toast.push(`Recorded: ${decision}`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Decision failed", "bad");
    }
  };

  if (loading) return <Loading label="Loading review queue…" />;

  return (
    <div>
      <PageHeader title="Human-in-the-Loop Review" subtitle="Every AI draft and integrity flag needs a human decision." />
      {error && <ErrorNote error={error} />}

      <div className="grid gap-4 stagger mb-6" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))" }}>
        <StatCard label="AI drafts pending" value={artifacts.length} accent="violet" icon={<Wand2 size={17} />} />
        <StatCard label="Integrity cases open" value={reviews.length} accent="cyan" icon={<ShieldAlert size={17} />} />
      </div>

      <h2 className="label" style={{ margin: "8px 0 12px" }}>AI drafts pending approval</h2>
      {artifacts.length === 0 ? (
        <Empty label="No AI drafts awaiting review." />
      ) : (
        <div className="space-y-3 stagger">
          {artifacts.map((a) => (
            <div key={a.id} className="card card-hover p-4">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                  <IconBadge color="var(--violet)"><Wand2 size={16} /></IconBadge>
                  <div>
                    <div className="font-semibold">{a.title}</div>
                    <div style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 4 }}>
                      <span className="pill" style={{ textTransform: "capitalize" }}>{a.artifact_type.replace("_", " ")}</span>
                      {a.curriculum_codes && <span className="pill grad-text" style={{ fontWeight: 700 }}>{a.curriculum_codes}</span>}
                      {a.llm_generated && <span className="pill">LLM</span>}
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                  <button className="btn btn-primary" onClick={() => decideArtifact(a.id, "approve")}><Check size={14} /> Approve</button>
                  <button className="btn btn-ghost" onClick={() => decideArtifact(a.id, "reject")}><X size={14} /> Reject</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <h2 className="label" style={{ margin: "26px 0 12px" }}>Academic integrity — awaiting human decision</h2>
      {reviews.length === 0 ? (
        <Empty label="No integrity reviews open." />
      ) : (
        <div className="space-y-3 stagger">
          {reviews.map((r) => (
            <div key={r.id} className="card card-hover p-4">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                  <IconBadge color={r.risk_band === "high" ? "var(--bad)" : "var(--warn)"}><TriangleAlert size={16} /></IconBadge>
                  <div>
                    <div className="font-semibold">{r.title}</div>
                    <div style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 4 }}>
                      <span className={`status ${r.risk_band === "high" ? "status-bad" : "status-warn"}`} style={{ textTransform: "capitalize" }}>
                        {r.risk_band} risk · advisory
                      </span>
                      {r.disclosed_ai_use && <span className="pill">AI disclosed</span>}
                    </div>
                    <div className="text-xs mt-1" style={{ color: "var(--muted)" }}>
                      {r.draft_versions} drafts · {r.edit_span_minutes} min edit span
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                  <button className="btn btn-primary" onClick={() => decideReview(r.id, "cleared")}>Clear</button>
                  <button className="btn btn-ghost" onClick={() => decideReview(r.id, "concern")}>Note concern</button>
                  <button className="btn btn-ghost" onClick={() => decideReview(r.id, "escalated")}>Escalate</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
