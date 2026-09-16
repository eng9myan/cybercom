"use client";

import { useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Field } from "@/components/ui";
import { Badge, IconBadge } from "@/components/kit";
import type { TutorResult } from "@/lib/types";
import { Sparkles, ShieldCheck } from "lucide-react";

export default function TutorPage() {
  const [question, setQuestion] = useState("");
  const [yearLevel, setYearLevel] = useState("8");
  const [result, setResult] = useState<TutorResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await cyed.action<TutorResult>("ai/tutor/ask/", { question, year_level: parseInt(yearLevel) || undefined }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Tutor request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 780 }}>
      <PageHeader
        title="Curriculum-Aligned AI Tutor"
        subtitle="Grounded in the Australian Curriculum. Off-syllabus questions are declined."
      />

      <form
        onSubmit={ask}
        className="card p-5 mb-5 anim-fade-up"
        style={{ boxShadow: "var(--shadow), var(--glow)", borderColor: "color-mix(in srgb, var(--cyan) 30%, var(--border))" }}
      >
        <div className="flex items-center gap-3 mb-4">
          <IconBadge color="var(--cyan)"><Sparkles size={18} /></IconBadge>
          <div>
            <div style={{ fontWeight: 700 }}>Ask the tutor</div>
            <div style={{ fontSize: 12, color: "var(--muted)" }}>Grounded + cited · never trained on your input</div>
          </div>
        </div>
        <Field label="Question">
          <textarea className="input" rows={3} value={question} onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. Can you explain irrational numbers?" />
        </Field>
        <div style={{ display: "flex", gap: 12, alignItems: "end", marginTop: 12 }}>
          <div style={{ width: 120 }}>
            <Field label="Year level">
              <input className="input" type="number" min={0} max={12} value={yearLevel} onChange={(e) => setYearLevel(e.target.value)} />
            </Field>
          </div>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            <Sparkles size={14} /> {loading ? "Thinking…" : "Ask tutor"}
          </button>
        </div>
      </form>

      {error && <ErrorNote error={error} />}

      {loading && (
        <div className="card p-5 space-y-3">
          <div className="skeleton" style={{ height: 14, width: "40%" }} />
          <div className="skeleton" style={{ height: 12, width: "90%" }} />
          <div className="skeleton" style={{ height: 12, width: "80%" }} />
          <div className="skeleton" style={{ height: 12, width: "60%" }} />
        </div>
      )}

      {result && (
        <div className="card p-5 space-y-3 anim-fade-up">
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <Badge value={result.grounded ? "curriculum grounded" : "out of curriculum"} />
            {result.adaptations.map((a) => (
              <span key={a} className="pill">{a}</span>
            ))}
          </div>
          <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>{result.answer}</p>
          {result.citations.length > 0 && (
            <div>
              <div className="label" style={{ marginBottom: 6 }}>Citations</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {result.citations.map((c) => (
                  <span key={c.code} className="pill grad-text" style={{ fontWeight: 700 }}>
                    {c.code} · {c.learning_area} Y{c.year_level}
                  </span>
                ))}
              </div>
            </div>
          )}
          <div className="text-xs flex items-center gap-1" style={{ color: "var(--muted)" }}>
            <ShieldCheck size={12} /> Privacy-first: your input is never used for model training. Teacher-reviewable.
          </div>
        </div>
      )}
    </div>
  );
}
