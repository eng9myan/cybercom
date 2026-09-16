"use client";

import { useEffect, useMemo, useState } from "react";
import { GraduationCap, ClipboardList, Tag } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Field, SkeletonRows } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { Assessment, ClassSection } from "@/lib/types";

export default function GradebookPage() {
  const [rows, setRows] = useState<Assessment[]>([]);
  const [sections, setSections] = useState<ClassSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sectionId, setSectionId] = useState("");
  const [name, setName] = useState("");
  const [maxScore, setMaxScore] = useState("100");
  const [code, setCode] = useState("");
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [assessments, secs] = await Promise.all([
        cyed.list<Assessment>("gradebook/assessments/"),
        cyed.list<ClassSection>("sis/class-sections/"),
      ]);
      setRows(assessments);
      setSections(secs);
      if (!sectionId && secs.length) setSectionId(secs[0].id);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load gradebook");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stats = useMemo(() => {
    const coded = rows.filter((a) => a.curriculum_code).length;
    return { total: rows.length, coded, classes: new Set(rows.map((a) => a.class_section_name)).size };
  }, [rows]);

  const addAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sectionId || !name) return;
    setSaving(true);
    try {
      await cyed.create("gradebook/assessments/", { class_section: sectionId, name, max_score: maxScore, curriculum_code: code });
      setName("");
      setCode("");
      toast.push(`Assessment “${name}” added`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Failed to create assessment", "bad");
    } finally {
      setSaving(false);
    }
  };

  const columns: Column<Assessment>[] = [
    { key: "name", header: "Assessment", render: (a) => <span style={{ fontWeight: 600 }}>{a.name}</span> },
    { key: "class", header: "Class", render: (a) => <span style={{ color: "var(--muted)" }}>{a.class_section_name || "—"}</span> },
    { key: "type", header: "Type", render: (a) => a.assessment_type, width: 110 },
    { key: "max", header: "Max", render: (a) => a.max_score, width: 70, align: "right" },
    { key: "acara", header: "ACARA", render: (a) => (a.curriculum_code ? <span className="pill">{a.curriculum_code}</span> : "—"), width: 120 },
  ];

  return (
    <div>
      <PageHeader title="Gradebook" subtitle="Assessments mapped to ACARA codes" />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Assessments" value={stats.total} accent="cyan" icon={<ClipboardList size={17} />} />
        <StatCard label="ACARA-coded" value={stats.coded} accent="violet" icon={<Tag size={17} />} />
        <StatCard label="Classes covered" value={stats.classes} accent="blue" icon={<GraduationCap size={17} />} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
        <Panel title={<div className="flex items-center gap-2"><GraduationCap size={15} style={{ color: "var(--cyan)" }} /><span className="label">New assessment</span></div>}>
          <form onSubmit={addAssessment} className="space-y-3">
            <Field label="Class section">
              <select className="input" value={sectionId} onChange={(e) => setSectionId(e.target.value)}>
                {sections.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Name">
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
            </Field>
            <Field label="Max score">
              <input className="input" type="number" value={maxScore} onChange={(e) => setMaxScore(e.target.value)} />
            </Field>
            <Field label="ACARA code (optional)">
              <input className="input" placeholder="AC9M8N01" value={code} onChange={(e) => setCode(e.target.value)} />
            </Field>
            <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} type="submit" disabled={!sections.length || saving}>
              {saving ? "Adding…" : "Add assessment"}
            </button>
          </form>
        </Panel>

        {loading ? (
          <SkeletonRows rows={6} />
        ) : error ? (
          <ErrorNote error={error} />
        ) : (
          <DataTable columns={columns} rows={rows} filterKeys={["name", "class_section_name", "curriculum_code"]} emptyLabel="No assessments yet." />
        )}
      </div>
    </div>
  );
}
