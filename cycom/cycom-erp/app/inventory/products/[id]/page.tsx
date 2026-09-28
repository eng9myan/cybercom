'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Package, Tag, Boxes } from 'lucide-react';
import { useT } from '@/lib/i18n';
import CustomFieldsPanel from '@/components/CustomFieldsPanel';
import { LoadingCard } from '@/components/CycomEmptyStates';

interface ProductDetail {
  id: string;
  name: string;
  internal_ref: string;
  barcode: string;
  description: string;
  product_type: string;
  category_name: string | null;
  unit_name: string | null;
  cost_price: string;
  sell_price: string;
  min_stock_qty: string;
  track_stock: boolean;
  is_active: boolean;
}

export default function ProductDetailPage() {
  const t = useT();
  const router = useRouter();
  const params = useParams();
  const productId = params?.id as string;

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!productId) return;
    fetch(`/api/cycom/rest/inventory/products/${productId}/`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then(setProduct)
      .finally(() => setLoading(false));
  }, [productId]);

  if (loading) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8"><LoadingCard label={t('productDetail.loading')} /></div>;
  if (!product) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-center text-slate-400">{t('productDetail.notFound')}</div>;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-4xl mx-auto flex items-center gap-4 mb-8">
        <button onClick={() => router.push('/inventory/products')} className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition">
          <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Package className="w-6 h-6 text-cyan-400" /> {product.name}
            {!product.is_active && <span className="text-xs font-normal text-slate-500 uppercase">{t('productCatalog.inactive')}</span>}
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">{product.internal_ref || '—'}</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-3">
              <Tag className="w-4 h-4 text-cyan-400" /> {t('productDetail.identityHeading')}
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('productCatalog.colType')}</label>
                <div className="text-slate-200 font-semibold mt-0.5">{product.product_type}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('productCatalog.colCategory')}</label>
                <div className="text-slate-200 mt-0.5">{product.category_name || '—'}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('productDetail.unit')}</label>
                <div className="text-slate-200 mt-0.5">{product.unit_name || '—'}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('productDetail.barcode')}</label>
                <div className="text-slate-200 font-mono mt-0.5" dir="ltr">{product.barcode || '—'}</div>
              </div>
            </div>
            {product.description && (
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('productDetail.description')}</label>
                <p className="text-slate-300 mt-0.5 leading-relaxed">{product.description}</p>
              </div>
            )}
          </div>

          <div className="glass-card p-6 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-3">
              <Boxes className="w-4 h-4 text-emerald-400" /> {t('productDetail.pricingStockHeading')}
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('productDetail.costPrice')}</label>
                <div className="text-slate-200 font-mono mt-0.5">{Number(product.cost_price).toFixed(4)}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('productCatalog.colPrice')}</label>
                <div className="text-emerald-400 font-bold font-mono mt-0.5">{Number(product.sell_price).toFixed(4)}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('productDetail.trackStock')}</label>
                <div className="text-slate-200 mt-0.5">{product.track_stock ? t('common.yes') : t('common.no')}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t('productDetail.minStockQty')}</label>
                <div className="text-slate-200 font-mono mt-0.5">{Number(product.min_stock_qty).toFixed(2)}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <CustomFieldsPanel modelKey="product" recordId={productId} />
        </div>
      </div>
    </div>
  );
}
