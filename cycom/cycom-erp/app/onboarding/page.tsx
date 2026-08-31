'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Percent, Ruler, Warehouse as WarehouseIcon, Package, Rocket,
  ArrowRight, ArrowLeft, Check, AlertCircle,
} from 'lucide-react';

// Commerce quick-setup. cyshop's original onboarding drove per-Company/Branch
// tenant endpoints that Cycom doesn't have; Cycom scopes by tenant_id and its
// generic /setup wizard already covers company/industry/provisioning. So this
// route does the retail-specific piece /setup doesn't: bootstrap the catalog +
// a warehouse so POS/KDS have something to sell. Every step writes a REAL row
// through the DRF endpoints (products.cycom.catalog / inventory).

const CURRENCIES = ['JOD', 'SAR', 'AED', 'USD', 'EUR', 'GBP'];

const STEPS = [
  { id: 1, label: 'Tax', icon: Percent },
  { id: 2, label: 'Unit', icon: Ruler },
  { id: 3, label: 'Warehouse', icon: WarehouseIcon },
  { id: 4, label: 'First product', icon: Package },
  { id: 5, label: 'Go live', icon: Rocket },
];

async function post(path: string, body: unknown) {
  const res = await fetch(`/api/cycom/rest/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data?.detail || data?.error?.message || JSON.stringify(data) || `HTTP ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : 'Request failed');
  }
  return data;
}

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const [currency, setCurrency] = useState('JOD');
  const [tax, setTax] = useState({ name: 'Standard', code: 'STD', rate: '16' });
  const [unit, setUnit] = useState({ name: 'Piece', abbreviation: 'pc' });
  const [wh, setWh] = useState({ code: 'WH-MAIN', name: 'Main Warehouse' });
  const [product, setProduct] = useState({ name: '', sell_price: '' });

  // ids created along the way (so downstream steps can link + review can show)
  const [created, setCreated] = useState<{ taxId?: string; unitId?: string; whId?: string; productId?: string }>({});

  const advance = () => { setError(''); setStep((s) => Math.min(s + 1, 5)); };
  const back = () => { setError(''); setStep((s) => Math.max(s - 1, 1)); };

  const saveTax = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const row = await post('catalog/tax-classes/', {
        name: tax.name, code: tax.code,
        rate: (parseFloat(tax.rate || '0') / 100).toFixed(4),
      });
      setCreated((c) => ({ ...c, taxId: row.id }));
      if (typeof window !== 'undefined') localStorage.setItem('cycom.currency', currency);
      advance();
    } catch (err) { setError(err instanceof Error ? err.message : 'Failed'); } finally { setSaving(false); }
  };

  const saveUnit = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const row = await post('catalog/units/', unit);
      setCreated((c) => ({ ...c, unitId: row.id }));
      advance();
    } catch (err) { setError(err instanceof Error ? err.message : 'Failed'); } finally { setSaving(false); }
  };

  const saveWarehouse = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const row = await post('inventory/warehouses/', wh);
      setCreated((c) => ({ ...c, whId: row.id }));
      advance();
    } catch (err) { setError(err instanceof Error ? err.message : 'Failed'); } finally { setSaving(false); }
  };

  const saveProduct = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const row = await post('catalog/products/', {
        name: product.name,
        sell_price: parseFloat(product.sell_price || '0').toFixed(4),
        product_type: 'STORABLE',
        tax_class: created.taxId || null,
        unit: created.unitId || null,
        pos_available: true,
      });
      setCreated((c) => ({ ...c, productId: row.id }));
      advance();
    } catch (err) { setError(err instanceof Error ? err.message : 'Failed'); } finally { setSaving(false); }
  };

  const S = STEPS[step - 1];

  return (
    <div className="min-h-screen bg-[#030712] text-white flex flex-col">
      <header className="h-16 px-6 flex items-center border-b border-white/10">
        <span className="font-black text-lg tracking-wide">Commerce Setup</span>
        <span className="ml-3 text-[10px] text-[#E67E22] uppercase tracking-widest font-bold">Cycom</span>
      </header>

      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-xl">
          <div className="flex items-center gap-2 mb-8">
            {STEPS.map((s, i) => (
              <div key={s.id} className="flex items-center gap-2 flex-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center border transition shrink-0 ${
                  step > s.id ? 'bg-[#E67E22] border-[#E67E22]' : step === s.id ? 'border-[#E67E22] text-[#E67E22]' : 'border-white/15 text-white/30'
                }`}>
                  {step > s.id ? <Check className="w-4 h-4" /> : <s.icon className="w-4 h-4" />}
                </div>
                {i < STEPS.length - 1 && <div className="flex-1 h-px bg-white/10" />}
              </div>
            ))}
          </div>

          <div className="glass-card p-8">
            <h1 className="text-2xl font-black mb-1">{S.label}</h1>
            <p className="text-sm text-white/50 mb-6">Step {step} of {STEPS.length}</p>

            {error && (
              <div className="mb-5 flex items-start gap-2 p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-sm">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" /><span>{error}</span>
              </div>
            )}

            {step === 1 && (
              <form onSubmit={saveTax} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-white/60 block mb-1.5">Base Currency</label>
                  <select className="input-field w-full" value={currency} onChange={(e) => setCurrency(e.target.value)}>
                    {CURRENCIES.map((c) => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="col-span-1">
                    <label className="text-xs font-semibold text-white/60 block mb-1.5">Tax name</label>
                    <input className="input-field w-full" value={tax.name} onChange={(e) => setTax((t) => ({ ...t, name: e.target.value }))} />
                  </div>
                  <div className="col-span-1">
                    <label className="text-xs font-semibold text-white/60 block mb-1.5">Code</label>
                    <input className="input-field w-full" value={tax.code} onChange={(e) => setTax((t) => ({ ...t, code: e.target.value }))} />
                  </div>
                  <div className="col-span-1">
                    <label className="text-xs font-semibold text-white/60 block mb-1.5">Rate (%)</label>
                    <input type="number" step="0.01" min="0" className="input-field w-full" value={tax.rate} onChange={(e) => setTax((t) => ({ ...t, rate: e.target.value }))} />
                  </div>
                </div>
                <button disabled={saving} className="btn-primary w-full flex items-center justify-center gap-2">
                  {saving ? 'Saving…' : <>Continue <ArrowRight className="w-4 h-4" /></>}
                </button>
              </form>
            )}

            {step === 2 && (
              <form onSubmit={saveUnit} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-white/60 block mb-1.5">Unit name</label>
                    <input className="input-field w-full" value={unit.name} onChange={(e) => setUnit((u) => ({ ...u, name: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-white/60 block mb-1.5">Abbreviation</label>
                    <input className="input-field w-full" value={unit.abbreviation} onChange={(e) => setUnit((u) => ({ ...u, abbreviation: e.target.value }))} />
                  </div>
                </div>
                <StepButtons saving={saving} onBack={back} />
              </form>
            )}

            {step === 3 && (
              <form onSubmit={saveWarehouse} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-white/60 block mb-1.5">Warehouse code</label>
                    <input className="input-field w-full" value={wh.code} onChange={(e) => setWh((w) => ({ ...w, code: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-white/60 block mb-1.5">Name</label>
                    <input className="input-field w-full" value={wh.name} onChange={(e) => setWh((w) => ({ ...w, name: e.target.value }))} />
                  </div>
                </div>
                <StepButtons saving={saving} onBack={back} />
              </form>
            )}

            {step === 4 && (
              <form onSubmit={saveProduct} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-white/60 block mb-1.5">Product name *</label>
                  <input required className="input-field w-full" value={product.name} onChange={(e) => setProduct((p) => ({ ...p, name: e.target.value }))} placeholder="e.g. Espresso" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-white/60 block mb-1.5">Sell price ({currency})</label>
                  <input type="number" step="0.01" min="0" className="input-field w-full" value={product.sell_price} onChange={(e) => setProduct((p) => ({ ...p, sell_price: e.target.value }))} />
                </div>
                <StepButtons saving={saving} onBack={back} disabled={!product.name} />
              </form>
            )}

            {step === 5 && (
              <div className="space-y-5">
                <div className="rounded-xl bg-white/5 border border-white/10 p-4 space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-white/50">Currency</span><span className="font-semibold">{currency}</span></div>
                  <div className="flex justify-between"><span className="text-white/50">Tax class</span><span className="font-semibold">{tax.name} ({tax.rate}%)</span></div>
                  <div className="flex justify-between"><span className="text-white/50">Unit</span><span className="font-semibold">{unit.name}</span></div>
                  <div className="flex justify-between"><span className="text-white/50">Warehouse</span><span className="font-semibold">{wh.name}</span></div>
                  <div className="flex justify-between"><span className="text-white/50">First product</span><span className="font-semibold">{product.name || '—'}</span></div>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => router.push('/pos')} className="btn-secondary flex-1 flex items-center justify-center gap-2">Open POS</button>
                  <button onClick={() => router.push('/kds')} className="btn-primary flex-1 flex items-center justify-center gap-2">
                    Open Kitchen <Rocket className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function StepButtons({ saving, onBack, disabled }: { saving: boolean; onBack: () => void; disabled?: boolean }) {
  return (
    <div className="flex gap-3 pt-1">
      <button type="button" onClick={onBack} className="btn-secondary flex-1 flex items-center justify-center gap-2">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>
      <button disabled={saving || disabled} className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50">
        {saving ? 'Saving…' : <>Continue <ArrowRight className="w-4 h-4" /></>}
      </button>
    </div>
  );
}
