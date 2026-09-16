"use client";

import { useEffect, useMemo, useState } from "react";
import { BookOpen, Library, BookMarked } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Field, SkeletonRows } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { Course } from "@/lib/types";

export default function LmsPage() {
  const [rows, setRows] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [subject, setSubject] = useState("Mathematics");
  const [year, setYear] = useState("8");
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      setRows(await cyed.list<Course>("lms/courses/"));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load courses");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const stats = useMemo(() => {
    const published = rows.filter((c) => c.is_published).length;
    const lessons = rows.reduce((s, c) => s + (c.lesson_count ?? 0), 0);
    return { total: rows.length, published, lessons };
  }, [rows]);

  const addCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return;
    setSaving(true);
    try {
      await cyed.create("lms/courses/", { name, subject, year_level: parseInt(year) || 8, is_published: true });
      setName("");
      toast.push(`Course “${name}” created`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Failed to create course", "bad");
    } finally {
      setSaving(false);
    }
  };

  const columns: Column<Course>[] = [
    { key: "name", header: "Course", render: (c) => <span style={{ fontWeight: 600 }}>{c.name}</span> },
    { key: "subject", header: "Subject", render: (c) => <span style={{ color: "var(--muted)" }}>{c.subject || "—"}</span> },
    { key: "year", header: "Year", render: (c) => `Y${c.year_level}`, width: 80 },
    { key: "lessons", header: "Lessons", render: (c) => c.lesson_count ?? 0, width: 90, align: "right" },
    { key: "published", header: "State", render: (c) => <Badge value={c.is_published ? "published" : "draft"} />, width: 120 },
  ];

  return (
    <div>
      <PageHeader title="Learning (LMS)" subtitle="Courses, modules, and ACARA-coded lessons" />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Courses" value={stats.total} accent="cyan" icon={<Library size={17} />} />
        <StatCard label="Published" value={stats.published} accent="blue" icon={<BookMarked size={17} />} />
        <StatCard label="Lessons" value={stats.lessons} accent="violet" icon={<BookOpen size={17} />} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
        <Panel title={<div className="flex items-center gap-2"><BookOpen size={15} style={{ color: "var(--cyan)" }} /><span className="label">New course</span></div>}>
          <form onSubmit={addCourse} className="space-y-3">
            <Field label="Name">
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
            </Field>
            <Field label="Subject">
              <input className="input" value={subject} onChange={(e) => setSubject(e.target.value)} />
            </Field>
            <Field label="Year level">
              <input className="input" type="number" min={0} max={12} value={year} onChange={(e) => setYear(e.target.value)} />
            </Field>
            <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} type="submit" disabled={saving}>
              {saving ? "Creating…" : "Add course"}
            </button>
          </form>
        </Panel>

        {loading ? (
          <SkeletonRows rows={6} />
        ) : error ? (
          <ErrorNote error={error} />
        ) : (
          <DataTable columns={columns} rows={rows} filterKeys={["name", "subject"]} emptyLabel="No courses yet." />
        )}
      </div>
    </div>
  );
}
