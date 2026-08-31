'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { ChefHat, Clock, Flame, CheckCircle2, ArrowRight, RefreshCw } from 'lucide-react';

// Kitchen Display System. Renders the live ticket feed from
//   GET /api/cycom/rest/pos/orders/kds/
// and advances a ticket's stage via
//   POST /api/cycom/rest/pos/orders/<id>/kitchen-status/  {advance:true}
// (backend: products.cycom.pos — Device type "KDS" maps to this /kds route.)

type Line = { id: string; product?: string; product_name?: string; quantity?: string; description?: string };
type Ticket = {
  id: string;
  order_number: string;
  kitchen_status: 'pending' | 'in_progress' | 'ready' | 'served';
  table_ref?: string;
  customer_name?: string;
  source?: string;
  created_at?: string;
  lines?: Line[];
};

const LANES: { key: Ticket['kitchen_status']; label: string; icon: any; accent: string }[] = [
  { key: 'pending', label: 'New', icon: Clock, accent: '#F59E0B' },
  { key: 'in_progress', label: 'Cooking', icon: Flame, accent: '#E67E22' },
  { key: 'ready', label: 'Ready to serve', icon: CheckCircle2, accent: '#10B981' },
];

const POLL_MS = 5000;

export default function KdsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [lastSync, setLastSync] = useState<Date | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch('/api/cycom/rest/pos/orders/kds/', { credentials: 'include' });
      if (!res.ok) throw new Error(`Backend ${res.status}`);
      const data = await res.json();
      const rows: Ticket[] = Array.isArray(data) ? data : data.results || [];
      setTickets(rows);
      setError(null);
      setLastSync(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tickets');
    }
  }, []);

  useEffect(() => {
    // Subscribe to the ticket feed: initial fetch + poll. load() only setStates
    // after an awaited network round-trip, so this isn't the synchronous
    // cascading-render pattern the rule guards against.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, [load]);

  async function advance(ticket: Ticket) {
    setBusy(ticket.id);
    try {
      const res = await fetch(`/api/cycom/rest/pos/orders/${ticket.id}/kitchen-status/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ advance: true }),
      });
      if (!res.ok) throw new Error(`Backend ${res.status}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setBusy(null);
    }
  }

  const byLane = (k: Ticket['kitchen_status']) => tickets.filter((t) => t.kitchen_status === k);

  return (
    <div className="min-h-screen bg-[#030712] text-white p-6">
      <header className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#E67E22] to-[#D35400] flex items-center justify-center">
            <ChefHat className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-wide">Kitchen Display</h1>
            <p className="text-[10px] text-white/40 uppercase tracking-widest font-bold">
              {tickets.length} active ticket{tickets.length === 1 ? '' : 's'}
              {lastSync && <> · synced {lastSync.toLocaleTimeString()}</>}
            </p>
          </div>
        </div>
        <button onClick={load} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </header>

      {error && (
        <div className="mb-4 p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-sm">{error}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {LANES.map((lane) => {
          const items = byLane(lane.key);
          const Icon = lane.icon;
          return (
            <div key={lane.key} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
              <div className="flex items-center gap-2 mb-3 px-1">
                <Icon className="w-4 h-4" style={{ color: lane.accent }} />
                <span className="font-bold text-sm">{lane.label}</span>
                <span className="ml-auto text-xs text-white/40 font-mono">{items.length}</span>
              </div>

              <div className="space-y-3">
                {items.length === 0 && (
                  <p className="text-xs text-white/25 text-center py-8">No tickets</p>
                )}
                {items.map((t) => (
                  <div key={t.id} className="rounded-xl border p-3" style={{ borderColor: `${lane.accent}55`, background: `${lane.accent}0d` }}>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm font-mono">{t.order_number}</span>
                      {t.table_ref && <span className="text-xs px-2 py-0.5 rounded bg-white/10">Table {t.table_ref}</span>}
                    </div>
                    <div className="text-xs text-white/50 mt-0.5">
                      {t.customer_name || 'Walk-in'}{t.source && t.source !== 'POS' && <> · {t.source}</>}
                    </div>
                    {t.lines && t.lines.length > 0 && (
                      <ul className="mt-2 space-y-0.5 text-xs text-white/70">
                        {t.lines.slice(0, 6).map((l) => (
                          <li key={l.id} className="flex justify-between">
                            <span>{l.product_name || l.description || 'Item'}</span>
                            {l.quantity && <span className="text-white/40 font-mono">×{parseFloat(l.quantity)}</span>}
                          </li>
                        ))}
                      </ul>
                    )}
                    <button
                      onClick={() => advance(t)}
                      disabled={busy === t.id}
                      className="mt-3 w-full text-xs font-bold rounded-lg py-2 flex items-center justify-center gap-1.5 disabled:opacity-50"
                      style={{ background: lane.accent, color: '#0B0F19' }}
                    >
                      {busy === t.id ? 'Updating…' : (
                        <>{lane.key === 'ready' ? 'Mark served' : 'Advance'} <ArrowRight className="w-3.5 h-3.5" /></>
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
