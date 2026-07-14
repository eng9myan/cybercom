'use client';

import React from 'react';
import { BarChart3, TrendingUp, ShoppingBag, FileDown } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { useCycomList, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';

const GRAPH_DATA = [
  { name: 'Amman HQ', sales: 42000 },
  { name: 'Zarqa Branch', sales: 18900 },
  { name: 'Irbid Branch', sales: 15400 },
  { name: 'Aqaba Branch', sales: 12100 },
];

type CyPosOrderReport = {
  id: number;
  name?: string;
  date_order?: string;
  session_id?: Many2One;
  amount_total?: number;
  amount_tax?: number;
};

const mapPosOrderReport = (r: CyPosOrderReport) => ({
  id: r.name || `ORD-${r.id}`,
  date: r.date_order ? fmtDate(r.date_order) : '—',
  branch: m2oName(r.session_id, '—'),
  amount: `JOD ${(r.amount_total ?? 0).toFixed(2)}`,
  items: 0,
  payment: '—',
});

export default function POSReports() {
  const { rows: transactions, loading } = useCycomList<CyPosOrderReport, ReturnType<typeof mapPosOrderReport>>(
    'pos.order',
    [['state', 'in', ['done', 'paid', 'invoiced']]],
    ['name', 'date_order', 'session_id', 'amount_total', 'amount_tax'],
    mapPosOrderReport,
    { order: 'date_order desc', limit: 200 },
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">POS Orders Report</h1>
          <p className="page-subtitle">Analyze retail transactions, branch performance breakdowns, and payment method summaries (report_pos_order).</p>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <FileDown className="w-4 h-4" /> Download PDF Report
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 columns - Sales Chart */}
        <div className="glass-card p-6 lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Sales By Branch Location</h2>
            <span className="badge badge-cyan font-mono text-[10px]">Active Period</span>
          </div>
          <div className="h-[250px] w-full text-slate-300 text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={GRAPH_DATA}>
                <XAxis dataKey="name" stroke="#475569" />
                <YAxis stroke="#475569" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.07)' }}
                  labelStyle={{ color: '#94A3B8' }}
                />
                <Bar dataKey="sales" fill="#00F0FF" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right column - Payment Breakdown */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">Payment Breakdown</h3>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-white/5">
              <span className="text-slate-400">Credit Card / POS Terminal</span>
              <span className="text-white font-bold">JOD 48,290.00</span>
            </div>
            <div className="flex justify-between items-center pb-2 border-b border-white/5">
              <span className="text-slate-400">Cash Disbursed</span>
              <span className="text-white font-bold">JOD 24,110.00</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Pledge Invoices</span>
              <span className="text-rose-400 font-bold">JOD 6,000.00</span>
            </div>
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="glass-card p-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Recent Sales Transactions</h2>
        {loading && <div style={{ padding: '2rem', color: '#ccc' }}>Loading...</div>}
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Time & Date</th>
                <th>Branch</th>
                <th>Total Items</th>
                <th>Payment Mode</th>
                <th>Total Amount</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.id}>
                  <td className="font-mono text-xs font-bold text-slate-400">{tx.id}</td>
                  <td>{tx.date}</td>
                  <td>{tx.branch}</td>
                  <td>{tx.items} items</td>
                  <td>
                    <span className={`badge ${
                      tx.payment === 'Cash' ? 'badge-green' :
                      tx.payment === 'Card' ? 'badge-cyan' :
                      'badge-red'
                    }`}>{tx.payment}</span>
                  </td>
                  <td className="font-bold text-white">{tx.amount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
