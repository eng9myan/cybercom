'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Receipt, ListOrdered, BookCheck, Loader2, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useT } from '@/lib/i18n';
import { LoadingCard } from '@/components/CycomEmptyStates';
import { statusTone, REAL_INVOICE_STATE } from '@/lib/status';
import { formatApiErrors } from '@/lib/apiErrors';
import InvoiceEInvoicePanel from '@/components/InvoiceEInvoicePanel';

interface InvoiceLine {
  id: string;
  account_name: string;
  description: string;
  quantity: string;
  unit_price: string;
  tax_percent: string;
  subtotal: string;
}

interface InvoiceDetail {
  id: string;
  number: string;
  invoice_type: string;
  partner_name: string;
  date: string;
  due_date: string;
  currency: string;
  status: string;
  amount_subtotal: string;
  amount_tax: string;
  amount_total: string;
  amount_due: string;
  lines: InvoiceLine[];
}

export default function InvoiceDetailPage() {
  const t = useT();
  const router = useRouter();
  const params = useParams();
  const invoiceId = params?.id as string;

  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);
  const [postError, setPostError] = useState<string[] | null>(null);
  const [justPosted, setJustPosted] = useState(false);

  useEffect(() => {
    if (!invoiceId) return;
    fetch(`/api/cycom/rest/ar-ap/invoices/${invoiceId}/`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then(setInvoice)
      .finally(() => setLoading(false));
  }, [invoiceId]);

  const handlePost = async () => {
    setPosting(true);
    setPostError(null);
    try {
      const resp = await fetch(`/api/cycom/rest/ar-ap/invoices/${invoiceId}/post/`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const body = await resp.json().catch(() => null);
      if (resp.ok && body) {
        setInvoice(body);
        setJustPosted(true);
      } else {
        setPostError(formatApiErrors(body).length ? formatApiErrors(body) : [String(resp.status)]);
      }
    } finally {
      setPosting(false);
    }
  };

  if (loading) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8"><LoadingCard label={t('invoices.loading')} /></div>;
  if (!invoice) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-center text-slate-400">{t('invoices.notFound')}</div>;

  const statusKey = REAL_INVOICE_STATE[invoice.status] || 'unknown';
  const money = (v: string) => `${invoice.currency} ${Number(v).toFixed(2)}`;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-8 text-xs md:text-sm">
      <div className="max-w-4xl mx-auto flex flex-wrap items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-4 min-w-0">
          <button onClick={() => router.push('/accounting/invoices')} className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition">
            <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
          </button>
          <div className="min-w-0">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
              <Receipt className="w-6 h-6 text-cyan-400 flex-shrink-0" /> <bdi className="truncate">{invoice.partner_name}</bdi>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              <bdi className="font-mono">{invoice.number}</bdi> · {t(`invoices.type.${invoice.invoice_type}`)}
            </p>
          </div>
        </div>
        <span className={`badge ${statusTone(statusKey)}`}>{t(`status.${statusKey}`)}</span>
      </div>

      <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-3">
            <ListOrdered className="w-4 h-4 text-cyan-400" /> {t('invoices.linesHeading')}
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-xs">
              <thead>
                <tr className="bg-slate-950 text-slate-500 uppercase border-b border-slate-850">
                  <th className="p-2 text-start font-bold">{t('invoices.colDescription')}</th>
                  <th className="p-2 text-start font-bold">{t('invoices.colAccount')}</th>
                  <th className="p-2 text-end font-bold">{t('invoices.colQty')}</th>
                  <th className="p-2 text-end font-bold">{t('invoices.colUnitPrice')}</th>
                  <th className="p-2 text-end font-bold">{t('invoices.colTax')}</th>
                  <th className="p-2 text-end font-bold">{t('invoices.colAmount')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {invoice.lines.map((line) => (
                  <tr key={line.id}>
                    <td className="p-2 text-slate-200">{line.description || '—'}</td>
                    <td className="p-2 text-slate-400">{line.account_name}</td>
                    <td className="p-2 text-end font-mono text-slate-300">{Number(line.quantity).toFixed(2)}</td>
                    <td className="p-2 text-end font-mono text-slate-300">{Number(line.unit_price).toFixed(2)}</td>
                    <td className="p-2 text-end font-mono text-slate-400">{Number(line.tax_percent).toFixed(2)}</td>
                    <td className="p-2 text-end font-mono text-slate-200">{Number(line.subtotal).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="space-y-1.5 border-t border-white/10 pt-3">
            <div className="flex justify-between text-slate-400"><span>{t('invoices.subtotal')}</span><span className="font-mono">{money(invoice.amount_subtotal)}</span></div>
            <div className="flex justify-between text-slate-400"><span>{t('invoices.tax')}</span><span className="font-mono">{money(invoice.amount_tax)}</span></div>
            <div className="flex justify-between text-sm font-black text-white"><span>{t('invoices.total')}</span><span className="text-cyan-400 font-mono">{money(invoice.amount_total)}</span></div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-card p-6 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5 pb-3">{t('invoices.details')}</h3>
            <div className="flex justify-between"><span className="text-slate-500">{t('invoices.date')}</span><span className="text-slate-200">{invoice.date}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">{t('invoices.dueDate')}</span><span className="text-slate-200">{invoice.due_date}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">{t('invoices.currency')}</span><span className="text-slate-200">{invoice.currency}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">{t('invoices.amountDue')}</span><span className="text-slate-200 font-mono">{money(invoice.amount_due)}</span></div>
          </div>

          {invoice.status === 'draft' && (
            <button
              onClick={handlePost}
              disabled={posting}
              className="w-full flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-white font-semibold transition text-xs"
            >
              {posting ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookCheck className="w-4 h-4" />}
              {posting ? t('invoices.posting') : t('invoices.post')}
            </button>
          )}
          {justPosted && (
            <div className="flex items-start gap-2 p-3 rounded-lg border bg-emerald-950/40 border-emerald-500/20 text-emerald-400">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" /> {t('invoices.postedNote')}
            </div>
          )}
          {(invoice.invoice_type === 'customer' || invoice.invoice_type === 'customer_credit_note') && (
            <InvoiceEInvoicePanel invoiceId={invoice.id} invoiceStatus={invoice.status} />
          )}
          {postError && (
            <div className="flex items-start gap-2 p-3 rounded-lg border bg-rose-950/40 border-rose-500/20 text-rose-400">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">{t('invoices.postFailed')}</p>
                {postError.map((line, i) => <p key={i}>{line}</p>)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
