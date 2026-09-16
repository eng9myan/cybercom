"use client";

import { useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Field } from "@/components/ui";
import { Badge, IconBadge } from "@/components/kit";
import type { SocraticResult } from "@/lib/types";
import { Compass, HelpCircle } from "lucide-react";

export default function StudyBuddyPage() {
  const [question, setQuestion] = useState("");
  const [yearLevel, setYearLevel] = useState("8");
  const [result, setResult] = useState<SocraticResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await cyed.action<SocraticResult>("ai/tutor/socratic/", { question, year_level: parseInt(yearLevel) || undefined }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 780 }}>
      <PageHeader
        title="Study Buddy (Socratic)"
        subtitle="Guides you with questions — never gives the answer. Curriculum-grounded, privacy-safe."
      />

      <form
        onSubmit={ask}
        className="card p-5 mb-5 anim-fade-up"
        style={{ boxShadow: "var(--shadow), var(--glow-violet)", borderColor: "color-mix(in srgb, var(--violet) 30%, var(--border))" }}
      >
        <div className="flex items-center gap-3 mb-4">
          <IconBadge color="var(--violet)"><Compass size={18} /></IconBadge>
          <div>
            <div style={{ fontWeight: 700 }}>What are you stuck on?</div>
            <div style={{ fontSize: 12, color: "var(--muted)" }}>I ask the questions — you find the answer</div>
          </div>
        </div>
        <Field label="Your sticking point">
          <textarea className="input" rows={3} value={question} onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. I don't get irrational numbers" />
        </Field>
        <div style={{ display: "flex", gap: 12, alignItems: "end", marginTop: 12 }}>
          <div style={{ width: 120 }}>
            <Field label="Year level">
              <input className="input" type="number" min={0} max={12} value={yearLevel} onChange={(e) => setYearLevel(e.target.value)} />
            </Field>
          </div>
          <button className="btn btn-violet" type="submit" disabled={loading}>
            <Compass size={14} /> {loading ? "Thinking…" : "Guide me"}
          </button>
        </div>
      </form>

      {error && <ErrorNote error={error} />}

      {result && (
        <div className="card p-5 space-y-3 anim-fade-up">
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <span className="status status-warn">answer withheld — I only guide</span>
            <Badge value={result.grounded ? "curriculum grounded" : "out of curriculum"} />
          </div>
          <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>{result.response}</p>
          {result.guiding_questions.length > 0 && (
            <div>
              <div className="label" style={{ marginBottom: 8 }}>Think about</div>
              <div className="space-y-2">
                {result.guiding_questions.map((q, i) => (
                  <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start", fontSize: "0.88rem" }}>
                    <HelpCircle size={15} style={{ color: "var(--violet)", flexShrink: 0, marginTop: 2 }} />
                    <span>{q}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {result.citations.length > 0 && (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {result.citations.map((c) => (
                <span key={c.code} className="pill grad-text" style={{ fontWeight: 700 }}>{c.code}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
