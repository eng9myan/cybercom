"use client";

import { useEffect, useMemo, useState } from "react";
import { Banknote, Receipt, ShieldCheck, Wallet } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Loading, Field, Empty } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge, Modal } from "@/components/kit";
import { useToast } from "@/components/Toast";

type Payslip = {
  id: string;
  staff: string;
  staff_name?: string;
  gross: string;
  paye_tax: string;
  superannuation: string;
  net: string;
  hours_worked?: string;
  unpaid_days?: string;
  payment_status: string;
  lines?: { id: string; kind: string; description: string; amount: string }[];
};
type Run = {
  id: string;
  period_label: string;
  period_start?: string | null;
  period_end?: string | null;
  status: string;
  pay_date?: string | null;
  payslips?: Payslip[];
};
type Reconcile = {
  reconciled: boolean;
  out_of_sync: number;
  payslips: number;
  rows: { name: string; payslip_hours: string; attendance_hours: string; payslip_unpaid_days: string; attendance_unpaid_days: string; in_sync: boolean }[];
};

export default function PayrollPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [sel, setSel] = useState<Run | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rec, setRec] = useState<Reconcile | null>(null);
  const [slip, setSlip] = useState<Payslip | null>(null);
  const [label, setLabel] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const r = await cyed.list<Run>("payroll/runs/");
      setRuns(r);
      if (sel) setSel(r.find((x) => x.id === sel.id) || null);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load payroll");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const open = async (r: Run) => {
    setRec(null);
    try {
      setSel(await cyed.get<Run>(`payroll/runs/${r.id}/`));
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not open run", "bad");
    }
  };

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const r = await cyed.create<Run>("payroll/runs/", {
        period_label: label, period_start: start || null, period_end: end || null,
      });
      toast.push(`Run ${label} created`);
      setLabel("");
      await load();
      open(r);
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Could not create run", "bad");
    }
  };

  const run = async (action: string, ok: string) => {
    if (!sel) return;
    try {
      await cyed.action(`payroll/runs/${sel.id}/${action}/`, {});
      toast.push(ok);
      await load();
      open(sel);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Action failed", "bad");
    }
  };

  const reconcile = async () => {
    if (!sel) return;
    try {
      setRec(await cyed.get<Reconcile>(`payroll/runs/${sel.id}/reconcile/`));
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Reconcile failed", "bad");
    }
  };

  const totals = useMemo(() => {
    const slips = sel?.payslips || [];
    const sum = (k: keyof Payslip) => slips.reduce((a, s) => a + Number(s[k] || 0), 0);
    return { count: slips.length, gross: sum("gross"), tax: sum("paye_tax"), net: sum("net") };
  }, [sel]);

  if (loading) return <Loading label="Loading payroll…" />;

  const slipCols: Column<Payslip>[] = [
    { key: "staff", header: "Staff", render: (s) => <span style={{ fontWeight: 600 }}>{s.staff_name || s.staff}</span> },
    { key: "hours", header: "Hours", width: 90, align: "right", render: (s) => s.hours_worked ?? "—" },
    {
      key: "unpaid", header: "Unpaid", width: 90, align: "right",
      render: (s) => (Number(s.unpaid_days || 0) > 0 ? <span className="status status-bad">{s.unpaid_days}d</span> : "—"),
    },
    { key: "gross", header: "Gross", width: 110, align: "right", render: (s) => `$${s.gross}` },
    { key: "tax", header: "PAYG", width: 110, align: "right", render: (s) => `$${s.paye_tax}` },
    { key: "super", header: "Super", width: 110, align: "right", render: (s) => `$${s.superannuation}` },
    { key: "net", header: "Net", width: 110, align: "right", render: (s) => <strong>${s.net}</strong> },
    { key: "pay", header: "Payment", width: 120, render: (s) => <Badge value={s.payment_status} /> },
    { key: "act", header: "", align: "right", render: (s) => <button className="btn btn-ghost" onClick={() => setSlip(s)}>Payslip</button> },
  ];

  return (
    <div>
      <PageHeader title="Payroll" subtitle="Pay runs built from staff attendance — unexplained absence docks pay. AU PAYG + superannuation." />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Pay runs" value={runs.length} accent="cyan" icon={<Banknote size={17} />} />
        <StatCard label="Payslips (run)" value={totals.count} accent="blue" icon={<Receipt size={17} />} />
        <StatCard label="Gross (run)" value={totals.gross} prefixDollar accent="violet" icon={<Wallet size={17} />} />
        <StatCard label="Net (run)" value={totals.net} prefixDollar accent="cyan" icon={<ShieldCheck size={17} />} />
      </div>

      {error && <ErrorNote error={error} />}

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
        <div className="space-y-4">
          <Panel title="New pay run">
            <form onSubmit={create} className="space-y-3">
              <Field label="Period label"><input className="input" placeholder="2026-03" value={label} onChange={(e) => setLabel(e.target.value)} required /></Field>
              <Field label="Period start"><input className="input" type="date" value={start} onChange={(e) => setStart(e.target.value)} /></Field>
              <Field label="Period end"><input className="input" type="date" value={end} onChange={(e) => setEnd(e.target.value)} /></Field>
              <p className="text-xs" style={{ color: "var(--faint)" }}>
                Set a period so attendance can be consulted and reconciled.
              </p>
              <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }}>Create run</button>
            </form>
          </Panel>
          <Panel title="Pay runs" pad={false}>
            {runs.length === 0 ? (
              <div style={{ padding: 16 }}><Empty label="No pay runs yet." /></div>
            ) : (
              <div className="table-scroll">
                <table>
                  <tbody>
                    {runs.map((r) => (
                      <tr key={r.id} onClick={() => open(r)} style={{
                        cursor: "pointer",
                        boxShadow: sel?.id === r.id ? "inset 3px 0 0 var(--cyan)" : undefined,
                        background: sel?.id === r.id ? "var(--panel-2)" : undefined,
                      }}>
                        <td><div style={{ fontWeight: 600 }}>{r.period_label}</div></td>
                        <td style={{ textAlign: "right" }}><Badge value={r.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </div>

        <div className="space-y-4">
          {!sel ? (
            <Empty label="Select a pay run." />
          ) : (
            <>
              <Panel
                title={<div className="font-semibold">{sel.period_label} · <Badge value={sel.status} /></div>}
                action={
                  <div style={{ display: "flex", gap: 8 }}>
                    {sel.status === "draft" && <button className="btn btn-primary" onClick={() => run("process", "Payslips generated from attendance")}>Process</button>}
                    {sel.status === "processed" && <button className="btn btn-primary" onClick={() => run("mark-paid", "Run marked paid")}>Mark paid</button>}
                    <button className="btn btn-ghost" onClick={reconcile}>Reconcile vs attendance</button>
                  </div>
                }
              >
                {rec && (
                  <div className="mb-3">
                    <span className={`status ${rec.reconciled ? "status-ok" : "status-bad"}`}>
                      {rec.reconciled ? "in sync with staff attendance" : `${rec.out_of_sync} of ${rec.payslips} out of sync`}
                    </span>
                    {!rec.reconciled && (
                      <div className="table-scroll mt-2">
                        <table>
                          <thead><tr><th>Staff</th><th>Payslip hrs</th><th>Attendance hrs</th><th>Payslip unpaid</th><th>Attendance unpaid</th></tr></thead>
                          <tbody>
                            {rec.rows.filter((r) => !r.in_sync).map((r, i) => (
                              <tr key={i}>
                                <td>{r.name}</td><td>{r.payslip_hours}</td><td>{r.attendance_hours}</td>
                                <td>{r.payslip_unpaid_days}</td><td>{r.attendance_unpaid_days}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <p className="text-xs mt-2" style={{ color: "var(--muted)" }}>
                          Attendance changed after this run was processed — reprocess to bring pay back in line.
                        </p>
                      </div>
                    )}
                  </div>
                )}
                <div style={{ fontSize: 13, color: "var(--muted)" }}>
                  {sel.period_start && sel.period_end ? `Period ${sel.period_start} → ${sel.period_end}` : "No period set — attendance will not be consulted."}
                </div>
              </Panel>

              <DataTable columns={slipCols} rows={sel.payslips || []} emptyLabel="No payslips — process the run." />
            </>
          )}
        </div>
      </div>

      <Modal open={!!slip} onClose={() => setSlip(null)} title={`Payslip — ${slip?.staff_name || ""}`} width={560}>
        {slip && (
          <div className="space-y-3">
            <div className="table-scroll">
              <table>
                <thead><tr><th>Type</th><th>Description</th><th style={{ textAlign: "right" }}>Amount</th></tr></thead>
                <tbody>
                  {(slip.lines || []).map((l) => (
                    <tr key={l.id}>
                      <td><span className="pill" style={{ textTransform: "capitalize" }}>{l.kind}</span></td>
                      <td>{l.description}</td>
                      <td style={{ textAlign: "right" }}>${l.amount}</td>
                    </tr>
                  ))}
                  {(slip.lines || []).length === 0 && <tr><td colSpan={3} style={{ color: "var(--muted)" }}>No itemised lines.</td></tr>}
                </tbody>
              </table>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700, fontSize: "1.05rem" }}>
              <span>Net pay</span><span className="grad-text">${slip.net}</span>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
