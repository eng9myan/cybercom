"use client";

import { useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Field } from "@/components/ui";
import { Segmented, Badge, IconBadge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { GeneratedArtifact } from "@/lib/types";
import { Wand2 } from "lucide-react";

type ToolKey = "lesson" | "rubric" | "diff";
type Tool = { key: ToolKey; label: string; endpoint: string; inputLabel: string; field: string };

const TOOLS: Record<ToolKey, Tool> = {
  lesson: { key: "lesson", label: "Lesson Plan", endpoint: "ai/lesson-planner/generate/", inputLabel: "Topic", field: "topic" },
  rubric: { key: "rubric", label: "Rubric", endpoint: "ai/rubric/generate/", inputLabel: "Assessment title", field: "assessment_title" },
  diff: { key: "diff", label: "Differentiated Task", endpoint: "ai/differentiator/generate/", inputLabel: "Topic", field: "topic" },
};

export default function TeacherToolsPage() {
  const [toolKey, setToolKey] = useState<ToolKey>("lesson");
  const [text, setText] = useState("irrational numbers");
  const [yearLevel, setYearLevel] = useState("8");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GeneratedArtifact | null>(null);
  const toast = useToast();
  const tool = TOOLS[toolKey];

  const generate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const body: Record<string, unknown> = { year_level: parseInt(yearLevel) || undefined };
      body[tool.field] = text;
      const art = await cyed.action<GeneratedArtifact>(tool.endpoint, body);
      setResult(art);
      toast.push(`${tool.label} generated → sent to Review Queue`);
    } catch (e) {
      const m = e instanceof Error ? e.message : "Generation failed";
      setError(m);
      toast.push(m, "bad");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 840 }}>
      <PageHeader
        title="Teacher Tools"
        subtitle="ACARA-grounded generation. Every draft goes to the review queue for approval."
      />

      <form
        onSubmit={generate}
        className="card p-5 mb-5 anim-fade-up"
        style={{ boxShadow: "var(--shadow), var(--glow-violet)", borderColor: "color-mix(in srgb, var(--violet) 28%, var(--border))" }}
      >
        <div className="flex items-center gap-3 mb-4">
          <IconBadge color="var(--violet)"><Wand2 size={18} /></IconBadge>
          <Segmented
            value={toolKey}
            onChange={(v) => { setToolKey(v); setResult(null); }}
            options={Object.values(TOOLS).map((t) => ({ value: t.key, label: t.label }))}
          />
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "end" }}>
          <div style={{ flex: 1 }}>
            <Field label={tool.inputLabel}>
              <input className="input" value={text} onChange={(e) => setText(e.target.value)} required />
            </Field>
          </div>
          <div style={{ width: 110 }}>
            <Field label="Year level">
              <input className="input" type="number" min={0} max={12} value={yearLevel} onChange={(e) => setYearLevel(e.target.value)} />
            </Field>
          </div>
          <button className="btn btn-violet" type="submit" disabled={loading}>
            <Wand2 size={14} /> {loading ? "Generating…" : "Generate"}
          </button>
        </div>
      </form>

      {error && <ErrorNote error={error} />}

      {loading && (
        <div className="card p-5 space-y-3">
          <div className="skeleton" style={{ height: 14, width: "45%" }} />
          <div className="skeleton" style={{ height: 120, width: "100%" }} />
        </div>
      )}

      {result && (
        <div className="card p-5 space-y-3 anim-fade-up">
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <span className="pill" style={{ textTransform: "capitalize" }}>{result.artifact_type.replace("_", " ")}</span>
            {result.curriculum_codes && <span className="pill grad-text" style={{ fontWeight: 700 }}>{result.curriculum_codes}</span>}
            <Badge value={result.status} />
          </div>
          <div className="font-semibold text-lg">{result.title}</div>
          <pre
            style={{
              whiteSpace: "pre-wrap", fontSize: "0.78rem", color: "var(--muted)", background: "var(--panel-2)",
              border: "1px solid var(--border)", borderRadius: 10, padding: 12, maxHeight: 340, overflow: "auto",
            }}
          >
            {JSON.stringify(result.content, null, 2)}
          </pre>
          <div className="text-xs" style={{ color: "var(--muted)" }}>
            Sent to the Review Queue — a teacher must approve it before use.
          </div>
        </div>
      )}
    </div>
  );
}
