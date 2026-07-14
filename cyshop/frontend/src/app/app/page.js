"use client";

import { useState, useEffect } from "react";
import {
  Users, Building, MapPin, ClipboardList, RefreshCw, ArrowUpRight, ArrowDownRight,
  TrendingUp, Sparkles, ShoppingBag, AlertTriangle, CheckCircle2, ChevronRight, Brain
} from "lucide-react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar } from "recharts";

const REVENUE = [
  { d: "Mon", v: 12400 }, { d: "Tue", v: 14800 }, { d: "Wed", v: 13900 },
  { d: "Thu", v: 17200 }, { d: "Fri", v: 21500 }, { d: "Sat", v: 19800 }, { d: "Sun", v: 23100 },
];

const CHANNELS = [
  { c: "Direct", v: 42 }, { c: "Marketplace", v: 28 }, { c: "Partners", v: 18 }, { c: "Wholesale", v: 12 },
];

const fmt = (n) => new Intl.NumberFormat("en-US").format(n);
const usd = (n) => "$" + new Intl.NumberFormat("en-US").format(n);

function KpiCard({ label, value, delta, icon: Icon, accent = "orange" }) {
  const up = delta >= 0;
  const accentBg = accent === "blue" ? "rgba(89,195,225,.15)" : accent === "ink" ? "rgba(17,17,17,.06)" : "rgba(237,108,0,.10)";
  const accentFg = accent === "blue" ? "#0E7C9B" : accent === "ink" ? "#1A1A1A" : "#ED6C00";
  return (
    <div className="cy-card p-5">
      <div className="flex items-start justify-between">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: accentBg, color: accentFg }}>
          <Icon className="w-[18px] h-[18px]" />
        </div>
        <span
          className={`inline-flex items-center gap-0.5 text-xs font-semibold px-2 py-0.5 rounded-full ${
            up ? "text-[#16A34A] bg-[rgba(22,163,74,.10)]" : "text-[#DC2626] bg-[rgba(220,38,38,.10)]"
          }`}
        >
          {up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
          {Math.abs(delta)}%
        </span>
      </div>
      <div className="mt-4 text-xs uppercase tracking-[0.18em] text-[var(--color-ink-muted)]">{label}</div>
      <div className="mt-1 text-3xl font-heading font-black tracking-tight tabular-nums">{value}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState({ users: 248, companies: 14, branches: 36, logs: 1284 });
  const [loading, setLoading] = useState(false);
  const [recent, setRecent] = useState([
    { id: 1, type: "order", title: "SO-2419 closed · $4,820", who: "Sara K.", ts: "2m ago", ok: true },
    { id: 2, type: "lead", title: "New enterprise lead — Initech", who: "AI Copilot", ts: "11m ago", ok: true },
    { id: 3, type: "alert", title: "Inventory low: SKU-A19", who: "System", ts: "32m ago", ok: false },
    { id: 4, type: "quote", title: "Quote QT-1083 sent · $12,400", who: "John M.", ts: "1h ago", ok: true },
  ]);

  const refresh = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 500);
  };

  return (
    <div className="space-y-6">
      {/* AI insight strip */}
      <div className="relative rounded-2xl overflow-hidden p-5 md:p-6 text-white bg-[var(--color-brand-ink)]">
        <div
          className="absolute inset-0 opacity-70 pointer-events-none"
          style={{
            background:
              "radial-gradient(30rem 20rem at 90% 0%, rgba(237,108,0,.45), transparent 60%), radial-gradient(30rem 20rem at 0% 100%, rgba(89,195,225,.4), transparent 60%)",
          }}
        />
        <div className="relative flex flex-col md:flex-row md:items-center gap-4">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#ED6C00] to-[#FF8A2A] flex items-center justify-center shrink-0">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[11px] font-bold uppercase tracking-[0.18em] text-white/60">AI Insight · just now</div>
            <p className="mt-1 text-sm md:text-base text-white leading-snug">
              Revenue is pacing <span className="font-bold text-[#59C3E1]">+18.4%</span> vs last week, driven by Marketplace.
              Two enterprise quotes are likely to slip — recommend follow-ups for{" "}
              <span className="font-bold">Acme</span> and <span className="font-bold">Initech</span> within 24h.
            </p>
          </div>
          <button className="cy-btn cy-btn-primary !py-2 text-sm shrink-0">
            Open Copilot <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Revenue (7d)" value={usd(122740)} delta={18.4} icon={TrendingUp} accent="orange" />
        <KpiCard label="Active Users" value={fmt(stats.users)} delta={4.2} icon={Users} accent="blue" />
        <KpiCard label="Open Orders" value={fmt(312)} delta={-2.1} icon={ShoppingBag} accent="ink" />
        <KpiCard label="Pipeline Value" value={usd(847000)} delta={9.8} icon={Sparkles} accent="orange" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="cy-card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-1">
            <div>
              <h3 className="font-heading font-bold text-lg">Revenue trend</h3>
              <p className="text-xs text-[var(--color-ink-muted)]">Last 7 days · USD</p>
            </div>
            <button
              onClick={refresh}
              className="cy-btn cy-btn-ghost !py-1.5 !px-3 text-xs"
              aria-label="Refresh chart"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
          <div className="h-72 mt-3">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={REVENUE} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ED6C00" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#ED6C00" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#ECECEC" vertical={false} />
                <XAxis dataKey="d" tickLine={false} axisLine={false} tick={{ fill: "#8A8A8A", fontSize: 12 }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fill: "#8A8A8A", fontSize: 12 }} tickFormatter={(v) => `$${v / 1000}k`} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: "1px solid #ECECEC", fontSize: 12 }}
                  formatter={(v) => [usd(v), "Revenue"]}
                />
                <Area type="monotone" dataKey="v" stroke="#ED6C00" strokeWidth={2.5} fill="url(#rev)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="cy-card p-5">
          <h3 className="font-heading font-bold text-lg">Channels</h3>
          <p className="text-xs text-[var(--color-ink-muted)]">Share of revenue</p>
          <div className="h-72 mt-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={CHANNELS} layout="vertical" margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#ECECEC" horizontal={false} />
                <XAxis type="number" tickLine={false} axisLine={false} tick={{ fill: "#8A8A8A", fontSize: 12 }} tickFormatter={(v) => `${v}%`} />
                <YAxis type="category" dataKey="c" tickLine={false} axisLine={false} tick={{ fill: "#1A1A1A", fontSize: 12 }} width={90} />
                <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #ECECEC", fontSize: 12 }} formatter={(v) => [`${v}%`, "Share"]} />
                <Bar dataKey="v" radius={[0, 8, 8, 0]} fill="#59C3E1" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="cy-card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-heading font-bold text-lg">Recent activity</h3>
            <button className="text-sm font-semibold text-[#ED6C00] hover:underline">View all</button>
          </div>
          <ul className="divide-y divide-[var(--color-line)]">
            {recent.map((r) => {
              const Icon = r.type === "alert" ? AlertTriangle : r.type === "order" ? ShoppingBag : r.type === "lead" ? Sparkles : ClipboardList;
              const tone = r.type === "alert" ? "#DC2626" : r.type === "order" ? "#16A34A" : "#ED6C00";
              return (
                <li key={r.id} className="py-3 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: `${tone}1A`, color: tone }}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-semibold truncate">{r.title}</div>
                    <div className="text-xs text-[var(--color-ink-muted)]">{r.who} · {r.ts}</div>
                  </div>
                  {r.ok ? (
                    <CheckCircle2 className="w-4 h-4 text-[#16A34A]" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-[#DC2626]" />
                  )}
                </li>
              );
            })}
          </ul>
        </div>

        <div className="cy-card p-5">
          <h3 className="font-heading font-bold text-lg">Tenant footprint</h3>
          <p className="text-xs text-[var(--color-ink-muted)]">Workspace at a glance</p>
          <ul className="mt-4 space-y-3 text-sm">
            <li className="flex items-center justify-between">
              <span className="inline-flex items-center gap-2 text-[var(--color-ink-soft)]"><Building className="w-4 h-4" /> Companies</span>
              <span className="font-bold tabular-nums">{fmt(stats.companies)}</span>
            </li>
            <li className="flex items-center justify-between">
              <span className="inline-flex items-center gap-2 text-[var(--color-ink-soft)]"><MapPin className="w-4 h-4" /> Branches</span>
              <span className="font-bold tabular-nums">{fmt(stats.branches)}</span>
            </li>
            <li className="flex items-center justify-between">
              <span className="inline-flex items-center gap-2 text-[var(--color-ink-soft)]"><Users className="w-4 h-4" /> Users</span>
              <span className="font-bold tabular-nums">{fmt(stats.users)}</span>
            </li>
            <li className="flex items-center justify-between">
              <span className="inline-flex items-center gap-2 text-[var(--color-ink-soft)]"><ClipboardList className="w-4 h-4" /> Audit logs</span>
              <span className="font-bold tabular-nums">{fmt(stats.logs)}</span>
            </li>
          </ul>
          <div className="mt-5 pt-5 border-t border-[var(--color-line)]">
            <div className="text-xs uppercase tracking-[0.18em] text-[var(--color-ink-muted)]">Storage used</div>
            <div className="mt-2 flex items-center justify-between text-sm">
              <span className="font-bold tabular-nums">38.4 GB</span>
              <span className="text-[var(--color-ink-muted)]">of 100 GB</span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-[var(--color-line)] overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-[#ED6C00] to-[#59C3E1]" style={{ width: "38%" }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
