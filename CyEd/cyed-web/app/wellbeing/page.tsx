"use client";

import { useEffect, useMemo, useState } from "react";
import { HeartPulse, Languages, Brain } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Field, SkeletonRows } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { LearnerProfile, Student } from "@/lib/types";

const EALD = [
  { v: "", l: "Not EAL/D" },
  { v: "BL", l: "Beginning" },
  { v: "EM", l: "Emerging" },
  { v: "DV", l: "Developing" },
  { v: "CO", l: "Consolidating" },
];

export default function WellbeingPage() {
  const [rows, setRows] = useState<LearnerProfile[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [studentId, setStudentId] = useState("");
  const [eald, setEald] = useState("");
  const [firstLang, setFirstLang] = useState("");
  const [neuro, setNeuro] = useState(false);
  const [accom, setAccom] = useState("");
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [profiles, studs] = await Promise.all([
        cyed.list<LearnerProfile>("wellbeing/learner-profiles/"),
        cyed.list<Student>("sis/students/"),
      ]);
      setRows(profiles);
      setStudents(studs);
      if (!studentId && studs.length) setStudentId(studs[0].id);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load wellbeing");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const studentName = (id: string) => {
    const s = students.find((x) => x.id === id);
    return s ? `${s.first_name} ${s.last_name}` : "—";
  };

  const stats = useMemo(() => ({
    total: rows.length,
    eald: rows.filter((p) => p.eald_level).length,
    neuro: rows.filter((p) => p.is_neurodivergent).length,
  }), [rows]);

  const addProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId) return;
    setSaving(true);
    try {
      await cyed.create("wellbeing/learner-profiles/", {
        student: studentId, eald_level: eald, first_language: firstLang,
        is_neurodivergent: neuro, accommodations: accom,
      });
      setAccom("");
      toast.push("Learner profile saved");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Failed (one profile per student)", "bad");
    } finally {
      setSaving(false);
    }
  };

  const columns: Column<LearnerProfile>[] = [
    { key: "student", header: "Student", render: (p) => <span style={{ fontWeight: 600 }}>{studentName(p.student)}</span> },
    { key: "eald", header: "EAL/D", render: (p) => (p.eald_level ? <span className="pill">{p.eald_level}</span> : "—"), width: 100 },
    { key: "lang", header: "First language", render: (p) => <span style={{ color: "var(--muted)" }}>{p.first_language || "—"}</span> },
    { key: "neuro", header: "Neurodivergent", render: (p) => (p.is_neurodivergent ? <span className="status status-warn">yes · accommodations</span> : <span style={{ color: "var(--faint)" }}>no</span>), width: 200 },
  ];

  return (
    <div>
      <PageHeader title="Wellbeing & Support" subtitle="Learner profiles drive the adaptive AI (EAL/D, neurodivergent accommodations)" />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Learner profiles" value={stats.total} accent="cyan" icon={<HeartPulse size={17} />} />
        <StatCard label="EAL/D learners" value={stats.eald} accent="blue" icon={<Languages size={17} />} />
        <StatCard label="Neurodivergent" value={stats.neuro} accent="violet" icon={<Brain size={17} />} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 20, alignItems: "start" }}>
        <Panel title={<div className="flex items-center gap-2"><HeartPulse size={15} style={{ color: "var(--cyan)" }} /><span className="label">New learner profile</span></div>}>
          <form onSubmit={addProfile} className="space-y-3">
            <Field label="Student">
              <select className="input" value={studentId} onChange={(e) => setStudentId(e.target.value)}>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>
                ))}
              </select>
            </Field>
            <Field label="EAL/D level">
              <select className="input" value={eald} onChange={(e) => setEald(e.target.value)}>
                {EALD.map((o) => <option key={o.v} value={o.v}>{o.l}</option>)}
              </select>
            </Field>
            <Field label="First language">
              <input className="input" value={firstLang} onChange={(e) => setFirstLang(e.target.value)} />
            </Field>
            <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: "0.82rem" }}>
              <input type="checkbox" checked={neuro} onChange={(e) => setNeuro(e.target.checked)} />
              Neurodivergent (accommodations apply)
            </label>
            <Field label="Accommodations">
              <input className="input" value={accom} onChange={(e) => setAccom(e.target.value)} placeholder="Extra time; chunked tasks" />
            </Field>
            <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} type="submit" disabled={!students.length || saving}>
              {saving ? "Saving…" : "Save profile"}
            </button>
          </form>
        </Panel>

        {loading ? (
          <SkeletonRows rows={6} />
        ) : error ? (
          <ErrorNote error={error} />
        ) : (
          <DataTable columns={columns} rows={rows} emptyLabel="No learner profiles yet." />
        )}
      </div>
    </div>
  );
}
