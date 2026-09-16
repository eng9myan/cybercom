"use client";

import { useCallback, useEffect, useState } from "react";
import { Download, FileSpreadsheet } from "lucide-react";
import { cyed, cyedUrl } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { fmtDateTime } from "@/lib/portal";

/**
 * Statutory returns.
 *
 * These feed government portals and carry the whole cohort's personal
 * information, so the screen is deliberately unglamorous: choose a return,
 * look at what would be submitted, then download it.
 *
 * Preview before download is the point. A return is submitted once and argued
 * about afterwards, and "how many rows and which students" is the question
 * worth answering before the file leaves the building — not after.
 *
 * Every generation, preview included, is written to the report log below.
 * That log is the school's evidence of what was produced and by whom.
 */

type ExportKey = "nccd" | "nccd-summary" | "attendance" | "naplan" | "census";

type Preview = {
  report: string;
  period: string;
  count: number;
  rows: Record<string, unknown>[];
};

type LogRow = {
  id: string;
  report_type: string;
  period: string;
  row_count: number;
  generated_by: string;
  fmt: string;
  created_at: string;
};

const EXPORTS: { key: ExportKey; label: string; blurb: string; needsYear?: boolean; needsRange?: boolean }[] = [
  {
    key: "nccd",
    label: "NCCD return",
    blurb: "One row per student with an adjustment, with its category and level.",
    needsYear: true,
  },
  {
    key: "nccd-summary",
    label: "NCCD summary",
    blurb: "Counts by category and level — the aggregate the portal asks for.",
    needsYear: true,
  },
  {
    key: "attendance",
    label: "Attendance return",
    blurb: "Per-student attendance over a date range.",
    needsRange: true,
  },
  { key: "naplan", label: "NAPLAN participation", blurb: "Participation status per eligible student." },
  { key: "census", label: "Census", blurb: "Enrolment counts as at today, by year level." },
];

export default function CompliancePage() {
  const [which, setWhich] = useState<ExportKey>("nccd");
  const [year, setYear] = useState(String(new Date().getFullYear()));
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [logs, setLogs] = useState<LogRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingLogs, setLoadingLogs] = useState(true);
  const toast = useToast();

  const spec = EXPORTS.find((e) => e.key === which)!;

  const query = useCallback(() => {
    const params = new URLSearchParams();
    if (spec.needsYear && year) params.set("year", year);
    if (spec.needsRange) {
      if (from) params.set("from", from);
      if (to) params.set("to", to);
    }
    return params.toString();
  }, [spec, year, from, to]);

  const loadLogs = useCallback(async () => {
    try {
      setLogs(await cyed.list<LogRow>("compliance/report-logs/"));
    } catch {
      // The log is supporting evidence, not the job — a failure here must not
      // stop someone producing a return that is due today.
    } finally {
      setLoadingLogs(false);
    }
  }, []);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  useEffect(() => {
    setPreview(null);
    setError(null);
  }, [which]);

  const run = async () => {
    setLoading(true);
    try {
      const q = query();
      setPreview(await cyed.get<Preview>(`compliance/exports/${which}/${q ? `?${q}` : ""}`));
      setError(null);
      await loadLogs();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not build that return");
      setPreview(null);
    } finally {
      setLoading(false);
    }
  };

  const csvHref = () => {
    const q = query();
    return cyedUrl(`compliance/exports/${which}/?fmt=csv${q ? `&${q}` : ""}`);
  };

  const columns = preview?.rows?.length ? Object.keys(preview.rows[0]) : [];

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Statutory returns"
        subtitle="NCCD, attendance, NAPLAN and census exports"
        action={
          <Segmented
            value={which}
            onChange={setWhich}
            options={EXPORTS.map((e) => ({ value: e.key, label: e.label }))}
          />
        }
      />

      <Panel title={spec.label}>
        <p style={{ color: "var(--muted)", fontSize: "0.88rem", marginBottom: "0.9rem" }}>
          {spec.blurb}
        </p>

        <div
          style={{
            display: "grid",
            gap: "0.9rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(11rem, 1fr))",
            alignItems: "end",
          }}
        >
          {spec.needsYear && (
            <Field label="Collection year">
              <input className="input" value={year} onChange={(e) => setYear(e.target.value)} />
            </Field>
          )}
          {spec.needsRange && (
            <>
              <Field label="From">
                <input
                  className="input"
                  type="date"
                  value={from}
                  onChange={(e) => setFrom(e.target.value)}
                />
              </Field>
              <Field label="To">
                <input
                  className="input"
                  type="date"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                />
              </Field>
            </>
          )}
          <button className="btn btn-primary" disabled={loading} onClick={run}>
            <FileSpreadsheet size={15} style={{ marginRight: 6 }} />
            {loading ? "Building…" : "Preview"}
          </button>
        </div>

        <p style={{ fontSize: "0.78rem", color: "var(--faint)", marginTop: "0.8rem" }}>
          Every generation — preview included — is written to the report log below, with who
          produced it. That log is what evidences the return.
        </p>
      </Panel>

      {error && <ErrorNote error={error} />}

      {preview && (
        <Panel
          title={`${preview.count} row(s)${preview.period ? ` · ${preview.period}` : ""}`}
          action={
            preview.count > 0 && (
              <a className="btn btn-primary" href={csvHref()} onClick={() => toast.push("Downloading CSV…")}>
                <Download size={15} style={{ marginRight: 6 }} />
                Download CSV
              </a>
            )
          }
          pad={false}
        >
          {preview.count === 0 ? (
            <div style={{ padding: "1.1rem" }}>
              <Empty label="This return would submit no rows. Check the period before lodging." />
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="table" style={{ width: "100%" }}>
                <thead>
                  <tr>
                    {columns.map((c) => (
                      <th key={c} style={{ whiteSpace: "nowrap" }}>
                        {c.replace(/_/g, " ")}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {/* Capped: a census of 2,600 students would otherwise render
                      every row into the DOM to be glanced at and closed. */}
                  {preview.rows.slice(0, 50).map((row, i) => (
                    <tr key={i}>
                      {columns.map((c) => (
                        <td key={c} style={{ whiteSpace: "nowrap" }}>
                          {String(row[c] ?? "—")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {preview.count > 50 && (
                <p style={{ fontSize: "0.78rem", color: "var(--faint)", padding: "0.7rem 1.1rem" }}>
                  Showing the first 50 of {preview.count}. The CSV contains all of them.
                </p>
              )}
            </div>
          )}
        </Panel>
      )}

      <Panel title="Report log">
        {loadingLogs ? (
          <SkeletonRows rows={3} />
        ) : logs.length === 0 ? (
          <Empty label="No returns have been generated yet." />
        ) : (
          <div style={{ display: "grid", gap: "0.4rem" }}>
            {logs.slice(0, 25).map((row) => (
              <div
                key={row.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "0.75rem",
                  flexWrap: "wrap",
                  padding: "0.45rem 0",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <span>
                  <strong>{row.report_type}</strong>
                  <span style={{ color: "var(--muted)", fontSize: "0.83rem" }}>
                    {row.period && ` · ${row.period}`} · {row.row_count} rows
                    {row.generated_by && ` · ${row.generated_by}`}
                  </span>
                </span>
                <span style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  <Badge value={row.fmt} />
                  <span style={{ fontSize: "0.78rem", color: "var(--faint)" }}>
                    {fmtDateTime(row.created_at)}
                  </span>
                </span>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
