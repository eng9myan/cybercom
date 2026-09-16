"use client";

import { useEffect, useMemo, useState } from "react";
import { UserPlus, Users, GraduationCap, CircleUserRound } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Field, SkeletonRows } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { Student } from "@/lib/types";

export default function StudentsPage() {
  const [rows, setRows] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [yearLevel, setYearLevel] = useState("7");
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      setRows(await cyed.list<Student>("sis/students/"));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load students");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const stats = useMemo(() => {
    const enrolled = rows.filter((s) => s.enrolment_status === "enrolled").length;
    const applicants = rows.filter((s) => s.enrolment_status === "applicant").length;
    return { total: rows.length, enrolled, applicants };
  }, [rows]);

  const addStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!firstName || !lastName) return;
    setSaving(true);
    try {
      await cyed.create("sis/students/", {
        first_name: firstName,
        last_name: lastName,
        year_level: parseInt(yearLevel) || 7,
        enrolment_status: "enrolled",
      });
      setFirstName("");
      setLastName("");
      toast.push(`${firstName} ${lastName} added`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Failed to create student", "bad");
    } finally {
      setSaving(false);
    }
  };

  const columns: Column<Student>[] = [
    {
      key: "name",
      header: "Name",
      render: (s) => (
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{
              width: 30, height: 30, borderRadius: 9, display: "grid", placeItems: "center",
              background: "var(--grad-primary)", color: "#fff", fontWeight: 700, fontSize: 12, flexShrink: 0,
            }}
          >
            {(s.first_name?.[0] ?? "") + (s.last_name?.[0] ?? "")}
          </span>
          <span style={{ fontWeight: 600 }}>{s.full_name || `${s.first_name} ${s.last_name}`}</span>
        </div>
      ),
    },
    { key: "year", header: "Year", render: (s) => `Y${s.year_level}`, width: 80 },
    { key: "status", header: "Status", render: (s) => <Badge value={s.enrolment_status} />, width: 130 },
    { key: "student_number", header: "Student #", render: (s) => <span style={{ color: "var(--muted)" }}>{s.student_number || "—"}</span> },
  ];

  return (
    <div>
      <PageHeader title="Students" subtitle="Student information system" />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Total students" value={stats.total} accent="cyan" icon={<Users size={17} />} />
        <StatCard label="Enrolled" value={stats.enrolled} accent="blue" icon={<GraduationCap size={17} />} />
        <StatCard label="Applicants" value={stats.applicants} accent="violet" icon={<CircleUserRound size={17} />} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
        <Panel title={<div className="flex items-center gap-2"><UserPlus size={15} style={{ color: "var(--cyan)" }} /><span className="label">New student</span></div>}>
          <form onSubmit={addStudent} className="space-y-3">
            <Field label="First name">
              <input className="input" value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
            </Field>
            <Field label="Last name">
              <input className="input" value={lastName} onChange={(e) => setLastName(e.target.value)} required />
            </Field>
            <Field label="Year level">
              <input className="input" type="number" min={0} max={12} value={yearLevel} onChange={(e) => setYearLevel(e.target.value)} />
            </Field>
            <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} type="submit" disabled={saving}>
              {saving ? "Adding…" : "Add student"}
            </button>
          </form>
        </Panel>

        {loading ? (
          <SkeletonRows rows={6} />
        ) : error ? (
          <ErrorNote error={error} />
        ) : (
          <DataTable columns={columns} rows={rows} filterKeys={["first_name", "last_name", "student_number"]} emptyLabel="No students yet — add one on the left." />
        )}
      </div>
    </div>
  );
}
