'use client';

import React from 'react';
import { FileDown, ShieldCheck, ShieldAlert, CheckCircle2 } from 'lucide-react';

const WHITELISTS = [
  { id: 'WHL-101', branch: 'Zarqa Retail Shop', category: 'Confectionery Premium', productsAllowed: 'All premium items', status: 'Audited' },
  { id: 'WHL-102', branch: 'Irbid Warehouse', category: 'Imported Spices', productsAllowed: 'Selected Whitelist SKU set', status: 'Audit Pending' },
];

export default function InventoryReports() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Inventory Audit Reports</h1>
          <p className="page-subtitle">Examine branch stock restrictions, download transfer discrepancy excel outputs, and view whitelist audits (branch_product_whitelist).</p>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <FileDown className="w-4 h-4" /> Export Audit CSV
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Whitelist Audits */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex justify-between items-center pb-3 border-b border-white/5">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Branch Product Whitelist Rules</h2>
            <span className="badge badge-purple">Security Checks</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            <strong>branch_product_whitelist:</strong> Restricts specific store branches from listing or checking out products 
            not explicitly whitelisted for their regional customer segment. Prevents cross-branch sales pricing conflicts.
          </p>
          <div className="space-y-3">
            {WHITELISTS.map((wl) => (
              <div key={wl.id} className="p-3.5 rounded-lg bg-white/5 border border-white/5 flex justify-between items-center text-xs">
                <div>
                  <h4 className="font-bold text-slate-200">{wl.branch}</h4>
                  <span className="text-[10px] text-slate-500">Tier: {wl.category} • {wl.productsAllowed}</span>
                </div>
                <span className={`badge ${
                  wl.status === 'Audited' ? 'badge-green' : 'badge-yellow'
                }`}>{wl.status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column - Discrepancy explanation */}
        <div className="glass-card p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center pb-3 border-b border-white/5">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Transfer Discrepancy Reporting</h2>
              <span className="badge badge-cyan">Rules config</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mt-3">
              <strong>stock_transfer_discrepancy_new:</strong> When internal stock pickings are dispatched, 
              the destination warehouse performs a secondary physical audit check. 
              Any mismatch generates a discrepancy report that links to financial write-offs.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-black/45 border border-white/5 text-xs text-slate-300">
            <div className="flex justify-between items-center">
              <span>Auto discrepancy reporting threshold:</span>
              <span className="font-mono text-cyan-400 font-bold">1% or &gt; JOD 50.00</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
