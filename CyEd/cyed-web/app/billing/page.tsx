"use client";

import { useEffect, useMemo, useState } from "react";
import { CreditCard, FileStack, Layers } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, Loading, ErrorNote, Empty, Field } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { Panel, Badge, Modal } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { FeePlan, StudentBill, Student } from "@/lib/types";

const SCHEDULES = ["upfront", "monthly", "termly", "quarterly", "custom"];

export default function BillingPage() {
  const [plans, setPlans] = useState<FeePlan[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [bills, setBills] = useState<StudentBill[]>([]);
  const [sel, setSel] = useState<StudentBill | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pName, setPName] = useState("Termly Plan");
  const [pSched, setPSched] = useState("termly");
  const [bStudent, setBStudent] = useState("");
  const [bPlan, setBPlan] = useState("");
  const [liCat, setLiCat] = useState("tuition");
  const [liAmt, setLiAmt] = useState("3000");
  const [payAmt, setPayAmt] = useState("");
  const [payFor, setPayFor] = useState<string | null>(null);
  const toast = useToast();

  const load = async () => {
    try {
      const [p, st, b] = await Promise.all([
        cyed.list<FeePlan>("billing/plans/"),
        cyed.list<Student>("sis/students/"),
        cyed.list<StudentBill>("billing/bills/"),
      ]);
      setPlans(p); setStudents(st); setBills(b);
      if (!bStudent && st.length) setBStudent(st[0].id);
      if (!bPlan && p.length) setBPlan(p[0].id);
      if (sel) setSel(b.find((x) => x.id === sel.id) || null);
      setError(null);
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to load billing"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const totals = useMemo(() => {
    const billed = bills.reduce((s, b) => s + Number(b.total_amount || 0), 0);
    const outstanding = bills.reduce((s, b) => s + Number(b.balance || 0), 0);
    return { billed, outstanding };
  }, [bills]);

  const openBill = async (id: string) => {
    try { setSel(await cyed.get<StudentBill>(`billing/bills/${id}/`)); }
    catch (e) { toast.push(e instanceof Error ? e.message : "Failed", "bad"); }
  };
  const addPlan = async () => {
    try { await cyed.create("billing/plans/", { name: pName, schedule_type: pSched, installments_count: pSched === "monthly" ? 10 : 3 }); toast.push("Plan added"); await load(); }
    catch (e) { toast.push(e instanceof Error ? e.message : "Plan failed", "bad"); }
  };
  const addBill = async () => {
    if (!bStudent || !bPlan) return;
    try { const b = await cyed.create<StudentBill>("billing/bills/", { student: bStudent, plan: bPlan, start_date: new Date().toISOString().slice(0, 10) }); toast.push("Bill created"); await load(); openBill(b.id); }
    catch (e) { toast.push(e instanceof Error ? e.message : "Bill failed", "bad"); }
  };
  const addLine = async () => {
    if (!sel) return;
    try { await cyed.create("billing/line-items/", { bill: sel.id, category: liCat, amount: liAmt, description: liCat }); toast.push("Line item added"); openBill(sel.id); }
    catch (e) { toast.push(e instanceof Error ? e.message : "Line failed", "bad"); }
  };
  const generate = async () => {
    if (!sel) return;
    try { await cyed.action(`billing/bills/${sel.id}/generate/`); toast.push("Installments generated"); openBill(sel.id); }
    catch (e) { toast.push(e instanceof Error ? e.message : "Generate failed", "bad"); }
  };
  const pay = async () => {
    if (!payFor || !payAmt) return;
    try { await cyed.action(`billing/installments/${payFor}/pay/`, { amount: payAmt }); toast.push(`Payment of $${payAmt} recorded`); setPayFor(null); setPayAmt(""); openBill(sel!.id); }
    catch (e) { toast.push(e instanceof Error ? e.message : "Payment failed", "bad"); }
  };

  const studentName = (id: string) => { const s = students.find((x) => x.id === id); return s ? `${s.first_name} ${s.last_name}` : "—"; };
  if (loading) return <Loading label="Loading billing…" />;

  return (
    <div>
      <PageHeader title="Billing & Installments" subtitle="Plans, bills (tuition + transport + materials), and installment schedules" />
      {error && <ErrorNote error={error} />}

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))" }}>
        <StatCard label="Bills" value={bills.length} accent="cyan" icon={<FileStack size={17} />} />
        <StatCard label="Total billed" value={totals.billed} prefixDollar accent="blue" icon={<CreditCard size={17} />} />
        <StatCard label="Outstanding" value={totals.outstanding} prefixDollar accent="violet" icon={<Layers size={17} />} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
        <div className="space-y-4">
          <Panel title="Fee plans">
            <div className="space-y-1 mb-3">
              {plans.map((p) => <div key={p.id} className="text-sm">{p.name} · <span style={{ color: "var(--muted)" }}>{p.schedule_type}</span></div>)}
            </div>
            <div style={{ display: "flex", gap: 6, alignItems: "end" }}>
              <div style={{ flex: 1 }}><Field label="Name"><input className="input" value={pName} onChange={(e) => setPName(e.target.value)} /></Field></div>
              <div style={{ width: 110 }}><Field label="Schedule"><select className="input" value={pSched} onChange={(e) => setPSched(e.target.value)}>{SCHEDULES.map((s) => <option key={s}>{s}</option>)}</select></Field></div>
              <button className="btn btn-ghost" onClick={addPlan}>Add</button>
            </div>
          </Panel>
          <Panel title="New bill">
            <div className="space-y-3">
              <Field label="Student"><select className="input" value={bStudent} onChange={(e) => setBStudent(e.target.value)}>{students.map((s) => <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>)}</select></Field>
              <Field label="Plan"><select className="input" value={bPlan} onChange={(e) => setBPlan(e.target.value)}>{plans.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
              <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} onClick={addBill} disabled={!students.length || !plans.length}>Create bill</button>
            </div>
          </Panel>
          <Panel title="Bills" pad={false}>
            {bills.length === 0 ? <div style={{ padding: 16 }}><Empty label="No bills." /></div> : (
              <div className="table-scroll">
                <table><thead><tr><th>Student</th><th>Status</th></tr></thead><tbody>
                  {bills.map((b) => (
                    <tr key={b.id} onClick={() => openBill(b.id)} style={{ cursor: "pointer", boxShadow: sel?.id === b.id ? "inset 3px 0 0 var(--cyan)" : undefined, background: sel?.id === b.id ? "var(--panel-2)" : undefined }}>
                      <td>{studentName(b.student)}</td><td><Badge value={b.status} /></td>
                    </tr>
                  ))}
                </tbody></table>
              </div>
            )}
          </Panel>
        </div>

        <div>
          {!sel ? <Empty label="Select a bill." /> : (
            <Panel
              title={<div className="font-semibold">{studentName(sel.student)} — total ${sel.total_amount} · balance ${sel.balance}</div>}
              action={<button className="btn btn-primary" onClick={generate}>Generate installments</button>}
            >
              <div className="mb-4">
                <div className="label" style={{ marginBottom: 6 }}>Line items</div>
                <div className="table-scroll">
                  <table><thead><tr><th>Category</th><th>Description</th><th>Amount</th></tr></thead><tbody>
                    {(sel.line_items || []).map((li) => <tr key={li.id}><td><span className="pill" style={{ textTransform: "capitalize" }}>{li.category}</span></td><td style={{ color: "var(--muted)" }}>{li.description}</td><td>${li.amount}</td></tr>)}
                  </tbody></table>
                </div>
                <div style={{ display: "flex", gap: 6, alignItems: "end", marginTop: 10 }}>
                  <div style={{ width: 130 }}><Field label="Category"><select className="input" value={liCat} onChange={(e) => setLiCat(e.target.value)}>{["tuition", "transport", "material", "other"].map((c) => <option key={c}>{c}</option>)}</select></Field></div>
                  <div style={{ width: 100 }}><Field label="Amount"><input className="input" value={liAmt} onChange={(e) => setLiAmt(e.target.value)} /></Field></div>
                  <button className="btn btn-ghost" onClick={addLine}>Add line</button>
                </div>
              </div>
              <div>
                <div className="label" style={{ marginBottom: 6 }}>Installments</div>
                {(sel.installments || []).length === 0 ? <span className="text-xs" style={{ color: "var(--muted)" }}>None — click Generate.</span> : (
                  <div className="table-scroll">
                    <table><thead><tr><th>#</th><th>Due</th><th>Amount</th><th>Balance</th><th>Status</th><th></th></tr></thead><tbody>
                      {(sel.installments || []).map((i) => (
                        <tr key={i.id}>
                          <td>{i.installment_no}</td><td>{i.due_date}</td><td>${i.amount_due}</td><td>${i.balance}</td>
                          <td><Badge value={i.status} /></td>
                          <td style={{ textAlign: "right" }}>
                            {i.status !== "paid" && <button className="btn btn-ghost" onClick={() => { setPayFor(i.id); setPayAmt(String(i.balance ?? i.amount_due ?? "")); }}>Pay</button>}
                          </td>
                        </tr>
                      ))}
                    </tbody></table>
                  </div>
                )}
              </div>
            </Panel>
          )}
        </div>
      </div>

      <Modal open={!!payFor} onClose={() => setPayFor(null)} title="Pay installment">
        <div className="space-y-3">
          <Field label="Amount (AUD)">
            <input className="input" type="number" value={payAmt} onChange={(e) => setPayAmt(e.target.value)} autoFocus />
          </Field>
          <div className="flex justify-end gap-2">
            <button className="btn btn-ghost" onClick={() => setPayFor(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={pay}>Record ${payAmt}</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
