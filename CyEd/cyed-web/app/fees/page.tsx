"use client";

import { useEffect, useMemo, useState } from "react";
import { Receipt, Wallet, TrendingDown } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Field, SkeletonRows } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge, Modal } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { Invoice, Student } from "@/lib/types";

export default function FeesPage() {
  const [rows, setRows] = useState<Invoice[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [studentId, setStudentId] = useState("");
  const [desc, setDesc] = useState("Term 1 Tuition");
  const [amount, setAmount] = useState("1000");
  const [saving, setSaving] = useState(false);
  const [payFor, setPayFor] = useState<Invoice | null>(null);
  const [payAmount, setPayAmount] = useState("");
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [invoices, studs] = await Promise.all([
        cyed.list<Invoice>("fees/invoices/"),
        cyed.list<Student>("sis/students/"),
      ]);
      setRows(invoices);
      setStudents(studs);
      if (!studentId && studs.length) setStudentId(studs[0].id);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load fees");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const studentName = (id: string) => {
    const s = students.find((x) => x.id === id);
    return s ? `${s.first_name} ${s.last_name}` : "—";
  };

  const totals = useMemo(() => {
    const billed = rows.reduce((s, i) => s + Number(i.amount || 0), 0);
    const outstanding = rows.reduce((s, i) => s + Number(i.balance ?? i.amount ?? 0), 0);
    return { billed, collected: billed - outstanding, outstanding };
  }, [rows]);

  const createInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId) return;
    setSaving(true);
    try {
      await cyed.create("fees/invoices/", {
        student: studentId,
        description: desc,
        amount,
        status: "issued",
        issued_on: new Date().toISOString().slice(0, 10),
      });
      toast.push("Invoice issued");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Failed to create invoice", "bad");
    } finally {
      setSaving(false);
    }
  };

  const recordPayment = async () => {
    if (!payFor || !payAmount) return;
    try {
      await cyed.create("fees/payments/", { invoice: payFor.id, amount: payAmount, method: "card" });
      toast.push(`Payment of $${payAmount} recorded`);
      setPayFor(null);
      setPayAmount("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Payment failed", "bad");
    }
  };

  const columns: Column<Invoice>[] = [
    { key: "student", header: "Student", render: (i) => <span style={{ fontWeight: 600 }}>{studentName(i.student)}</span> },
    { key: "description", header: "Description", render: (i) => <span style={{ color: "var(--muted)" }}>{i.description || "—"}</span> },
    { key: "amount", header: "Amount", render: (i) => `$${i.amount}`, align: "right", width: 100 },
    { key: "balance", header: "Balance", render: (i) => `$${i.balance ?? i.amount}`, align: "right", width: 100 },
    { key: "status", header: "Status", render: (i) => <Badge value={i.status} />, width: 110 },
    {
      key: "action",
      header: "",
      align: "right",
      render: (i) =>
        i.status !== "paid" ? (
          <button className="btn btn-ghost" onClick={() => { setPayFor(i); setPayAmount(String(i.balance ?? i.amount ?? "")); }}>
            Record payment
          </button>
        ) : null,
    },
  ];

  return (
    <div>
      <PageHeader title="Fees & Billing" subtitle="Invoices and payments (AUD)" />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Total billed" value={totals.billed} prefixDollar accent="cyan" icon={<Receipt size={17} />} />
        <StatCard label="Collected" value={totals.collected} prefixDollar accent="blue" icon={<Wallet size={17} />} />
        <StatCard label="Outstanding" value={totals.outstanding} prefixDollar accent="violet" icon={<TrendingDown size={17} />} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
        <Panel title={<div className="flex items-center gap-2"><Receipt size={15} style={{ color: "var(--cyan)" }} /><span className="label">New invoice</span></div>}>
          <form onSubmit={createInvoice} className="space-y-3">
            <Field label="Student">
              <select className="input" value={studentId} onChange={(e) => setStudentId(e.target.value)}>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>
                ))}
              </select>
            </Field>
            <Field label="Description">
              <input className="input" value={desc} onChange={(e) => setDesc(e.target.value)} />
            </Field>
            <Field label="Amount (AUD)">
              <input className="input" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
            </Field>
            <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} type="submit" disabled={!students.length || saving}>
              {saving ? "Issuing…" : "Issue invoice"}
            </button>
          </form>
        </Panel>

        {loading ? (
          <SkeletonRows rows={6} />
        ) : error ? (
          <ErrorNote error={error} />
        ) : (
          <DataTable columns={columns} rows={rows} emptyLabel="No invoices yet." />
        )}
      </div>

      <Modal open={!!payFor} onClose={() => setPayFor(null)} title="Record payment">
        <div className="space-y-3">
          <div style={{ fontSize: 13, color: "var(--muted)" }}>
            {payFor && `${studentName(payFor.student)} · ${payFor.description || "Invoice"} · balance $${payFor.balance ?? payFor.amount}`}
          </div>
          <Field label="Amount (AUD)">
            <input className="input" type="number" value={payAmount} onChange={(e) => setPayAmount(e.target.value)} autoFocus />
          </Field>
          <div className="flex justify-end gap-2">
            <button className="btn btn-ghost" onClick={() => setPayFor(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={recordPayment}>Record $ {payAmount}</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
