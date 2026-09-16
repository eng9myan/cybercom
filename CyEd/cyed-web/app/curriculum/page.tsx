"use client";

import { useEffect, useMemo, useState } from "react";
import { BookMarked, Layers, Sparkles, Tag } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Loading, Field, SkeletonRows } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { Panel, Badge } from "@/components/kit";
import { DataTable, type Column } from "@/components/table";

type Coverage = {
  total_outcomes: number;
  content_descriptions: number;
  elaborations: number;
  general_capabilities: number;
  cross_curriculum_priorities: number;
  achievement_standards: number;
  by_learning_area: { learning_area: string; count: number }[];
  by_year_level: { year_level: number; count: number }[];
  by_learning_area_and_year: { learning_area: string; year_level: number; count: number }[];
  attribution: string;
};

type Outcome = {
  id: string;
  code: string;
  learning_area: string;
  year_level: number;
  strand?: string;
  content_description?: string;
  is_elaboration?: boolean;
  general_capability_codes?: string[];
};

const YEARS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const yearLabel = (y: number) => (y === 0 ? "F" : String(y));

export default function CurriculumPage() {
  const [cov, setCov] = useState<Coverage | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [area, setArea] = useState("");
  const [year, setYear] = useState("");
  const [code, setCode] = useState("");
  const [showElaborations, setShowElaborations] = useState(false);
  const [rows, setRows] = useState<Outcome[]>([]);
  const [loadingRows, setLoadingRows] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setCov(await cyed.get<Coverage>("curriculum/outcomes/coverage/"));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load curriculum coverage");
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      setLoadingRows(true);
      try {
        const qs = new URLSearchParams();
        if (area) qs.set("learning_area", area);
        if (year !== "") qs.set("year_level", year);
        if (code) qs.set("code", code);
        qs.set("elaborations", showElaborations ? "only" : "exclude");
        setRows(await cyed.list<Outcome>(`curriculum/outcomes/?${qs.toString()}`));
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load outcomes");
      } finally {
        setLoadingRows(false);
      }
    })();
  }, [area, year, code, showElaborations]);

  // learning area × year grid, for the coverage heatmap
  const grid = useMemo(() => {
    if (!cov) return null;
    const areas = cov.by_learning_area.map((a) => a.learning_area);
    const lookup = new Map<string, number>();
    let max = 0;
    for (const c of cov.by_learning_area_and_year) {
      lookup.set(`${c.learning_area}|${c.year_level}`, c.count);
      if (c.count > max) max = c.count;
    }
    return { areas, lookup, max };
  }, [cov]);

  if (error && !cov) return <ErrorNote error={error} />;
  if (!cov) return <Loading label="Loading Australian Curriculum coverage…" />;

  const columns: Column<Outcome>[] = [
    {
      key: "code",
      header: "Code",
      width: 130,
      render: (o) => <span className="pill grad-text" style={{ fontWeight: 700 }}>{o.code}</span>,
    },
    { key: "year", header: "Year", width: 70, render: (o) => yearLabel(o.year_level) },
    { key: "area", header: "Learning area", render: (o) => <span style={{ color: "var(--muted)" }}>{o.learning_area}</span> },
    { key: "strand", header: "Strand", render: (o) => <span style={{ color: "var(--muted)" }}>{o.strand || "—"}</span> },
    {
      key: "text",
      header: "Content description",
      render: (o) => <span style={{ display: "block", maxWidth: 520 }}>{o.content_description || "—"}</span>,
    },
    {
      key: "gc",
      header: "Capabilities",
      width: 150,
      render: (o) =>
        (o.general_capability_codes || []).length ? (
          <span style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {(o.general_capability_codes || []).map((c) => (
              <span key={c} className="pill">{c}</span>
            ))}
          </span>
        ) : (
          <span style={{ color: "var(--faint)" }}>—</span>
        ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Australian Curriculum (ACARA v9)"
        subtitle="Machine-readable curriculum loaded from ACARA. Everything the AI tutor and teacher tools ground against."
        action={<Badge value="loaded" />}
      />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Content descriptions" value={cov.content_descriptions} accent="cyan" icon={<BookMarked size={17} />} />
        <StatCard label="Elaborations" value={cov.elaborations} accent="blue" icon={<Layers size={17} />} />
        <StatCard label="General capabilities" value={cov.general_capabilities} accent="violet" icon={<Sparkles size={17} />} />
        <StatCard label="Achievement standards" value={cov.achievement_standards} accent="cyan" icon={<Tag size={17} />} />
      </div>

      <Panel title="Coverage — learning area × year level" className="mb-5">
        {grid && (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th style={{ minWidth: 180 }}>Learning area</th>
                  {YEARS.map((y) => (
                    <th key={y} style={{ textAlign: "center", width: 52 }}>{yearLabel(y)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {grid.areas.map((a) => (
                  <tr key={a}>
                    <td style={{ fontWeight: 600 }}>{a}</td>
                    {YEARS.map((y) => {
                      const n = grid.lookup.get(`${a}|${y}`) ?? 0;
                      const intensity = grid.max ? Math.round((n / grid.max) * 100) : 0;
                      return (
                        <td
                          key={y}
                          title={`${a} · Year ${yearLabel(y)}: ${n} outcomes`}
                          style={{
                            textAlign: "center",
                            fontSize: 11,
                            color: intensity > 45 ? "#04121a" : "var(--muted)",
                            background: n
                              ? `color-mix(in srgb, var(--cyan) ${Math.max(intensity, 12)}%, transparent)`
                              : "transparent",
                          }}
                        >
                          {n || "·"}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Panel title="Browse outcomes" className="mb-4">
        <div style={{ display: "flex", gap: 10, alignItems: "end", flexWrap: "wrap" }}>
          <div style={{ minWidth: 200 }}>
            <Field label="Learning area">
              <select className="input" value={area} onChange={(e) => setArea(e.target.value)}>
                <option value="">All</option>
                {cov.by_learning_area.map((a) => (
                  <option key={a.learning_area} value={a.learning_area}>
                    {a.learning_area} ({a.count})
                  </option>
                ))}
              </select>
            </Field>
          </div>
          <div style={{ width: 120 }}>
            <Field label="Year">
              <select className="input" value={year} onChange={(e) => setYear(e.target.value)}>
                <option value="">All</option>
                {YEARS.map((y) => (
                  <option key={y} value={String(y)}>{yearLabel(y)}</option>
                ))}
              </select>
            </Field>
          </div>
          <div style={{ width: 180 }}>
            <Field label="Code contains">
              <input className="input" placeholder="AC9M8N" value={code} onChange={(e) => setCode(e.target.value)} />
            </Field>
          </div>
          <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: "0.82rem", paddingBottom: 8 }}>
            <input type="checkbox" checked={showElaborations} onChange={(e) => setShowElaborations(e.target.checked)} />
            Show elaborations instead
          </label>
        </div>
      </Panel>

      {error && <ErrorNote error={error} />}
      {loadingRows ? (
        <SkeletonRows rows={6} />
      ) : (
        <DataTable columns={columns} rows={rows} emptyLabel="No outcomes match those filters." />
      )}

      <p className="text-xs mt-4" style={{ color: "var(--faint)", maxWidth: 900, lineHeight: 1.5 }}>
        {cov.attribution}
      </p>
    </div>
  );
}
