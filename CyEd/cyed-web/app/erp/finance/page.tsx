"use client";

import { useEffect, useState } from "react";
import { Calculator, TrendingUp, Scale, Landmark } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Loading, Field, Empty } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";

type Account = { id: string; code: string; name: string; account_type: string };
type Line = { code: string; name: string; type: string; amount: string };
type PL = { total_income: string; total_expenses: string; net_surplus: string; income: Line[]; expenses: Line[] };
type BS = {
  total_assets: string; total_liabilities: string; total_equity: string; retained_surplus: string;
  balanced: boolean; assets: Line[]; liabilities: Line[]; equity: Line[];
};
type Budget = { id: string; name: string; fiscal_year: string; status: string };
type BudgetRow = { account_code: string; account_name: string; budgeted: string; actual: string; variance: string; utilisation_pct: string };
type BankLine = { id: string; date: string; description: string; amount: string; is_reconciled: boolean; bank_reference?: string };

type Tab = "statements" | "budgets" | "bank" | "ledger";

export default function FinancePage() {
  const [tab, setTab] = useState<Tab>("statements");
  const [pl, setPl] = useState<PL | null>(null);
  const [bs, setBs] = useState<BS | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [budgetRows, setBudgetRows] = useState<BudgetRow[] | null>(null);
  const [selBudget, setSelBudget] = useState<Budget | null>(null);
  const [bank, setBank] = useState<BankLine[]>([]);
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
      const [p, b, a, bg, bl] = await Promise.all([
        cyed.get<PL>(`finance/profit-and-loss/?${qs}`),
        cyed.get<BS>(`finance/balance-sheet/${to ? `?as_of=${to}` : ""}`),
        cyed.list<Account>("finance/accounts/"),
        cyed.list<Budget>("finance/budgets/"),
        cyed.list<BankLine>("finance/bank-lines/"),
      ]);
      setPl(p); setBs(b); setAccounts(a); setBudgets(bg); setBank(bl);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load accounting");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [from, to]);

  const openBudget = async (b: Budget) => {
    setSelBudget(b);
    try {
      const data = await cyed.get<{ rows: BudgetRow[] }>(`finance/budgets/${b.id}/vs-actual/`);
      setBudgetRows(data.rows || []);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not load budget", "bad");
    }
  };

  const reconcileLine = async (l: BankLine) => {
    const entry = window.prompt("Journal entry id to match this bank line against:");
    if (!entry) return;
    try {
      await cyed.action(`finance/bank-lines/${l.id}/reconcile/`, { entry });
      toast.push("Bank line reconciled");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Reconcile failed", "bad");
    }
  };

  if (loading) return <Loading label="Loading accounting…" />;

  const statementRows = (rows: Line[]): Column<Line & { id: string }>[] => [
    { key: "code", header: "Code", width: 90, render: (r) => <span className="pill">{r.code}</span> },
    { key: "name", header: "Account", render: (r) => r.name },
    { key: "amount", header: "Amount", width: 130, align: "right", render: (r) => `$${r.amount}` },
  ];

  const budgetCols: Column<BudgetRow & { id: string }>[] = [
    { key: "code", header: "Account", render: (r) => <span><span className="pill">{r.account_code}</span> {r.account_name}</span> },
    { key: "budgeted", header: "Budget", width: 120, align: "right", render: (r) => `$${r.budgeted}` },
    { key: "actual", header: "Actual", width: 120, align: "right", render: (r) => `$${r.actual}` },
    {
      key: "variance", header: "Variance", width: 130, align: "right",
      render: (r) => (
        <span className={`status ${Number(r.variance) < 0 ? "status-bad" : "status-ok"}`}>
          ${r.variance}
        </span>
      ),
    },
    { key: "util", header: "Used", width: 90, align: "right", render: (r) => `${r.utilisation_pct}%` },
  ];

  const bankCols: Column<BankLine>[] = [
    { key: "date", header: "Date", width: 120, render: (l) => l.date },
    { key: "desc", header: "Description", render: (l) => l.description },
    { key: "ref", header: "Reference", width: 140, render: (l) => <span style={{ color: "var(--muted)" }}>{l.bank_reference || "—"}</span> },
    {
      key: "amount", header: "Amount", width: 120, align: "right",
      render: (l) => <span style={{ color: Number(l.amount) < 0 ? "var(--bad)" : "var(--ok)" }}>${l.amount}</span>,
    },
    { key: "status", header: "Status", width: 140, render: (l) => <Badge value={l.is_reconciled ? "completed" : "pending"} /> },
    {
      key: "act", header: "", align: "right",
      render: (l) => (!l.is_reconciled ? <button className="btn btn-ghost" onClick={() => reconcileLine(l)}>Reconcile</button> : null),
    },
  ];

  const accountCols: Column<Account>[] = [
    { key: "code", header: "Code", width: 100, render: (a) => <span className="pill">{a.code}</span> },
    { key: "name", header: "Name", render: (a) => <span style={{ fontWeight: 600 }}>{a.name}</span> },
    { key: "type", header: "Type", width: 140, render: (a) => <span className="pill" style={{ textTransform: "capitalize" }}>{a.account_type}</span> },
  ];

  return (
    <div>
      <PageHeader
        title="Accounting"
        subtitle="General ledger, budgets, bank reconciliation and financial statements. Separate from student fees, but fed by payroll and procurement."
        action={
          <Segmented
            value={tab}
            onChange={setTab}
            options={[
              { value: "statements", label: "Statements" },
              { value: "budgets", label: "Budgets" },
              { value: "bank", label: "Bank" },
              { value: "ledger", label: "Chart" },
            ]}
          />
        }
      />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Income" value={Number(pl?.total_income || 0)} prefixDollar accent="cyan" icon={<TrendingUp size={17} />} />
        <StatCard label="Expenses" value={Number(pl?.total_expenses || 0)} prefixDollar accent="violet" icon={<Calculator size={17} />} />
        <StatCard label="Net surplus" value={Number(pl?.net_surplus || 0)} prefixDollar accent="blue" icon={<Scale size={17} />} />
        <StatCard label="Total assets" value={Number(bs?.total_assets || 0)} prefixDollar accent="cyan" icon={<Landmark size={17} />} />
      </div>

      <Panel title="Reporting period" className="mb-4">
        <div style={{ display: "flex", gap: 10, alignItems: "end" }}>
          <div style={{ width: 170 }}><Field label="From"><input className="input" type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></Field></div>
          <div style={{ width: 170 }}><Field label="To / as at"><input className="input" type="date" value={to} onChange={(e) => setTo(e.target.value)} /></Field></div>
          {(from || to) && <button className="btn btn-ghost" onClick={() => { setFrom(""); setTo(""); }}>Clear</button>}
        </div>
      </Panel>

      {error && <ErrorNote error={error} />}

      {tab === "statements" && pl && bs && (
        <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <Panel title="Profit & Loss">
            <div className="label mb-2">Income</div>
            <DataTable columns={statementRows(pl.income)} rows={pl.income.map((r, i) => ({ ...r, id: `${r.code}-${i}` }))} emptyLabel="No income posted." />
            <div className="label mt-4 mb-2">Expenses</div>
            <DataTable columns={statementRows(pl.expenses)} rows={pl.expenses.map((r, i) => ({ ...r, id: `${r.code}-${i}` }))} emptyLabel="No expenses posted." />
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 14, fontWeight: 700 }}>
              <span>Net surplus</span><span className="grad-text">${pl.net_surplus}</span>
            </div>
          </Panel>

          <Panel
            title="Balance Sheet"
            action={<span className={`status ${bs.balanced ? "status-ok" : "status-bad"}`}>{bs.balanced ? "balanced" : "OUT OF BALANCE"}</span>}
          >
            <div className="label mb-2">Assets</div>
            <DataTable columns={statementRows(bs.assets)} rows={bs.assets.map((r, i) => ({ ...r, id: `a${i}` }))} emptyLabel="No assets." />
            <div className="label mt-4 mb-2">Liabilities</div>
            <DataTable columns={statementRows(bs.liabilities)} rows={bs.liabilities.map((r, i) => ({ ...r, id: `l${i}` }))} emptyLabel="No liabilities." />
            <div className="space-y-1 mt-4" style={{ fontSize: 13 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Total assets</span><strong>${bs.total_assets}</strong></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Total liabilities</span><strong>${bs.total_liabilities}</strong></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Retained surplus</span><strong>${bs.retained_surplus}</strong></div>
              <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700 }}><span>Total equity</span><span className="grad-text">${bs.total_equity}</span></div>
            </div>
          </Panel>
        </div>
      )}

      {tab === "budgets" && (
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
          <Panel title="Budgets" pad={false}>
            {budgets.length === 0 ? (
              <div style={{ padding: 16 }}><Empty label="No budgets yet." /></div>
            ) : (
              <div className="table-scroll">
                <table>
                  <tbody>
                    {budgets.map((b) => (
                      <tr key={b.id} onClick={() => openBudget(b)} style={{
                        cursor: "pointer",
                        boxShadow: selBudget?.id === b.id ? "inset 3px 0 0 var(--cyan)" : undefined,
                        background: selBudget?.id === b.id ? "var(--panel-2)" : undefined,
                      }}>
                        <td><div style={{ fontWeight: 600 }}>{b.name}</div><div style={{ fontSize: 11, color: "var(--faint)" }}>{b.fiscal_year}</div></td>
                        <td style={{ textAlign: "right" }}><Badge value={b.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
          {budgetRows ? (
            <DataTable columns={budgetCols} rows={budgetRows.map((r, i) => ({ ...r, id: `${r.account_code}-${i}` }))} emptyLabel="No budget lines." />
          ) : (
            <Empty label="Select a budget to see budget vs actual." />
          )}
        </div>
      )}

      {tab === "bank" && <DataTable columns={bankCols} rows={bank} filterKeys={["description"]} emptyLabel="No bank statement lines imported." />}
      {tab === "ledger" && <DataTable columns={accountCols} rows={accounts} filterKeys={["code", "name"]} emptyLabel="No accounts in the chart." />}
    </div>
  );
}
