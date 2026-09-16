"use client";

import { useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote } from "@/components/ui";

type ImportReport = {
  created: number;
  updated: number;
  errors: { row: number; error: string }[];
};

const TEMPLATES: Record<string, string> = {
  students:
    "first_name,last_name,student_number,date_of_birth,gender,year_level,email,enrolment_status,usi,state_student_number,indigenous_status,country_of_birth,language_at_home,lbote,campus_code",
  staff: "first_name,last_name,staff_number,email,phone,role,department,campus_code",
};

function ImportCard({
  kind,
  endpoint,
  title,
  hint,
}: {
  kind: "students" | "staff";
  endpoint: string;
  title: string;
  hint: string;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<ImportReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputId = `file-${kind}`;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    setReport(null);
    try {
      const form = new FormData();
      form.append("file", file);
      setReport(await cyed.upload<ImportReport>(endpoint, form));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setBusy(false);
    }
  };

  const downloadTemplate = () => {
    const blob = new Blob([TEMPLATES[kind] + "\n"], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${kind}-template.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="card p-5" aria-labelledby={`${kind}-h`}>
      <h2 id={`${kind}-h`} className="font-bold mb-1">
        {title}
      </h2>
      <p className="text-sm mb-4" style={{ color: "var(--muted)" }}>
        {hint}
      </p>

      <form onSubmit={submit} className="space-y-3">
        <label htmlFor={inputId} className="label">
          CSV file
        </label>
        <input
          id={inputId}
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="input"
          aria-describedby={`${kind}-desc`}
        />
        <p id={`${kind}-desc`} className="sr-only">
          Upload a comma-separated values file to bulk import {kind}.
        </p>
        <div className="flex items-center gap-2">
          <button type="submit" className="btn btn-primary" disabled={!file || busy}>
            {busy ? "Importing…" : "Import"}
          </button>
          <button type="button" className="btn btn-ghost" onClick={downloadTemplate}>
            Download template
          </button>
        </div>
      </form>

      <div aria-live="polite" className="mt-4">
        {error && <ErrorNote error={error} />}
        {report && (
          <div className="card p-4 text-sm" style={{ background: "#0b1424" }}>
            <p className="font-semibold mb-2">
              <span className="status status-ok">
                {report.created} created
              </span>{" "}
              <span className="status status-warn">
                {report.updated} updated
              </span>{" "}
              {report.errors.length > 0 && (
                <span className="status status-bad">{report.errors.length} skipped</span>
              )}
            </p>
            {report.errors.length > 0 && (
              <table>
                <caption className="sr-only">Rows that could not be imported</caption>
                <thead>
                  <tr>
                    <th scope="col">Row</th>
                    <th scope="col">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {report.errors.map((er, i) => (
                    <tr key={i}>
                      <td>{er.row}</td>
                      <td>{er.error}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

export default function DataImportPage() {
  return (
    <div>
      <PageHeader
        title="Data Import"
        subtitle="Onboard a school or the whole group from a legacy system. Imports upsert by key — re-running the same file updates rather than duplicates."
      />
      <div className="grid gap-5" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" }}>
        <ImportCard
          kind="students"
          endpoint="sis/students/import/"
          title="Students"
          hint="Upsert key: student_number. Optional campus_code maps to a campus in this group."
        />
        <ImportCard
          kind="staff"
          endpoint="hr/staff/import/"
          title="Staff"
          hint="Upsert key: staff_number (or email). Role must be one of teacher, admin, support, leadership, finance."
        />
      </div>
    </div>
  );
}
