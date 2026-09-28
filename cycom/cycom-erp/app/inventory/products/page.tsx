'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Package, Search } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface ProductRow {
  id: string;
  name: string;
  internal_ref: string;
  barcode: string;
  product_type: string;
  category_name: string | null;
  sell_price: string;
  is_active: boolean;
}

export default function ProductCatalogPage() {
  const t = useT();
  const router = useRouter();
  const [products, setProducts] = useState<ProductRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetch('/api/cycom/rest/inventory/products/', { credentials: 'include' })
      .then((r) => r.json())
      .then((data) => setProducts(data.results || data || []))
      .finally(() => setLoading(false));
  }, []);

  const filtered = products.filter((p) =>
    !search.trim() ||
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.internal_ref.toLowerCase().includes(search.toLowerCase()) ||
    p.barcode.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-5xl mx-auto flex items-center gap-4 mb-8">
        <button onClick={() => router.push('/inventory')} className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition">
          <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent flex items-center gap-2">
            <Package className="w-6 h-6 text-cyan-400" /> {t('productCatalog.title')}
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('productCatalog.subtitle')}</p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto space-y-4">
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 max-w-sm">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder={t('productCatalog.searchPh')}
            className="bg-transparent border-none outline-none text-slate-200 w-full"
          />
        </div>

        <div className="glass-card p-0 overflow-hidden">
          {loading ? (
            <div className="py-10 text-center text-slate-500">{t('productCatalog.loading')}</div>
          ) : filtered.length === 0 ? (
            <div className="py-10 text-center text-slate-500">{t('productCatalog.emptyState')}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-xs">
                <thead>
                  <tr className="bg-slate-950 text-slate-500 uppercase border-b border-slate-850">
                    <th className="p-3 text-start font-bold">{t('productCatalog.colName')}</th>
                    <th className="p-3 text-start font-bold">{t('productCatalog.colSku')}</th>
                    <th className="p-3 text-start font-bold">{t('productCatalog.colType')}</th>
                    <th className="p-3 text-start font-bold">{t('productCatalog.colCategory')}</th>
                    <th className="p-3 text-end font-bold">{t('productCatalog.colPrice')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filtered.map((p) => (
                    <tr key={p.id} className="hover:bg-white/5 transition-colors">
                      <td className="p-3">
                        <Link href={`/inventory/products/${p.id}`} className="font-semibold text-slate-200 hover:text-cyan-400 transition-colors">
                          {p.name}
                        </Link>
                        {!p.is_active && <span className="ms-2 text-[9px] text-slate-600 uppercase">{t('productCatalog.inactive')}</span>}
                      </td>
                      <td className="p-3 font-mono text-slate-400">{p.internal_ref || '—'}</td>
                      <td className="p-3 text-slate-400">{p.product_type}</td>
                      <td className="p-3 text-slate-400">{p.category_name || '—'}</td>
                      <td className="p-3 text-end font-bold text-slate-200">{Number(p.sell_price).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
