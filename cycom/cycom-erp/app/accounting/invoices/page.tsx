'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Receipt, Search, Loader2 } from 'lucide-react';
import { useT } from '@/lib/i18n';
import { LoadingCard } from '@/components/CycomEmptyStates';
import { statusTone, REAL_INVOICE_STATE } from '@/lib/status';

interface InvoiceRow {
  id: string;
  number: string;
  invoice_type: string;
  partner_name: string;
  date: string;
  due_date: string;
  currency: string;
  amount_total: string;
  status: string;
}

export default function InvoicesPage() {
  const t = useT();
  const router = useRouter();
  const [rows, setRows] = useState<InvoiceRow[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [search, setSearch] = useState('');

  // The invoices endpoint uses the project-wide PageNumberPagination, so
  // walk it page by page instead of silently showing only the first 25.
  useEffect(() => {
    const first = page === 1;
    first ? setLoading(true) : setLoadingMore(true);
    fetch(`/api/cycom/rest/ar-ap/invoices/?page=${page}`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        const results: InvoiceRow[] = Array.isArray(data) ? data : data?.results || [];
        setRows((prev) => (first ? results : [...prev, ...results]));
        setHasMore(Boolean(data && !Array.isArray(data) && data.next));
      })
      .finally(() => { setLoading(false); setLoadingMore(false); });
  }, [page]);

  const q = search.trim().toLowerCase();
  const filtered = rows.filter((r) =>
    !q || r.number.toLowerCase().includes(q) || (r.partner_name || '').toLowerCase().includes(q)
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-8 text-xs md:text-sm">
      <div className="max-w-5xl mx-auto flex items-center gap-4 mb-8">
        <button onClick={() => router.push('/accounting')} className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition">
          <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Receipt className="w-6 h-6 text-cyan-400" /> {t('invoices.title')}
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('invoices.subtitle')}</p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto space-y-4">
        <div className="relative max-w-sm">
          <Search className="w-4 h-4 text-slate-500 absolute start-3 top-1/2 -translate-y-1/2" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('invoices.search')}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg ps-9 pe-3 py-2 text-slate-200 outline-none"
          />
        </div>

        {loading ? (
          <LoadingCard label={t('invoices.loading')} />
        ) : filtered.length === 0 ? (
          <div className="glass-card p-10 text-center text-slate-500">{t('invoices.empty')}</div>
        ) : (
          <div className="glass-card overflow-x-auto">
            <table className="w-full min-w-[640px] text-xs">
              <thead>
                <tr className="bg-slate-950 text-slate-500 uppercase border-b border-slate-850">
                  <th className="p-3 text-start font-bold">{t('invoices.colNumber')}</th>
                  <th className="p-3 text-start font-bold">{t('invoices.colPartner')}</th>
                  <th className="p-3 text-start font-bold">{t('invoices.colType')}</th>
                  <th className="p-3 text-start font-bold">{t('invoices.colDate')}</th>
                  <th className="p-3 text-start font-bold">{t('invoices.colDue')}</th>
                  <th className="p-3 text-end font-bold">{t('invoices.colTotal')}</th>
                  <th className="p-3 text-end font-bold">{t('invoices.colStatus')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filtered.map((inv) => {
                  const statusKey = REAL_INVOICE_STATE[inv.status] || 'unknown';
                  return (
                    <tr
                      key={inv.id}
                      onClick={() => router.push(`/accounting/invoices/${inv.id}`)}
                      className="cursor-pointer hover:bg-white/5 transition-colors"
                    >
                      <td className="p-3 font-mono text-slate-200">{inv.number}</td>
                      <td className="p-3 text-slate-200"><bdi>{inv.partner_name}</bdi></td>
                      <td className="p-3 text-slate-400">{t(`invoices.type.${inv.invoice_type}`)}</td>
                      <td className="p-3 text-slate-400">{inv.date}</td>
                      <td className="p-3 text-slate-400">{inv.due_date}</td>
                      <td className="p-3 text-end font-mono text-slate-200">{inv.currency} {Number(inv.amount_total).toFixed(2)}</td>
                      <td className="p-3 text-end"><span className={`badge ${statusTone(statusKey)}`}>{t(`status.${statusKey}`)}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {hasMore && !loading && (
          <div className="flex justify-center">
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={loadingMore}
              className="flex items-center gap-2 px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition text-xs font-semibold disabled:opacity-50"
            >
              {loadingMore && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {t('invoices.loadMore')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
