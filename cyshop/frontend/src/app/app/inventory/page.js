"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Package, Warehouse, RefreshCw, AlertTriangle, TrendingDown,
  ArrowRight, Search, Filter, CheckCircle2,
} from "lucide-react";
import { api } from "@/lib/api";
import Link from "next/link";

function Toast({ msg, ok, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3500); return () => clearTimeout(t); }, [onDone]);
  return (
    <div className={`fixed bottom-6 right-6 z-[200] flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl text-white text-sm font-medium ${ok ? "bg-[#16A34A]" : "bg-[#DC2626]"}`}>
      {ok ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
      {msg}
    </div>
  );
}

export default function InventoryPage() {
  const [levels, setLevels] = useState([]);
  const [summary, setSummary] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [warehouseFilter, setWarehouseFilter] = useState("");
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [lvls, summ, whs] = await Promise.all([
        api.get("/api/v1/inventory/levels/"),
        api.get("/api/v1/inventory/levels/summary/"),
        api.get("/api/v1/inventory/warehouses/"),
      ]);
      setLevels(Array.isArray(lvls) ? lvls : lvls.results || []);
      setSummary(Array.isArray(summ) ? summ : []);
      setWarehouses(Array.isArray(whs) ? whs : whs.results || []);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = levels.filter((l) => {
    const matchSearch = !search || l.product_name?.toLowerCase().includes(search.toLowerCase());
    const matchWh = !warehouseFilter || l.warehouse_name === warehouseFilter;
    return matchSearch && matchWh;
  });

  const lowStock = levels.filter(
    (l) => l.product && parseFloat(l.quantity) < parseFloat(l.product?.min_stock_qty || 0)
  );

  const totalValue = levels.reduce((sum, l) => {
    const cost = parseFloat(l.product?.cost_price || 0);
    return sum + parseFloat(l.quantity) * cost;
  }, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-heading font-bold text-2xl">Inventory</h2>
          <p className="text-sm text-[var(--color-ink-muted)] mt-0.5">
            Live stock levels · {levels.length} location{levels.length !== 1 ? "s" : ""} tracked
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={load} className="cy-btn cy-btn-ghost !py-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <Link href="/app/inventory/movements" className="cy-btn cy-btn-primary">
            Post Movement <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total SKUs", value: summary.length, icon: Package, accent: "orange" },
          { label: "Warehouses", value: warehouses.length, icon: Warehouse, accent: "blue" },
          { label: "Low Stock Alerts", value: lowStock.length, icon: TrendingDown, accent: lowStock.length > 0 ? "red" : "green" },
          {
            label: "Est. Stock Value",
            value: totalValue > 0 ? totalValue.toLocaleString("en", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—",
            icon: Filter,
            accent: "orange",
          },
        ].map(({ label, value, icon: Icon, accent }) => {
          const bg = accent === "blue" ? "rgba(89,195,225,.15)" : accent === "red" ? "rgba(220,38,38,.12)" : accent === "green" ? "rgba(22,163,74,.12)" : "rgba(237,108,0,.10)";
          const fg = accent === "blue" ? "#0E7C9B" : accent === "red" ? "#DC2626" : accent === "green" ? "#16A34A" : "#ED6C00";
          return (
            <div key={label} className="cy-card p-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: bg, color: fg }}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs text-[var(--color-ink-muted)]">{label}</div>
                  <div className="text-xl font-heading font-bold tabular-nums">{value}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Low-stock alert banner */}
      {lowStock.length > 0 && (
        <div className="rounded-xl border border-[rgba(220,38,38,.25)] bg-[rgba(220,38,38,.06)] px-4 py-3 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-[#DC2626] shrink-0" />
          <p className="text-sm font-medium text-[#DC2626]">
            {lowStock.length} product{lowStock.length !== 1 ? "s are" : " is"} below minimum stock threshold.
          </p>
          <Link href="/app/inventory/movements" className="ml-auto text-sm font-semibold text-[#DC2626] hover:underline shrink-0">
            Receive stock →
          </Link>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-ink-muted)]" />
          <input className="cy-input pl-9" placeholder="Search by product name…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <select className="cy-input w-auto" value={warehouseFilter} onChange={(e) => setWarehouseFilter(e.target.value)}>
          <option value="">All Warehouses</option>
          {warehouses.map((w) => <option key={w.id} value={w.name}>{w.name}</option>)}
        </select>
      </div>

      {/* Stock levels table */}
      <div className="cy-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-line)] bg-[var(--color-surface)]">
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Product</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide hidden md:table-cell">Location</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide hidden lg:table-cell">Warehouse</th>
                <th className="text-right px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">On Hand</th>
                <th className="text-right px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide hidden sm:table-cell">Reserved</th>
                <th className="text-right px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Available</th>
                <th className="text-center px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-line)]">
              {loading ? (
                <tr><td colSpan={7} className="text-center py-16 text-[var(--color-ink-muted)]">Loading…</td></tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-16">
                    <Package className="w-10 h-10 mx-auto mb-3 text-[var(--color-ink-muted)] opacity-40" />
                    <p className="text-[var(--color-ink-muted)]">No stock records found.</p>
                    <Link href="/app/inventory/movements" className="mt-3 inline-flex cy-btn cy-btn-primary !py-2 !text-xs">
                      Post first stock receipt →
                    </Link>
                  </td>
                </tr>
              ) : filtered.map((l) => {
                const onHand = parseFloat(l.quantity);
                const reserved = parseFloat(l.reserved_quantity);
                const available = parseFloat(l.available_quantity ?? (onHand - reserved));
                const minQty = parseFloat(l.product?.min_stock_qty || 0);
                const isLow = onHand < minQty && minQty > 0;

                return (
                  <tr key={l.id} className={`hover:bg-[var(--color-surface)] transition-colors ${isLow ? "bg-[rgba(220,38,38,.03)]" : ""}`}>
                    <td className="px-4 py-3">
                      <div className="font-semibold">{l.product_name}</div>
                      {l.product_sku && <div className="text-xs text-[var(--color-ink-muted)] font-mono">{l.product_sku}</div>}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-[var(--color-ink-muted)] hidden md:table-cell">{l.location_code}</td>
                    <td className="px-4 py-3 text-[var(--color-ink-muted)] hidden lg:table-cell">{l.warehouse_name}</td>
                    <td className="px-4 py-3 text-right font-semibold tabular-nums">{onHand.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-[var(--color-ink-muted)] tabular-nums hidden sm:table-cell">{reserved.toFixed(2)}</td>
                    <td className={`px-4 py-3 text-right font-bold tabular-nums ${isLow ? "text-[#DC2626]" : "text-[#16A34A]"}`}>
                      {available.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {isLow ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#DC2626] bg-[rgba(220,38,38,.10)] px-2 py-0.5 rounded-full">
                          <AlertTriangle className="w-3 h-3" /> Low
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#16A34A] bg-[rgba(22,163,74,.10)] px-2 py-0.5 rounded-full">
                          <CheckCircle2 className="w-3 h-3" /> OK
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {toast && <Toast msg={toast.msg} ok={toast.ok} onDone={() => setToast(null)} />}
    </div>
  );
}
