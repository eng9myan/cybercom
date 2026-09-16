"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Circle } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";

/**
 * Rubric marking.
 *
 * The rule this screen enforces is that the score follows the criteria. There
 * is no box to type a total into — a teacher picks a level per criterion and
 * the mark falls out, which is the only version a student can be shown a
 * breakdown of without it contradicting their grade.
 *
 * The running total is computed here as well as on the server, so a teacher
 * sees what a selection costs *before* saving. The server's number is
 * authoritative and replaces it on save.
 */

type Level = {
  id: string;
  label: string;
  descriptor: string;
  marks: string;
  achievement_level: string;
  sequence: number;
};

type Criterion = {
  id: string;
  name: string;
  description: string;
  weight: string;
  sequence: number;
  levels: Level[];
};

type Rubric = {
  id: string;
  name: string;
  description: string;
  subject: string;
  year_level: number | null;
  criteria: Criterion[];
  total_marks: string;
};

type Assessment = {
  id: string;
  name: string;
  max_score: string;
  rubric: string | null;
  rubric_name: string;
  class_section_name: string;
};

type SheetRow = {
  student: string;
  name: string | null;
  score: string | null;
  achievement_level: string;
  graded: boolean;
};

type MarkResult = {
  score: string;
  achievement_level: string;
  criteria_marked: number;
  criteria_total: number;
  complete: boolean;
};

const bySequence = <T extends { sequence: number }>(rows: T[]) =>
  [...rows].sort((a, b) => a.sequence - b.sequence);

