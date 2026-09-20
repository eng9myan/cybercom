"use client";

import { useEffect, useMemo, useState } from "react";
import { UserPlus, Inbox, CheckCircle2, Clock, MapPin } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Field, SkeletonRows } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { Application, CatchmentVerdict } from "@/lib/types";

export default function AdmissionsPage() {
  const [rows, setRows] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [year, setYear] = useState("7");
  const [guardian, setGuardian] = useState("");
  const [suburb, setSuburb] = useState("");
  const [postcode, setPostcode] = useState("");
  const [saving, setSaving] = useState(false);
  const [zones, setZones] = useState<Record<string, CatchmentVerdict | "loading">>({});
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      setRows(await cyed.list<Application>("admissions/applications/"));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load applications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const stats = useMemo(() => {
    const enrolled = rows.filter((a) => a.enrolled_student_id).length;
    return { total: rows.length, enrolled, open: rows.length - enrolled };
  }, [rows]);

  const addApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!first || !last) return;
    setSaving(true);
    try {
      await cyed.create("admissions/applications/", {
        applicant_first_name: first,
        applicant_last_name: last,
        year_level_applying: parseInt(year) || 7,
        guardian_name: guardian,
        residential_suburb: suburb,
        residential_postcode: postcode,
        status: "submitted",
      });
      setFirst("");
      setLast("");
      setGuardian("");
      setSuburb("");
      setPostcode("");
      toast.push("Application submitted");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Failed to create application", "bad");
    } finally {
      setSaving(false);
    }
  };

  const checkZone = async (id: string) => {
    setZones((z) => ({ ...z, [id]: "loading" }));
    try {
      const verdict = await cyed.get<CatchmentVerdict>(`admissions/applications/${id}/catchment/`);
      setZones((z) => ({ ...z, [id]: verdict }));
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Catchment check failed", "bad");
      setZones((z) => {
        const next = { ...z };
        delete next[id];
        return next;
      });
    }
  };

  const enrol = async (id: string, name: string) => {
    try {
      await cyed.action(`admissions/applications/${id}/enrol/`, {});
      toast.push(`${name} enrolled into the SIS`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Enrol failed", "bad");
    }
  };

  const columns: Column<Application>[] = [
    { key: "applicant", header: "Applicant", render: (a) => <span style={{ fontWeight: 600 }}>{a.applicant_first_name} {a.applicant_last_name}</span> },
    { key: "year", header: "Year", render: (a) => `Y${a.year_level_applying}`, width: 80 },
    { key: "status", header: "Status", render: (a) => <Badge value={a.status} />, width: 130 },
    {
      key: "zone",
      header: "Zone",
      width: 160,
      render: (a) => {
        const v = zones[a.id];
        if (v === "loading") return <span className="muted">Checking…</span>;
        if (!v) {
          return (
            <button
              className="btn btn-ghost"
              style={{ fontSize: 12, padding: "2px 8px" }}
              onClick={() => checkZone(a.id)}
              disabled={!a.residential_suburb && !a.residential_postcode}
              title={!a.residential_suburb && !a.residential_postcode ? "No address on this application" : undefined}
            >
              <MapPin size={12} /> Check
            </button>
          );
        }
        if (!v.checked) return <span className="muted" title={v.reason}>Unchecked</span>;
        if (!v.in_catchment) return <span className="status status-warn">Out of zone</span>;
        return (
          <span className="status status-ok" title={v.zone_name}>
            {v.is_priority ? "Priority zone" : "In zone"}
          </span>
        );
      },
    },
    {
      key: "action",
      header: "",
      align: "right",
      render: (a) =>
        a.enrolled_student_id ? (
          <Badge value="enrolled" />
        ) : (
          <button className="btn btn-ghost" onClick={() => enrol(a.id, `${a.applicant_first_name} ${a.applicant_last_name}`)}>
            Enrol →
          </button>
        ),
    },
  ];

  return (
    <div>
      <PageHeader title="Admissions" subtitle="Applications → offers → enrol into the SIS" />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Applications" value={stats.total} accent="cyan" icon={<Inbox size={17} />} />
        <StatCard label="Awaiting enrol" value={stats.open} accent="violet" icon={<Clock size={17} />} />
        <StatCard label="Enrolled" value={stats.enrolled} accent="blue" icon={<CheckCircle2 size={17} />} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
        <Panel title={<div className="flex items-center gap-2"><UserPlus size={15} style={{ color: "var(--cyan)" }} /><span className="label">New application</span></div>}>
          <form onSubmit={addApplication} className="space-y-3">
            <Field label="First name">
              <input className="input" value={first} onChange={(e) => setFirst(e.target.value)} required />
            </Field>
            <Field label="Last name">
              <input className="input" value={last} onChange={(e) => setLast(e.target.value)} required />
            </Field>
            <Field label="Year applying">
              <input className="input" type="number" min={0} max={12} value={year} onChange={(e) => setYear(e.target.value)} />
            </Field>
            <Field label="Guardian">
              <input className="input" value={guardian} onChange={(e) => setGuardian(e.target.value)} />
            </Field>
            <Field label="Residential suburb">
              <input className="input" value={suburb} onChange={(e) => setSuburb(e.target.value)} placeholder="e.g. Richmond" />
            </Field>
            <Field label="Residential postcode">
              <input className="input" value={postcode} onChange={(e) => setPostcode(e.target.value)} placeholder="e.g. 3121" />
            </Field>
            <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} type="submit" disabled={saving}>
              {saving ? "Submitting…" : "Add application"}
            </button>
          </form>
        </Panel>

        {loading ? (
          <SkeletonRows rows={6} />
        ) : error ? (
          <ErrorNote error={error} />
        ) : (
          <DataTable columns={columns} rows={rows} filterKeys={["applicant_first_name", "applicant_last_name"]} emptyLabel="No applications yet." />
        )}
      </div>
    </div>
  );
}
