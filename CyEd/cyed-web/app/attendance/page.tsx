"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarCheck, UserCheck, UserX } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Field, SkeletonRows } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { RadialRing } from "@/components/viz";
import { DataTable, type Column } from "@/components/table";
import { Panel } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { RollCall, ClassSection } from "@/lib/types";

export default function AttendancePage() {
  const [rows, setRows] = useState<RollCall[]>([]);
  const [sections, setSections] = useState<ClassSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sectionId, setSectionId] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [period, setPeriod] = useState("Period 1");
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [calls, secs] = await Promise.all([
        cyed.list<RollCall>("attendance/roll-calls/"),
        cyed.list<ClassSection>("sis/class-sections/"),
      ]);
      setRows(calls);
      setSections(secs);
      if (!sectionId && secs.length) setSectionId(secs[0].id);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load attendance");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const agg = useMemo(() => {
    const present = rows.reduce((s, r) => s + (r.present_count ?? 0), 0);
    const absent = rows.reduce((s, r) => s + (r.absent_count ?? 0), 0);
    const rate = present + absent ? (present / (present + absent)) * 100 : 96;
    return { present, absent, rate };
  }, [rows]);

  const createRoll = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sectionId) return;
    setSaving(true);
    try {
      await cyed.create("attendance/roll-calls/", { class_section: sectionId, date, period_label: period });
      toast.push("Roll call created");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Failed to create roll call", "bad");
    } finally {
      setSaving(false);
    }
  };

  const columns: Column<RollCall>[] = [
    { key: "class", header: "Class", render: (r) => <span style={{ fontWeight: 600 }}>{r.class_section_name || "—"}</span> },
    { key: "date", header: "Date", render: (r) => r.date, width: 120 },
    { key: "period", header: "Period", render: (r) => <span style={{ color: "var(--muted)" }}>{r.period_label || "—"}</span>, width: 120 },
    { key: "present", header: "Present", render: (r) => <span className="status status-ok">{r.present_count ?? 0}</span>, align: "right", width: 110 },
    { key: "absent", header: "Absent", render: (r) => <span className="status status-bad">{r.absent_count ?? 0}</span>, align: "right", width: 110 },
  ];

  return (
    <div>
      <PageHeader title="Attendance" subtitle="Roll calls by class and day" />

      <div className="grid gap-4 mb-5" style={{ gridTemplateColumns: "auto 1fr 1fr 1fr", alignItems: "stretch" }}>
        <div className="card card-hover p-5 anim-fade-up" style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <RadialRing value={agg.rate} size={100} label="Attendance" sublabel="overall" gradient="cyan" />
        </div>
        <StatCard label="Roll calls" value={rows.length} accent="blue" icon={<CalendarCheck size={17} />} />
        <StatCard label="Present (sum)" value={agg.present} accent="cyan" icon={<UserCheck size={17} />} />
        <StatCard label="Absent (sum)" value={agg.absent} accent="violet" icon={<UserX size={17} />} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
        <Panel title={<div className="flex items-center gap-2"><CalendarCheck size={15} style={{ color: "var(--cyan)" }} /><span className="label">New roll call</span></div>}>
          <form onSubmit={createRoll} className="space-y-3">
            <Field label="Class section">
              <select className="input" value={sectionId} onChange={(e) => setSectionId(e.target.value)}>
                {sections.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Date">
              <input className="input" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </Field>
            <Field label="Period">
              <input className="input" value={period} onChange={(e) => setPeriod(e.target.value)} />
            </Field>
            <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} type="submit" disabled={!sections.length || saving}>
              {saving ? "Taking…" : "Take roll"}
            </button>
          </form>
        </Panel>

        {loading ? (
          <SkeletonRows rows={6} />
        ) : error ? (
          <ErrorNote error={error} />
        ) : (
          <DataTable columns={columns} rows={rows} filterKeys={["class_section_name", "period_label"]} emptyLabel="No roll calls yet." />
        )}
      </div>
    </div>
  );
}
