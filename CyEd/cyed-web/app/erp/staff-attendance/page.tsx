"use client";

import { useEffect, useMemo, useState } from "react";
import { LogIn, LogOut, Clock, CalendarCheck } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Loading, Field } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";

type Day = {
  id: string;
  staff: string;
  staff_name?: string;
  date: string;
  check_in?: string | null;
  check_out?: string | null;
  status: string;
  minutes_late: number;
  hours_worked: string;
  note?: string;
};
type Timesheet = {
  id: string;
  staff: string;
  staff_name?: string;
  period_label: string;
  total_hours: string;
  days_present: number;
  days_absent: number;
  days_leave: number;
  total_minutes_late: number;
  status: string;
};
type SummaryRow = {
  staff: string; name: string; days: number; present: number; absent: number;
  leave: number; late: number; minutes_late: number; hours: number;
};

type Tab = "days" | "timesheets" | "summary";

export default function StaffAttendancePage() {
  const [tab, setTab] = useState<Tab>("days");
  const [days, setDays] = useState<Day[]>([]);
  const [sheets, setSheets] = useState<Timesheet[]>([]);
  const [summary, setSummary] = useState<SummaryRow[] | null>(null);
  const [today, setToday] = useState<Day | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      if (from) qs.set("from", from);
      if (to) qs.set("to", to);
      const [d, t] = await Promise.all([
        cyed.list<Day>(`staff-attendance/days/?${qs}`),
        cyed.list<Timesheet>("staff-attendance/timesheets/"),
      ]);
      setDays(d);
      setSheets(t);
      setError(null);
      try {
        setToday(await cyed.get<Day>("staff-attendance/days/today/"));
      } catch {
        setToday(null); // not checked in, or no linked staff record
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load staff attendance");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [from, to]);

  useEffect(() => {
    if (tab !== "summary") return;
    (async () => {
      try {
        const qs = new URLSearchParams();
        if (from) qs.set("from", from);
        if (to) qs.set("to", to);
        const data = await cyed.get<{ rows: SummaryRow[] }>(`staff-attendance/days/summary/?${qs}`);
        setSummary(data.rows || []);
      } catch (e) {
        toast.push(e instanceof Error ? e.message : "Summary is leadership-only", "bad");
        setSummary([]);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, from, to]);

  const punch = async (which: "check-in" | "check-out") => {
    try {
      await cyed.action(`staff-attendance/days/${which}/`, {});
      toast.push(which === "check-in" ? "Checked in" : "Checked out");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not record", "bad");
    }
  };

  const act = async (path: string, ok: string) => {
    try {
      await cyed.action(path, {});
      toast.push(ok);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Action failed", "bad");
    }
  };

  const stats = useMemo(() => {
    const late = days.filter((d) => d.minutes_late > 0).length;
    const absent = days.filter((d) => d.status === "absent").length;
    const hours = days.reduce((a, d) => a + Number(d.hours_worked || 0), 0);
    return { records: days.length, late, absent, hours: Math.round(hours) };
  }, [days]);

  if (loading) return <Loading label="Loading staff attendance…" />;

  const dayCols: Column<Day>[] = [
    { key: "staff", header: "Staff", render: (d) => <span style={{ fontWeight: 600 }}>{d.staff_name || d.staff}</span> },
    { key: "date", header: "Date", width: 120, render: (d) => d.date },
    { key: "in", header: "In", width: 90, render: (d) => d.check_in || "—" },
    { key: "out", header: "Out", width: 90, render: (d) => d.check_out || "—" },
    { key: "hours", header: "Hours", width: 90, align: "right", render: (d) => d.hours_worked },
    {
      key: "late", header: "Late", width: 100, align: "right",
      render: (d) => (d.minutes_late ? <span className="status status-warn">{d.minutes_late}m</span> : "—"),
    },
    { key: "status", header: "Status", width: 130, render: (d) => <Badge value={d.status} /> },
  ];

  const sheetCols: Column<Timesheet>[] = [
    { key: "staff", header: "Staff", render: (t) => <span style={{ fontWeight: 600 }}>{t.staff_name || t.staff}</span> },
    { key: "period", header: "Period", width: 120, render: (t) => t.period_label },
    { key: "hours", header: "Hours", width: 90, align: "right", render: (t) => t.total_hours },
    { key: "present", header: "Present", width: 90, align: "right", render: (t) => t.days_present },
    { key: "absent", header: "Absent", width: 90, align: "right", render: (t) => t.days_absent },
    { key: "leave", header: "Leave", width: 90, align: "right", render: (t) => t.days_leave },
    { key: "status", header: "Status", width: 130, render: (t) => <Badge value={t.status} /> },
    {
      key: "actions", header: "", align: "right",
      render: (t) => (
        <span style={{ display: "inline-flex", gap: 6 }}>
          <button className="btn btn-ghost" onClick={() => act(`staff-attendance/timesheets/${t.id}/recalculate/`, "Recalculated")}>Recalc</button>
          {t.status === "draft" && <button className="btn btn-ghost" onClick={() => act(`staff-attendance/timesheets/${t.id}/submit/`, "Submitted")}>Submit</button>}
          {t.status === "submitted" && <button className="btn btn-primary" onClick={() => act(`staff-attendance/timesheets/${t.id}/approve/`, "Approved")}>Approve</button>}
        </span>
      ),
    },
  ];

  const sumCols: Column<SummaryRow & { id: string }>[] = [
    { key: "name", header: "Staff", render: (r) => <span style={{ fontWeight: 600 }}>{r.name}</span> },
    { key: "days", header: "Days", width: 80, align: "right", render: (r) => r.days },
    { key: "present", header: "Present", width: 90, align: "right", render: (r) => r.present },
    { key: "absent", header: "Absent", width: 90, align: "right", render: (r) => (r.absent ? <span className="status status-bad">{r.absent}</span> : "0") },
    { key: "leave", header: "Leave", width: 90, align: "right", render: (r) => r.leave },
    { key: "late", header: "Late days", width: 100, align: "right", render: (r) => (r.late ? <span className="status status-warn">{r.late}</span> : "0") },
    { key: "mins", header: "Mins late", width: 100, align: "right", render: (r) => r.minutes_late },
    { key: "hours", header: "Hours", width: 90, align: "right", render: (r) => Math.round(r.hours) },
  ];

  return (
    <div>
      <PageHeader
        title="Staff Attendance"
        subtitle="Daily check-in/out, lateness and timesheets. This is the source of truth payroll reads."
        action={
          <Segmented
            value={tab}
            onChange={setTab}
            options={[
              { value: "days", label: "Days" },
              { value: "timesheets", label: "Timesheets" },
              { value: "summary", label: "Summary" },
            ]}
          />
        }
      />

      <div className="grid gap-4 mb-5" style={{ gridTemplateColumns: "1.2fr 1fr 1fr 1fr" }}>
        <Panel title="Today">
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <button className="btn btn-primary" onClick={() => punch("check-in")} disabled={!!today?.check_in}>
              <LogIn size={14} /> Check in
            </button>
            <button className="btn btn-ghost" onClick={() => punch("check-out")} disabled={!today?.check_in || !!today?.check_out}>
              <LogOut size={14} /> Check out
            </button>
          </div>
          <div className="text-xs mt-3" style={{ color: "var(--muted)" }}>
            {today?.check_in
              ? `In ${today.check_in}${today.check_out ? ` · out ${today.check_out} · ${today.hours_worked}h` : " · still on site"}`
              : "Not checked in today."}
          </div>
        </Panel>
        <StatCard label="Records" value={stats.records} accent="cyan" icon={<CalendarCheck size={17} />} />
        <StatCard label="Late arrivals" value={stats.late} accent="violet" icon={<Clock size={17} />} />
        <StatCard label="Absences" value={stats.absent} accent="blue" icon={<LogOut size={17} />} />
      </div>

      <Panel title="Date range" className="mb-4">
        <div style={{ display: "flex", gap: 10, alignItems: "end" }}>
          <div style={{ width: 170 }}><Field label="From"><input className="input" type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></Field></div>
          <div style={{ width: 170 }}><Field label="To"><input className="input" type="date" value={to} onChange={(e) => setTo(e.target.value)} /></Field></div>
          {(from || to) && <button className="btn btn-ghost" onClick={() => { setFrom(""); setTo(""); }}>Clear</button>}
        </div>
      </Panel>

      {error && <ErrorNote error={error} />}

      {tab === "days" && <DataTable columns={dayCols} rows={days} emptyLabel="No attendance records in this range." />}
      {tab === "timesheets" && <DataTable columns={sheetCols} rows={sheets} emptyLabel="No timesheets yet." />}
      {tab === "summary" && (
        <DataTable
          columns={sumCols}
          rows={(summary || []).map((r) => ({ ...r, id: r.staff }))}
          emptyLabel="No summary available (leadership only)."
        />
      )}
    </div>
  );
}