export default function RubricsPage() {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [rubric, setRubric] = useState<Rubric | null>(null);
  const [sheet, setSheet] = useState<SheetRow[]>([]);
  const [student, setStudent] = useState<string>("");
  const [selections, setSelections] = useState<Record<string, string>>({});
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  useEffect(() => {
    (async () => {
      try {
        const rows = await cyed.list<Assessment>("gradebook/assessments/");
        const marked = rows.filter((a) => a.rubric);
        setAssessments(marked);
        setAssessment(marked[0] ?? null);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load assessments");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const loadSheet = useCallback(async () => {
    if (!assessment) return;
    try {
      const [detail, marks] = await Promise.all([
        cyed.get<Rubric>(`gradebook/rubrics/${assessment.rubric}/`),
        cyed.get<{ students: SheetRow[] }>(`gradebook/assessments/${assessment.id}/mark-sheet/`),
      ]);
      setRubric(detail);
      setSheet(marks.students ?? []);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not load that rubric");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assessment]);

  useEffect(() => {
    setStudent("");
    setSelections({});
    setComment("");
    loadSheet();
  }, [loadSheet]);

  // Mirrors the server: each criterion's chosen level scaled by its weight,
  // then scaled again to the assessment's own maximum when the two differ.
  const running = useMemo(() => {
    if (!rubric) return null;
    let earned = 0;
    let possible = 0;
    for (const criterion of rubric.criteria) {
      const weight = Number(criterion.weight) || 0;
      const best = Math.max(0, ...criterion.levels.map((l) => Number(l.marks) || 0));
      possible += best * weight;
      const chosen = criterion.levels.find((l) => l.id === selections[criterion.id]);
      if (chosen) earned += (Number(chosen.marks) || 0) * weight;
    }
    const max = Number(assessment?.max_score) || 0;
    const scaled = possible && max && possible !== max ? (earned / possible) * max : earned;
    return {
      earned: Math.round(scaled * 100) / 100,
      outOf: possible && max && possible !== max ? max : possible,
      marked: Object.keys(selections).length,
      criteria: rubric.criteria.length,
    };
  }, [rubric, selections, assessment]);

  const save = async () => {
    if (!assessment || !student || Object.keys(selections).length === 0) return;
    setBusy(true);
    try {
      const result = await cyed.action<MarkResult>(
        `gradebook/assessments/${assessment.id}/rubric-mark/`,
        { student, selections, comment },
      );
      toast.push(
        `Saved — ${result.score} / ${assessment.max_score}` +
          (result.achievement_level ? ` (${result.achievement_level})` : "") +
          (result.complete ? "" : ` · ${result.criteria_marked} of ${result.criteria_total} criteria`),
      );
      setSelections({});
      setComment("");
      setStudent("");
      await loadSheet();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not save that mark");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;
  if (!assessment) {
    return (
      <div style={{ display: "grid", gap: "1.25rem" }}>
        <PageHeader title="Rubric marking" subtitle="Marks derived from criteria" />
        <Empty label="No assessment has a rubric attached yet." />
      </div>
    );
  }

  const graded = sheet.filter((r) => r.graded).length;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Rubric marking"
        subtitle={`${assessment.name}${
          assessment.class_section_name ? ` — ${assessment.class_section_name}` : ""
        }`}
        action={
          <span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
            {graded} of {sheet.length} marked
          </span>
        }
      />

      <div
        style={{
          display: "grid",
          gap: "0.9rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(15rem, 1fr))",
        }}
      >
        <Field label="Assessment">
          <select
            className="input"
            value={assessment.id}
            onChange={(e) =>
              setAssessment(assessments.find((a) => a.id === e.target.value) ?? assessment)
            }
          >
            {assessments.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
                {a.rubric_name ? ` — ${a.rubric_name}` : ""}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Student">
          <select
            className="input"
            value={student}
            onChange={(e) => {
              setStudent(e.target.value);
              // Selections belong to one script; carrying them to the next
              // student is how a whole class ends up with the same marks.
              setSelections({});
              setComment("");
            }}
          >
            <option value="">Choose…</option>
            {sheet.map((row) => (
              <option key={row.student} value={row.student}>
                {row.name ?? "Unnamed student"}
                {row.graded ? ` — ${row.score}${row.achievement_level ? ` (${row.achievement_level})` : ""}` : ""}
              </option>
            ))}
          </select>
        </Field>
      </div>

      {!student ? (
        <Empty label="Choose a student to start marking." />
      ) : (
        rubric &&
        bySequence(rubric.criteria).map((criterion) => (
          <Panel
            key={criterion.id}
            title={
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <strong style={{ fontSize: "1rem" }}>{criterion.name}</strong>
                {Number(criterion.weight) !== 1 && (
                  <span className="pill" style={{ fontSize: "0.72rem" }}>
                    ×{criterion.weight}
                  </span>
                )}
              </span>
            }
            action={
              selections[criterion.id] ? (
                <Badge value="marked" />
              ) : (
                <span style={{ fontSize: "0.8rem", color: "var(--faint)" }}>not marked</span>
              )
            }
          >
            {criterion.description && (
              <p style={{ color: "var(--muted)", fontSize: "0.87rem", marginBottom: "0.7rem" }}>
                {criterion.description}
              </p>
            )}
            <div style={{ display: "grid", gap: "0.5rem" }}>
              {bySequence(criterion.levels).map((level) => {
                const chosen = selections[criterion.id] === level.id;
                return (
                  <button
                    key={level.id}
                    type="button"
                    onClick={() =>
                      setSelections((current) => {
                        // Clicking the chosen level again clears it, so a
                        // misclick does not force a whole re-mark.
                        const next = { ...current };
                        if (chosen) delete next[criterion.id];
                        else next[criterion.id] = level.id;
                        return next;
                      })
                    }
                    style={{
                      textAlign: "left",
                      display: "flex",
                      gap: "0.7rem",
                      alignItems: "flex-start",
                      padding: "0.7rem 0.9rem",
                      borderRadius: 12,
                      cursor: "pointer",
                      border: `1px solid ${chosen ? "var(--cyan)" : "var(--border)"}`,
                      background: chosen
                        ? "color-mix(in srgb, var(--cyan) 12%, transparent)"
                        : "transparent",
                      color: "inherit",
                      font: "inherit",
                    }}
                  >
                    {chosen ? (
                      <CheckCircle2 size={17} style={{ color: "var(--cyan)", flexShrink: 0 }} />
                    ) : (
                      <Circle size={17} style={{ color: "var(--faint)", flexShrink: 0 }} />
                    )}
                    <span style={{ display: "grid", gap: 2 }}>
                      <span style={{ fontWeight: 600 }}>
                        {level.label} · {level.marks}
                        {level.achievement_level && ` · ${level.achievement_level}`}
                      </span>
                      {/* The descriptor is the standard; hiding it behind a
                          tooltip is how two teachers mark differently. */}
                      <span style={{ fontSize: "0.86rem", color: "var(--muted)", lineHeight: 1.5 }}>
                        {level.descriptor}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>
          </Panel>
        ))
      )}

      {student && running && (
        <Panel title="Result">
          <div style={{ display: "grid", gap: "0.8rem" }}>
            <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", alignItems: "baseline" }}>
              <div style={{ fontSize: "2rem", fontWeight: 800 }}>
                {running.earned}
                <span style={{ fontSize: "1rem", color: "var(--muted)" }}> / {running.outOf}</span>
              </div>
              <span style={{ color: "var(--muted)", fontSize: "0.87rem" }}>
                {running.marked} of {running.criteria} criteria marked
                {running.marked < running.criteria &&
                  " — unmarked criteria score nothing until you come back to them"}
              </span>
            </div>
            <Field label="Comment to the student (optional)">
              <textarea
                className="input"
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                style={{ width: "100%", resize: "vertical" }}
              />
            </Field>
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                className="btn btn-primary"
                disabled={busy || running.marked === 0}
                onClick={save}
              >
                Save mark
              </button>
            </div>
          </div>
        </Panel>
      )}
    </div>
  );
}
