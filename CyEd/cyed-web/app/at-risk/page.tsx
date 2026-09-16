"use client";

import { useEffect, useState } from "react";
import { AlertOctagon, AlertTriangle, ShieldCheck } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, Loading, ErrorNote } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import type { AtRiskResponse } from "@/lib/types";

type Row = AtRiskResponse["students"][number];

export default function AtRiskPage() {
  const [data, setData] = useState<AtRiskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setData(await cyed.get<AtRiskResponse>("analytics/at-risk/"));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load analytics");
      }
    })();
  }, []);

  if (error) return <ErrorNote error={error} />;
  if (!data) return <Loading label="Computing risk signals…" />;

  const flagged = data.students.filter((s) => s.risk_band !== "low");

  const columns: Column<Row & { id: string }>[] = [
    { key: "student_name", header: "Student", render: (s) => <span style={{ fontWeight: 600 }}>{s.student_name}</span> },
    { key: "year", header: "Year", render: (s) => `Y${s.year_level}`, width: 70 },
    {
      key: "risk",
      header: "Risk",
      width: 110,
      render: (s) => (
        <span className={`status ${s.risk_band === "high" ? "status-bad" : "status-warn"}`} style={{ textTransform: "capitalize" }}>
          {s.risk_band}
        </span>
      ),
    },
    { key: "absence", header: "Absence", render: (s) => `${(s.absence_rate * 100).toFixed(0)}%`, align: "right", width: 100 },
    { key: "avg", header: "Avg grade", render: (s) => (s.avg_grade != null ? `${s.avg_grade}%` : "—"), align: "right", width: 100 },
    { key: "factors", header: "Factors", render: (s) => <span style={{ color: "var(--muted)", fontSize: "0.75rem" }}>{s.factors.join("; ") || "—"}</span> },
  ];

  return (
    <div>
      <PageHeader
        title="Predictive Student Success"
        subtitle="Early at-risk signals from attendance, grades, and behaviour. Advisory — a counsellor reviews."
      />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="High risk" value={data.summary.high} accent="violet" icon={<AlertOctagon size={17} />} />
        <StatCard label="Medium risk" value={data.summary.medium} accent="blue" icon={<AlertTriangle size={17} />} />
        <StatCard label="Low / on track" value={data.summary.low} accent="cyan" icon={<ShieldCheck size={17} />} />
      </div>

      <DataTable
        columns={columns}
        rows={flagged.map((s) => ({ ...s, id: s.student_id }))}
        filterKeys={["student_name"]}
        emptyLabel="No students currently flagged. Seed attendance/grades/behaviour to see signals."
      />
    </div>
  );
}
