'use client';

import React from 'react';
import Link from 'next/link';
import { useCycomList, fmtMoney } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';
import { 
  Users, UserPlus, Shield, ShieldAlert, ShieldCheck, 
  CreditCard, FileText, AlertTriangle, AlertCircle
} from 'lucide-react';

interface VendorRow {
  rawId: number;
  id: string;
  legalName: string;
  tradeName: string;
  crNumber: string;
  taxNumber: string;
  paymentTerms: string;
  creditLimit: string;
  riskRating: string;
  status: string;
  category: string;
}

type CycomVendor = {
  id: number;
  legal_name: string;
  trade_name?: string;
  vendor_code?: string;
  cr_number?: string;
  tax_number?: string;
  payment_terms_days?: number;
  credit_limit?: number;
  risk_rating?: string;
  approval_status?: string;
  category?: string;
};

const mapVendor = (r: CycomVendor): VendorRow => ({
  rawId: r.id,
  id: r.vendor_code || `VND-${String(r.id).padStart(4, '0')}`,
  legalName: r.legal_name,
  tradeName: r.trade_name || '—',
  crNumber: r.cr_number || '—',
  taxNumber: r.tax_number || '—',
  paymentTerms: `${r.payment_terms_days ?? 30} Days`,
  creditLimit: r.credit_limit ? fmtMoney(r.credit_limit, 'JOD') : '—',
  riskRating: r.risk_rating || 'medium',
  status: r.approval_status || 'draft',
  category: r.category ? r.category.toUpperCase() : 'GOODS',
});

const STATUS_BADGE: Record<string, string> = {
  draft: 'bg-slate-800 text-slate-400 border border-slate-700',
  submitted: 'bg-blue-950/40 text-blue-400 border border-blue-500/20',
  under_review: 'bg-amber-950/40 text-amber-400 border border-amber-500/20',
  approved: 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/20',
  rejected: 'bg-rose-950/40 text-rose-400 border border-rose-500/20',
  suspended: 'bg-red-950/40 text-red-500 border border-red-500/30'
};

const RISK_BADGE: Record<string, string> = {
  low: 'text-emerald-400 bg-emerald-500/5 px-2 py-0.5 rounded border border-emerald-500/10',
  medium: 'text-amber-400 bg-amber-500/5 px-2 py-0.5 rounded border border-amber-500/10',
  high: 'text-rose-400 bg-rose-500/5 px-2 py-0.5 rounded border border-rose-500/10'
};

export default function VendorDirectory() {
  const { rows: vendors, loading, error } = useCycomList<CycomVendor, VendorRow>(
    'cy.vendor',
    [],
    ['legal_name', 'trade_name', 'vendor_code', 'cr_number', 'tax_number', 'payment_terms_days', 'credit_limit', 'risk_rating', 'approval_status', 'category'],
    mapVendor,
    { limit: 200 }
  );

  const statusCounts = vendors.reduce<Record<string, number>>((acc, v) => {
    acc[v.status] = (acc[v.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6 text-xs md:text-sm">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Vendor Directory</h1>
          <p className="page-subtitle">Onboard, manage, and verify supplier credentials and compliance documentation.</p>
        </div>
        <Link 
          href="/purchase/vendors/new"
          className="btn-primary flex items-center gap-2"
        >
          <UserPlus className="w-4 h-4" /> Register Vendor
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Suppliers</span>
            <p className="text-2xl font-black text-white">{vendors.length}</p>
          </div>
          <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400">
            <Users className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Pending Review</span>
            <p className="text-2xl font-black text-amber-500">{statusCounts['submitted'] || statusCounts['under_review'] || 0}</p>
          </div>
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active & Approved</span>
            <p className="text-2xl font-black text-emerald-500">{statusCounts['approved'] || 0}</p>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Suspended/Rejected</span>
            <p className="text-2xl font-black text-rose-500">{(statusCounts['rejected'] || 0) + (statusCounts['suspended'] || 0)}</p>
          </div>
          <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {loading && <LoadingCard label="Loading supplier profiles…" />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && vendors.length === 0 && (
        <EmptyCard label="No vendors registered. Click 'Register Vendor' to onboard one." />
      )}

      {/* Grid List */}
      {!loading && !error && vendors.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">Onboarded Supplier Master</h2>
          <div className="overflow-x-auto">
            <table className="data-table text-left w-full border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-[10px] uppercase text-slate-500 tracking-wider font-semibold">
                  <th className="pb-3">Vendor Code</th>
                  <th className="pb-3">Legal Name</th>
                  <th className="pb-3">CR / TAX Number</th>
                  <th className="pb-3">Category</th>
                  <th className="pb-3">Terms & Limits</th>
                  <th className="pb-3">Risk Rating</th>
                  <th className="pb-3">Onboarding Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {vendors.map((v) => (
                  <tr key={v.rawId} className="hover:bg-white/[0.01] transition-all">
                    <td className="py-4 font-mono text-xs font-bold text-slate-400">
                      <Link href={`/purchase/vendors/${v.rawId}`} className="hover:text-blue-400 transition">
                        {v.id}
                      </Link>
                    </td>
                    <td className="py-4">
                      <div className="font-semibold text-slate-200">{v.legalName}</div>
                      {v.tradeName && <div className="text-[10px] text-slate-500 mt-0.5">{v.tradeName}</div>}
                    </td>
                    <td className="py-4">
                      <div className="text-slate-300 font-medium">CR: {v.crNumber}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">TAX: {v.taxNumber}</div>
                    </td>
                    <td className="py-4">
                      <span className="text-[10px] font-bold text-slate-400 px-2 py-0.5 bg-slate-800 border border-slate-700/50 rounded-md">
                        {v.category}
                      </span>
                    </td>
                    <td className="py-4">
                      <div className="text-slate-300 font-semibold">{v.creditLimit}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">{v.paymentTerms}</div>
                    </td>
                    <td className="py-4">
                      <span className={RISK_BADGE[v.riskRating] || RISK_BADGE['medium']}>
                        {v.riskRating.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-4">
                      <span className={`px-2.5 py-1 text-[10px] font-bold uppercase rounded-md tracking-wider ${STATUS_BADGE[v.status] || STATUS_BADGE['draft']}`}>
                        {v.status.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
