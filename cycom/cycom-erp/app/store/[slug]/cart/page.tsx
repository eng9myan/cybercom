'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Trash2, ArrowLeft } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface CartLine {
  id: string;
  product: string;
  product_name: string;
  quantity: number;
  unit_price: string;
}

interface CartData {
  token: string;
  status: string;
  lines: CartLine[];
}

function cartTokenKey(slug: string) {
  return `cycom_store_cart_${slug}`;
}

export default function StorefrontCartPage() {
  const t = useT();
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;

  const [cart, setCart] = useState<CartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [confirmation, setConfirmation] = useState<{ order_number: string; total: string } | null>(null);

  const loadCart = async () => {
    let token: string | null = null;
    try {
      token = localStorage.getItem(cartTokenKey(slug));
    } catch {
      /* ignore */
    }
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(`/api/store/${slug}/carts/${token}/`);
      if (!res.ok) throw new Error(t('storefront.loadFailed'));
      setCart(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : t('storefront.loadFailed'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCart();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  const removeLine = async (productId: string) => {
    if (!cart) return;
    try {
      const res = await fetch(`/api/store/${slug}/carts/${cart.token}/items/${productId}/`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error(t('storefront.removeFailed'));
      setCart(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : t('storefront.removeFailed'));
    }
  };

  const total = (cart?.lines ?? []).reduce(
    (sum, l) => sum + Number(l.unit_price) * l.quantity, 0,
  );

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cart || !name) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/store/${slug}/carts/${cart.token}/checkout/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_name: name, customer_email: email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t('storefront.checkoutFailed'));
      setConfirmation(data);
      try {
        localStorage.removeItem(cartTokenKey(slug));
      } catch {
        /* ignore */
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t('storefront.checkoutFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  if (confirmation) {
    return (
      <div className="min-h-screen bg-[#030712] text-white flex items-center justify-center p-6 font-sans">
        <div className="glass-card p-8 max-w-md w-full text-center space-y-4">
          <h2 className="text-lg font-black text-white">{t('storefront.orderConfirmed')}</h2>
          <p className="text-sm text-slate-400">
            {t('storefront.orderNumberLabel')} <span className="font-mono text-white">{confirmation.order_number}</span>
          </p>
          <p className="text-2xl font-black text-white">{Number(confirmation.total).toFixed(2)}</p>
          <button onClick={() => router.push(`/store/${slug}`)} className="btn-primary w-full py-2">
            {t('storefront.continueShopping')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#030712] text-white p-4 md:p-8 font-sans">
      <div className="max-w-2xl mx-auto space-y-6">
        <header className="flex items-center gap-3 border-b border-white/5 pb-4">
          <button onClick={() => router.push(`/store/${slug}`)} className="text-slate-400 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-lg font-black text-white">{t('storefront.yourCart')}</h1>
        </header>

        {loading && <p className="text-slate-500 text-sm">{t('storefront.loading')}</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}

        {!loading && (!cart || cart.lines.length === 0) && (
          <p className="text-slate-500 text-sm italic">{t('storefront.cartEmpty')}</p>
        )}

        {!loading && cart && cart.lines.length > 0 && (
          <>
            <div className="space-y-3">
              {cart.lines.map((l) => (
                <div key={l.id} className="glass-card p-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-bold text-white">{l.product_name}</p>
                    <p className="text-xs text-slate-500">{t('storefront.qtyLabel', { qty: l.quantity })}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm text-white">
                      {(Number(l.unit_price) * l.quantity).toFixed(2)}
                    </span>
                    <button onClick={() => removeLine(l.product)} className="text-slate-500 hover:text-red-400">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="glass-card p-4 flex items-center justify-between">
              <span className="text-sm font-bold text-slate-400">{t('storefront.total')}</span>
              <span className="text-xl font-black text-white">{total.toFixed(2)}</span>
            </div>

            <form onSubmit={handleCheckout} className="glass-card p-5 space-y-3">
              <h3 className="text-sm font-bold text-white">{t('storefront.checkoutHeading')}</h3>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('storefront.nameLabel')}</label>
                <input
                  type="text" required value={name} onChange={(e) => setName(e.target.value)}
                  className="input-field" placeholder={t('storefront.namePlaceholder')}
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('storefront.emailLabel')}</label>
                <input
                  type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  className="input-field" placeholder={t('storefront.emailPlaceholder')} dir="ltr"
                />
              </div>
              <button type="submit" disabled={submitting} className="btn-primary w-full py-2.5 disabled:opacity-50">
                {submitting ? t('storefront.placingOrder') : t('storefront.placeOrder')}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
