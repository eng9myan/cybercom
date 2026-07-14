"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { ChefHat, Clock, CheckCircle2, ArrowRight, LogOut, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";

const COLUMNS = [
  { status: "PENDING", label: "New", next: "IN_PROGRESS", nextLabel: "Start", color: "#DC2626" },
  { status: "IN_PROGRESS", label: "Cooking", next: "READY", nextLabel: "Ready", color: "#ED6C00" },
  { status: "READY", label: "Ready to Serve", next: "SERVED", nextLabel: "Served", color: "#16A34A" },
];

const POLL_MS = 8000;

function Ticket({ order, next, nextLabel, color, onAdvance, busy }) {
  const age = Math.max(0, Math.round((Date.now() - new Date(order.created_at).getTime()) / 60000));
  return (
    <div className="rounded-xl border-2 bg-[#111] p-4 flex flex-col gap-2" style={{ borderColor: color }}>
      <div className="flex items-center justify-between">
        <span className="font-mono font-bold text-lg text-white">{order.order_number}</span>
        <span className="flex items-center gap-1 text-xs text-white/60"><Clock className="w-3 h-3" /> {age}m</span>
      </div>
      {order.table_ref && <div className="text-xs text-white/50">Table {order.table_ref}</div>}
      <div className="text-sm text-white/80">{order.line_count} item{order.line_count !== 1 ? "s" : ""}</div>
      <button
        disabled={busy}
        onClick={() => onAdvance(order.id, next)}
        className="mt-2 w-full py-2 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 text-white disabled:opacity-50"
        style={{ background: color }}
      >
        {nextLabel} <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}

export default function KdsPage() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const timerRef = useRef(null);

  useEffect(() => {
    const token = typeof window !== "undefined" && localStorage.getItem("access_token");
    if (!token) { router.push("/login"); return; }
    setReady(true);
  }, [router]);

  const load = useCallback(async () => {
    try {
      const results = await Promise.all(
        COLUMNS.map((c) => api.get(`/api/v1/pos/orders/?kitchen_status=${c.status}&status=CONFIRMED`))
      );
      const byStatus = {};
      results.forEach((r, i) => { byStatus[COLUMNS[i].status] = Array.isArray(r) ? r : r.results || []; });
      setOrders(byStatus);
    } catch (err) {
      // silent: KDS keeps last known board rather than showing an error screen
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!ready) return;
    load();
    timerRef.current = setInterval(load, POLL_MS);
    return () => clearInterval(timerRef.current);
  }, [ready, load]);

  const advance = async (orderId, next) => {
    setBusyId(orderId);
    try {
      await api.post(`/api/v1/pos/orders/${orderId}/kitchen-status/`, { kitchen_status: next });
      load();
    } finally {
      setBusyId(null);
    }
  };

  const logout = () => { localStorage.clear(); router.push("/login"); };

  if (!ready) return null;

  return (
    <div className="min-h-screen bg-black text-white p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <ChefHat className="w-7 h-7 text-[#ED6C00]" />
          <h1 className="text-2xl font-bold">Kitchen Display</h1>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={load} className="p-2 rounded-lg hover:bg-white/10">
            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={logout} className="p-2 rounded-lg hover:bg-white/10">
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {COLUMNS.map((col) => (
          <div key={col.status}>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: col.color }} />
              <h2 className="font-semibold text-white/80">{col.label}</h2>
              <span className="text-xs text-white/40">({(orders[col.status] || []).length})</span>
            </div>
            <div className="space-y-3">
              {(orders[col.status] || []).length === 0 ? (
                <div className="text-white/30 text-sm py-8 text-center border border-dashed border-white/10 rounded-xl">
                  No orders
                </div>
              ) : (orders[col.status] || []).map((o) => (
                <Ticket
                  key={o.id}
                  order={o}
                  next={col.next}
                  nextLabel={col.nextLabel}
                  color={col.color}
                  onAdvance={advance}
                  busy={busyId === o.id}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
      {orders.READY?.length > 0 && (
        <div className="mt-6 text-center text-xs text-white/40 flex items-center justify-center gap-1">
          <CheckCircle2 className="w-3.5 h-3.5" /> Served orders drop off the board automatically
        </div>
      )}
    </div>
  );
}
