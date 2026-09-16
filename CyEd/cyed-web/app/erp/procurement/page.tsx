"use client";

import { useEffect, useMemo, useState } from "react";
import { ShoppingCart, FileCheck2, Truck, Building2 } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Loading, Field, Empty } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge, Segmented, Modal } from "@/components/kit";
import { useToast } from "@/components/Toast";

type Supplier = { id: string; name: string; abn?: string; email?: string; is_active: boolean };
type Approval = { id: string; level: number; decision: string; approver?: string; comment?: string };
type PRLine = { id: string; description: string; quantity: string; estimated_unit_price: string };
type PR = {
  id: string; reference?: string; department?: string; justification?: string; status: string;
  estimated_total: string; needs_second_approval: boolean; requested_by?: string;
  lines?: PRLine[]; approvals?: Approval[]; suggested_supplier?: string | null;
};
type POLine = { id: string; description: string; quantity: string; unit_price: string; quantity_received: string; quantity_outstanding: string };
type PO = { id: string; reference?: string; supplier: string; supplier_name?: string; status: string; total: string; lines?: POLine[] };

type Tab = "requests" | "orders" | "suppliers";

export default function ProcurementPage() {
  const [tab, setTab] = useState<Tab>("requests");
  const [prs, setPrs] = useState<PR[]>([]);
  const [pos, setPos] = useState<PO[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [selPr, setSelPr] = useState<PR | null>(null);
  const [selPo, setSelPo] = useState<PO | null>(null);
  const [receiveFor, setReceiveFor] = useState<POLine | null>(null);
  const [qty, setQty] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const [dept, setDept] = useState("");
  const [just, setJust] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const [r, o, s] = await Promise.all([
        cyed.list<PR>("procurement/requests/"),
        cyed.list<PO>("procurement/purchase-orders/"),
        cyed.list<Supplier>("procurement/suppliers/"),
      ]);
      setPrs(r); setPos(o); setSuppliers(s);
      if (selPr) setSelPr(r.find((x) => x.id === selPr.id) || null);
      if (selPo) setSelPo(o.find((x) => x.id === selPo.id) || null);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load procurement");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stats = useMemo(() => ({
    open: prs.filter((p) => ["submitted", "approved_l1"].includes(p.status)).length,
    approved: prs.filter((p) => p.status === "approved").length,
    orders: pos.length,
    suppliers: suppliers.length,
  }), [prs, pos, suppliers]);

  const act = async (path: string, ok: string, body: Record<string, unknown> = {}) => {
    try {
      await cyed.action(path, body);
      toast.push(ok);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Action failed", "bad");
    }
  };

  const createPr = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const pr = await cyed.create<PR>("procurement/requests/", { department: dept, justification: just });
      toast.push("Purchase request raised");
      setDept(""); setJust("");
      await load();
      setSelPr(pr);
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Could not raise request", "bad");
    }
  };

  const receive = async () => {
    if (!selPo || !receiveFor) return;
    try {
      await cyed.action(`procurement/purchase-orders/${selPo.id}/receive/`, {
        lines: [{ purchase_order_line_id: receiveFor.id, quantity: Number(qty) }],
      });
      toast.push("Goods received — stock in, ledger posted");
      setReceiveFor(null); setQty("");
      await load();
      setSelPo(await cyed.get<PO>(`procurement/purchase-orders/${selPo.id}/`));
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Receipt failed", "bad");
    }
  };

  if (loading) return <Loading label="Loading procurement…" />;

  const prCols: Column<PR>[] = [
    { key: "ref", header: "Request", render: (p) => <span style={{ fontWeight: 600 }}>{p.reference || p.department || p.id.slice(0, 8)}</span> },
    { key: "by", header: "Raised by", render: (p) => <span style={{ color: "var(--muted)" }}>{p.requested_by || "—"}</span> },
    { key: "total", header: "Estimated", width: 130, align: "right", render: (p) => `$${p.estimated_total}` },
    { key: "two", header: "Approvals", width: 120, render: (p) => <span className="pill">{p.needs_second_approval ? "2 levels" : "1 level"}</span> },
    { key: "status", header: "Status", width: 150, render: (p) => <Badge value={p.status} /> },
    { key: "act", header: "", align: "right", render: (p) => <button className="btn btn-ghost" onClick={() => setSelPr(p)}>Open</button> },
  ];

  const poCols: Column<PO>[] = [
    { key: "ref", header: "Order", render: (p) => <span style={{ fontWeight: 600 }}>{p.reference || p.id.slice(0, 8)}</span> },
    { key: "supplier", header: "Supplier", render: (p) => <span style={{ color: "var(--muted)" }}>{p.supplier_name || p.supplier}</span> },
    { key: "total", header: "Total", width: 120, align: "right", render: (p) => `$${p.total}` },
    { key: "status", header: "Status", width: 170, render: (p) => <Badge value={p.status} /> },
    {
      key: "act", header: "", align: "right",
      render: (p) => <button className="btn btn-ghost" onClick={async () => setSelPo(await cyed.get<PO>(`procurement/purchase-orders/${p.id}/`))}>Receive</button>,
    },
  ];

  const supCols: Column<Supplier>[] = [
    { key: "name", header: "Supplier", render: (s) => <span style={{ fontWeight: 600 }}>{s.name}</span> },
    { key: "abn", header: "ABN", width: 160, render: (s) => <span style={{ color: "var(--muted)" }}>{s.abn || "—"}</span> },
    { key: "email", header: "Email", render: (s) => <span style={{ color: "var(--muted)" }}>{s.email || "—"}</span> },
    { key: "status", header: "Status", width: 120, render: (s) => <Badge value={s.is_active ? "active" : "cancelled"} /> },
  ];

  return (
    <div>
      <PageHeader
        title="Procurement"
        subtitle="Purchase requests through approval to order and goods receipt. Receiving moves stock and posts to the ledger."
        action={
          <Segmented
            value={tab}
            onChange={setTab}
            options={[
              { value: "requests", label: "Requests" },
              { value: "orders", label: "Orders" },
              { value: "suppliers", label: "Suppliers" },
            ]}
          />
        }
      />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Awaiting approval" value={stats.open} accent="violet" icon={<FileCheck2 size={17} />} />
        <StatCard label="Approved" value={stats.approved} accent="cyan" icon={<ShoppingCart size={17} />} />
        <StatCard label="Purchase orders" value={stats.orders} accent="blue" icon={<Truck size={17} />} />
        <StatCard label="Suppliers" value={stats.suppliers} accent="cyan" icon={<Building2 size={17} />} />
      </div>

      {error && <ErrorNote error={error} />}

      {tab === "requests" && (
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
          <Panel title="Raise a request">
            <form onSubmit={createPr} className="space-y-3">
              <Field label="Department"><input className="input" value={dept} onChange={(e) => setDept(e.target.value)} required /></Field>
              <Field label="Justification"><textarea className="input" rows={3} value={just} onChange={(e) => setJust(e.target.value)} /></Field>
              <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }}>Raise request</button>
              <p className="text-xs" style={{ color: "var(--faint)" }}>
                Requests of $5,000 or more need a second, leadership approval. You can never approve your own request.
              </p>
            </form>
          </Panel>
          <div className="space-y-4">
            <DataTable columns={prCols} rows={prs} emptyLabel="No purchase requests." />
            {selPr && (
              <Panel
                title={<div className="font-semibold">Request {selPr.reference || selPr.id.slice(0, 8)} · <Badge value={selPr.status} /></div>}
                action={
                  <div style={{ display: "flex", gap: 8 }}>
                    {selPr.status === "draft" && <button className="btn btn-primary" onClick={() => act(`procurement/requests/${selPr.id}/submit/`, "Submitted for approval")}>Submit</button>}
                    {["submitted", "approved_l1"].includes(selPr.status) && (
                      <>
                        <button className="btn btn-primary" onClick={() => act(`procurement/requests/${selPr.id}/approve/`, "Approved", { level: selPr.status === "submitted" ? 1 : 2 })}>
                          Approve L{selPr.status === "submitted" ? 1 : 2}
                        </button>
                        <button className="btn btn-ghost" onClick={() => act(`procurement/requests/${selPr.id}/reject/`, "Rejected", { level: selPr.status === "submitted" ? 1 : 2 })}>Reject</button>
                      </>
                    )}
                    {selPr.status === "approved" && <button className="btn btn-violet" onClick={() => act(`procurement/requests/${selPr.id}/convert/`, "Converted to a purchase order")}>Convert to PO</button>}
                  </div>
                }
              >
                <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 10 }}>{selPr.justification || "No justification given."}</div>
                <div className="label mb-2">Approval chain</div>
                {(selPr.approvals || []).length === 0 ? (
                  <div style={{ fontSize: 13, color: "var(--faint)" }}>Not submitted yet.</div>
                ) : (
                  <div className="space-y-1">
                    {(selPr.approvals || []).map((a) => (
                      <div key={a.id} style={{ display: "flex", gap: 10, alignItems: "center", fontSize: 13 }}>
                        <span className="pill">L{a.level}</span>
                        <Badge value={a.decision} />
                        <span style={{ color: "var(--muted)" }}>{a.approver || "awaiting"}</span>
                        {a.comment && <span style={{ color: "var(--faint)" }}>· {a.comment}</span>}
                      </div>
                    ))}
                  </div>
                )}
              </Panel>
            )}
          </div>
        </div>
      )}

      {tab === "orders" && (
        <div className="space-y-4">
          <DataTable columns={poCols} rows={pos} emptyLabel="No purchase orders." />
          {selPo && (
            <Panel title={<div className="font-semibold">Order {selPo.reference} · <Badge value={selPo.status} /></div>}>
              <div className="table-scroll">
                <table>
                  <thead><tr><th>Item</th><th style={{ textAlign: "right" }}>Ordered</th><th style={{ textAlign: "right" }}>Received</th><th style={{ textAlign: "right" }}>Outstanding</th><th></th></tr></thead>
                  <tbody>
                    {(selPo.lines || []).map((l) => (
                      <tr key={l.id}>
                        <td>{l.description}</td>
                        <td style={{ textAlign: "right" }}>{l.quantity}</td>
                        <td style={{ textAlign: "right" }}>{l.quantity_received}</td>
                        <td style={{ textAlign: "right" }}>{l.quantity_outstanding}</td>
                        <td style={{ textAlign: "right" }}>
                          {Number(l.quantity_outstanding) > 0 && (
                            <button className="btn btn-ghost" onClick={() => { setReceiveFor(l); setQty(l.quantity_outstanding); }}>Receive</button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>
          )}
        </div>
      )}

      {tab === "suppliers" && <DataTable columns={supCols} rows={suppliers} filterKeys={["name"]} emptyLabel="No suppliers." />}

      <Modal open={!!receiveFor} onClose={() => setReceiveFor(null)} title="Receive goods">
        <div className="space-y-3">
          <div style={{ fontSize: 13, color: "var(--muted)" }}>
            {receiveFor?.description} — {receiveFor?.quantity_outstanding} outstanding. Over-receipt is refused.
          </div>
          <Field label="Quantity received"><input className="input" type="number" value={qty} onChange={(e) => setQty(e.target.value)} autoFocus /></Field>
          <div className="flex justify-end gap-2">
            <button className="btn btn-ghost" onClick={() => setReceiveFor(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={receive}>Receive</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
