'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ShoppingCart } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface StoreProduct {
  id: string;
  name: string;
  description: string;
  image_url: string | null;
  sell_price: string;
  sku: string;
}

function cartTokenKey(slug: string) {
  return `cycom_store_cart_${slug}`;
}

export default function StorefrontPage() {
  const t = useT();
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;

  const [products, setProducts] = useState<StoreProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addingId, setAddingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/store/${slug}/products/`);
        if (!res.ok) throw new Error(t('storefront.loadFailed'));
        const data = await res.json();
        if (!cancelled) setProducts(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t('storefront.loadFailed'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [slug, t]);

  const ensureCartToken = async (): Promise<string> => {
    let token: string | null = null;
    try {
      token = localStorage.getItem(cartTokenKey(slug));
    } catch {
      /* private browsing / storage blocked — fall through to a fresh cart */
    }
    if (token) return token;

    const res = await fetch(`/api/store/${slug}/carts/`, { method: 'POST' });
    const data = await res.json();
    try {
      localStorage.setItem(cartTokenKey(slug), data.token);
    } catch {
      /* non-fatal — cart still works for this page view */
    }
    return data.token;
  };

  const addToCart = async (product: StoreProduct) => {
    setAddingId(product.id);
    try {
      const token = await ensureCartToken();
      const res = await fetch(`/api/store/${slug}/carts/${token}/items/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product: product.id, quantity: 1 }),
      });
      if (!res.ok) throw new Error(t('storefront.addToCartFailed'));
      router.push(`/store/${slug}/cart`);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('storefront.addToCartFailed'));
    } finally {
      setAddingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] text-white p-4 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <header className="flex items-center justify-between border-b border-white/5 pb-4">
          <h1 className="text-lg font-black text-white">{t('storefront.title')}</h1>
          <button
            onClick={() => router.push(`/store/${slug}/cart`)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:border-white/20 text-xs font-bold"
          >
            <ShoppingCart className="w-4 h-4" /> {t('storefront.viewCart')}
          </button>
        </header>

        {loading && <p className="text-slate-500 text-sm">{t('storefront.loading')}</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}
        {!loading && !error && products.length === 0 && (
          <p className="text-slate-500 text-sm italic">{t('storefront.empty')}</p>
        )}

        {!loading && !error && products.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
            {products.map((p) => (
              <div key={p.id} className="glass-card p-5 space-y-3 flex flex-col">
                {p.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={p.image_url} alt={p.name} className="w-full h-40 object-cover rounded-xl" />
                ) : (
                  <div className="w-full h-40 rounded-xl bg-white/5 flex items-center justify-center text-slate-600 text-xs">
                    {t('storefront.noImage')}
                  </div>
                )}
                <div className="flex-1 space-y-1">
                  <h3 className="text-sm font-bold text-white">{p.name}</h3>
                  {p.description && <p className="text-xs text-slate-400 line-clamp-2">{p.description}</p>}
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-white/5">
                  <span className="text-base font-black text-white">{Number(p.sell_price).toFixed(2)}</span>
                  <button
                    onClick={() => addToCart(p)}
                    disabled={addingId === p.id}
                    className="btn-primary py-1.5 px-3 text-xs disabled:opacity-50"
                  >
                    {addingId === p.id ? t('storefront.adding') : t('storefront.addToCart')}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
