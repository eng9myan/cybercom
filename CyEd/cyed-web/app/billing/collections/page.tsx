"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, RefreshCw, ArrowUpCircle, PauseCircle, PlayCircle, CheckCircle2 } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge, Modal, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { DunningCase } from "@/lib/types";

const STATUS_FILTERS = [
  { value: "", label: "All" },
  { value: "open", label: "Open" },
  { value: "paused", label: "Paused" },
  { value: "resolved", label: "Resolved" },
  { value: "written_off", label: "Written off" },
] as const;

function money(v: string | number) {
  return `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function CollectionsPage() {
  const [rows, setRows] = useState<DunningCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("open");
  const [sweeping, setSweeping] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [detail, setDetail] = useState<DunningCase | null>(null);
  const [pauseReason, setPauseReason] = useState("");
  const [resolveNote, setResolveNote] = useState("");
  const [writeOff, setWriteOff] = useState(false);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const qs = statusFilter ? `?status=${statusFilter}` : "";
      setRows(await cyed.list<DunningCase>(`billing/dunning-cases/${qs}`));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load collections cases");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const stats = useMemo(() => {
    const open = rows.filter((c) => c.status === "open").length;
    const paused = rows.filter((c) => c.status === "paused").length;
    const overdue = rows.reduce((sum, c) => sum + Number(c.current_overdue || 0), 0);
    return { open, paused, overdue };
  }, [rows]);

  const runSweep = async () => {
    setSweeping(true);
    try {
      const result = await cyed.action<{ opened: number; resolved: number }>("billing/dunning-cases/sweep/", {});
      toast.push(`Sweep: ${result.opened} case(s) opened, ${result.resolved} resolved`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Sweep failed", "bad");
    } finally {
      setSweeping(false);
    }
  };

  const escalate = async (row: DunningCase) => {
    setBusyId(row.id);
    try {
      await cyed.action(`billing/dunning-cases/${row.id}/escalate/`, { notify: true });
      toast.push(`${row.family_name} escalated`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not escalate — the ladder's rules refused it", "bad");
    } finally {
      setBusyId(null);
    }
  };

  const resume = async (row: DunningCase) => {
    setBusyId(row.id);
    try {
      await cyed.action(`billing/dunning-cases/${row.id}/resume/`, {});
      toast.push(`${row.family_name} resumed`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not resume", "bad");
    } finally {
      setBusyId(null);
    }
  };

  const pause = async () => {
    if (!detail) return;
    setBusyId(detail.id);
    try {
      await cyed.action(`billing/dunning-cases/${detail.id}/pause/`, { reason: pauseReason });
      toast.push(`${detail.family_name} paused`);
      setPauseReason("");
      setDetail(null);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not pause", "bad");
    } finally {
      setBusyId(null);
    }
  };

  const resolve = async () => {
    if (!detail) return;
    setBusyId(detail.id);
    try {
      await cyed.action(`billing/dunning-cases/${detail.id}/resolve/`, {
        note: resolveNote, written_off: writeOff,
      });
      toast.push(`${detail.family_name} ${writeOff ? "written off" : "resolved"}`);
      setResolveNote("");
      setWriteOff(false);
      setDetail(null);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not resolve", "bad");
    } finally {
      setBusyId(null);
    }
  };

  const columns: Column<DunningCase>[] = [
    { key: "family", header: "Household", render: (c) => <span style={{ fontWeight: 600 }}>{c.family_name}</span> },
    { key: "stage", header: "Stage", render: (c) => <Badge value={c.stage_display} />, width: 200 },
    { key: "status", header: "Status", render: (c) => <Badge value={c.status} />, width: 110 },
    { key: "overdue", header: "Overdue", align: "right", render: (c) => money(c.current_overdue), width: 110 },
    { key: "last", header: "Last action", render: (c) => c.last_action_on || "—", width: 120 },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (c) => (
        <div className="flex items-center gap-1.5" style={{ justifyContent: "flex-end" }}>
          {c.status === "open" && (
            <button className="btn btn-ghost" style={{ fontSize: 12 }} disabled={busyId === c.id} onClick={() => escalate(c)}>
              <ArrowUpCircle size={13} /> Escalate
            </button>
          )}
          {c.status === "paused" && (
            <button className="btn btn-ghost" style={{ fontSize: 12 }} disabled={busyId === c.id} onClick={() => resume(c)}>
              <PlayCircle size={13} /> Resume
            </button>
          )}
          <button className="btn btn-ghost" style={{ fontSize: 12 }} onClick={() => setDetail(c)}>
            Details
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Collections"
        subtitle="Fee-defaulter escalation ladder — reminder → formal notice → meeting → referral"
        action={
          <button className="btn btn-primary" onClick={runSweep} disabled={sweeping}>
            <RefreshCw size={14} /> {sweeping ? "Sweeping…" : "Run sweep"}
          </button>
        }
      />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Open cases" value={stats.open} accent="cyan" icon={<AlertTriangle size={17} />} />
        <StatCard label="Paused" value={stats.paused} accent="violet" icon={<PauseCircle size={17} />} />
        <StatCard label="Total overdue" value={stats.overdue} prefixDollar decimals={2} accent="blue" icon={<CheckCircle2 size={17} />} />
      </div>

      <Panel title={<Segmented<string> value={statusFilter} onChange={setStatusFilter} options={STATUS_FILTERS.map((f) => ({ value: f.value, label: f.label }))} />}>
        {loading ? (
          <SkeletonRows rows={6} />
        ) : error ? (
          <ErrorNote error={error} />
        ) : rows.length === 0 ? (
          <Empty label="No collections cases at this status." />
        ) : (
          <DataTable columns={columns} rows={rows} filterKeys={["family_name"]} emptyLabel="No cases." />
        )}
      </Panel>

      <Modal open={!!detail} onClose={() => setDetail(null)} title={detail ? detail.family_name : ""} width={560}>
        {detail && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge value={detail.stage_display} />
              <Badge value={detail.status} />
              <span className="muted">Overdue {money(detail.current_overdue)}</span>
            </div>

            <div>
              <div className="label mb-1">History</div>
              {detail.actions.length === 0 ? (
                <p className="muted">No actions recorded yet.</p>
              ) : (
                <div className="space-y-1.5" style={{ maxHeight: 220, overflowY: "auto" }}>
                  {detail.actions.map((a) => (
                    <div key={a.id} className="flex items-center justify-between" style={{ fontSize: 13 }}>
                      <span>{a.stage_display}</span>
                      <span className="muted">{a.action_on} · {a.performed_by} · {money(a.balance_at_action)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {detail.status === "open" && (
              <div className="space-y-2">
                <div className="label">Pause (genuine hardship, stop the letters)</div>
                <input
                  className="input"
                  placeholder="Reason"
                  value={pauseReason}
                  onChange={(e) => setPauseReason(e.target.value)}
                />
                <button className="btn btn-secondary" style={{ width: "100%" }} disabled={busyId === detail.id} onClick={pause}>
                  Pause case
                </button>
              </div>
            )}

            {(detail.status === "open" || detail.status === "paused") && (
              <div className="space-y-2">
                <div className="label">Resolve</div>
                <input
                  className="input"
                  placeholder="Note"
                  value={resolveNote}
                  onChange={(e) => setResolveNote(e.target.value)}
                />
                <label className="flex items-center gap-2" style={{ fontSize: 13 }}>
                  <input type="checkbox" checked={writeOff} onChange={(e) => setWriteOff(e.target.checked)} />
                  Write off (debt is uncollectable)
                </label>
                <button className="btn btn-primary" style={{ width: "100%" }} disabled={busyId === detail.id} onClick={resolve}>
                  {writeOff ? "Write off" : "Mark resolved"}
                </button>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
