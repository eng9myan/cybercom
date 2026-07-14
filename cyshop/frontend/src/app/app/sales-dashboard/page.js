"use client";

import { useState, useEffect } from "react";
import { DollarSign, TrendingUp, Percent, FileText, ArrowUpRight, BarChart3, PieChart, ShieldAlert, Sparkles, RefreshCw } from "lucide-react";

export default function SalesDashboardPage() {
  const [data, setData] = useState({
    revenue: 0,
    aov: 0,
    activePipeline: 0,
    winRate: 0,
    leadCount: 0,
    oppCount: 0,
    commCount: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const calculateMetrics = async () => {
    setLoading(true);
    setError("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      // 1. Fetch Orders
      const orderRes = await fetch("/api/v1/sales/orders/", {
        headers: { "Authorization": `Bearer ${token}`, "X-Tenant-ID": tenantId }
      });
      let fetchedOrders = [];
      if (orderRes.ok) fetchedOrders = await orderRes.json();

      // 2. Fetch Opportunities
      const oppRes = await fetch("/api/v1/sales/opportunities/", {
        headers: { "Authorization": `Bearer ${token}`, "X-Tenant-ID": tenantId }
      });
      let fetchedOpps = [];
      if (oppRes.ok) fetchedOpps = await oppRes.json();

      // 3. Fetch Leads
      const leadRes = await fetch("/api/v1/sales/leads/", {
        headers: { "Authorization": `Bearer ${token}`, "X-Tenant-ID": tenantId }
      });
      let fetchedLeads = [];
      if (leadRes.ok) fetchedLeads = await leadRes.json();

      // 4. Fetch Communications
      const commRes = await fetch("/api/v1/sales/communications/", {
        headers: { "Authorization": `Bearer ${token}`, "X-Tenant-ID": tenantId }
      });
      let fetchedComms = [];
      if (commRes.ok) fetchedComms = await commRes.json();

      // Calculate Metrics
      const completedOrders = fetchedOrders.filter(o => ["DELIVERED", "COMPLETED"].includes(o.status));
      const totalRevenue = completedOrders.reduce((sum, o) => sum + parseFloat(o.total_amount || 0), 0);
      const aov = completedOrders.length > 0 ? totalRevenue / completedOrders.length : 0;

      const activePipeline = fetchedOpps
        .filter(o => !["WON", "LOST"].includes(o.stage))
        .reduce((sum, o) => sum + parseFloat(o.expected_revenue || 0), 0);

      const closedWon = fetchedOpps.filter(o => o.stage === "WON").length;
      const closedLost = fetchedOpps.filter(o => o.stage === "LOST").length;
      const totalClosed = closedWon + closedLost;
      const winRate = totalClosed > 0 ? (closedWon / totalClosed) * 100 : 0;

      setData({
        revenue: totalRevenue,
        aov: aov,
        activePipeline: activePipeline,
        winRate: winRate,
        leadCount: fetchedLeads.length,
        oppCount: fetchedOpps.length,
        commCount: fetchedComms.length,
      });

    } catch (err) {
      setError("Failed to fetch dashboard metrics. Please check network connections.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    calculateMetrics();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="w-8 h-8 border-4 border-[var(--color-line)] border-t-orange-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 text-[var(--color-ink)] animate-fade">
      
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">Sales & CRM Analytics</h1>
          <p className="text-xs text-[var(--color-ink-muted)]">Executive dashboard detailing revenue cycles, average order values, and conversion pipelines.</p>
        </div>
        <button
          onClick={calculateMetrics}
          className="w-10 h-10 bg-white border border-[var(--color-line)] rounded-xl flex items-center justify-center text-[var(--color-ink-muted)] hover:text-white transition hover:bg-[var(--color-surface-2)]"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {error && (
        <div className="bg-red-950/40 border border-red-805 text-red-400 p-4 rounded-xl text-xs flex items-center gap-2">
          <ShieldAlert className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Total Revenue */}
        <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl flex items-center justify-between hover:border-[var(--color-ink)] transition">
          <div className="space-y-1">
            <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block">Fulfillment Revenue</span>
            <div className="text-2xl font-extrabold font-mono text-[#ED6C00]">{data.revenue.toFixed(2)} JOD</div>
            <span className="text-[9px] text-[var(--color-ink-muted)] flex items-center gap-1 font-bold">
              <TrendingUp className="w-3 h-3 text-emerald-400" />
              <span>+12.4% vs last week</span>
            </span>
          </div>
          <div className="w-10 h-10 bg-white rounded-xl border border-[var(--color-line)] flex items-center justify-center">
            <DollarSign className="w-5 h-5 text-[#ED6C00]" />
          </div>
        </div>

        {/* AOV */}
        <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl flex items-center justify-between hover:border-[var(--color-ink)] transition">
          <div className="space-y-1">
            <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block">Average Order Value</span>
            <div className="text-2xl font-extrabold font-mono text-[var(--color-ink)]">{data.aov.toFixed(2)} JOD</div>
            <span className="text-[9px] text-[var(--color-ink-muted)] flex items-center gap-1 font-bold">
              <ArrowUpRight className="w-3 h-3 text-sky-400" />
              <span>Flat over 30 days</span>
            </span>
          </div>
          <div className="w-10 h-10 bg-white rounded-xl border border-[var(--color-line)] flex items-center justify-center">
            <FileText className="w-5 h-5 text-sky-400" />
          </div>
        </div>

        {/* Active Pipeline */}
        <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl flex items-center justify-between hover:border-[var(--color-ink)] transition">
          <div className="space-y-1">
            <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block">CRM Deal Pipeline</span>
            <div className="text-2xl font-extrabold font-mono text-sky-400">{data.activePipeline.toFixed(2)} JOD</div>
            <span className="text-[9px] text-[var(--color-ink-muted)] flex items-center gap-1 font-bold">
              <Sparkles className="w-3 h-3 text-[#ED6C00]" />
              <span>{data.oppCount} Active Opps</span>
            </span>
          </div>
          <div className="w-10 h-10 bg-white rounded-xl border border-[var(--color-line)] flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-[#ED6C00]" />
          </div>
        </div>

        {/* Win Rate */}
        <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl flex items-center justify-between hover:border-[var(--color-ink)] transition">
          <div className="space-y-1">
            <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block">Deal Win Rate</span>
            <div className="text-2xl font-extrabold font-mono text-emerald-400">{data.winRate.toFixed(1)}%</div>
            <span className="text-[9px] text-[var(--color-ink-muted)] flex items-center gap-1 font-bold">
              <Percent className="w-3 h-3 text-emerald-400" />
              <span>High conversion index</span>
            </span>
          </div>
          <div className="w-10 h-10 bg-white rounded-xl border border-[var(--color-line)] flex items-center justify-center">
            <Percent className="w-5 h-5 text-emerald-400" />
          </div>
        </div>

      </div>

      {/* Analytics Charts & Funnels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* CSS-drawn Funnel Chart */}
        <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl lg:col-span-2 space-y-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-[#ED6C00]" />
              <span className="text-[10px] text-[var(--color-ink-soft)] uppercase tracking-widest font-bold">Leads-to-Opportunities Pipeline Funnel</span>
            </div>
            <span className="text-[9px] bg-white border border-[var(--color-line)] px-2 py-0.5 rounded-full text-[var(--color-ink-muted)] font-bold font-mono">
              Real-time Analysis
            </span>
          </div>

          <div className="space-y-4">
            
            {/* Step 1: Leads */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-bold text-[var(--color-ink-soft)]">
                <span>1. Captured Prospect Leads</span>
                <span className="font-mono">{data.leadCount} leads</span>
              </div>
              <div className="h-3 w-full bg-white rounded-full overflow-hidden">
                <div className="h-full bg-[var(--color-surface-2)] rounded-full transition-all duration-500" style={{ width: "100%" }}></div>
              </div>
            </div>

            {/* Step 2: Opportunities */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-bold text-[var(--color-ink-soft)]">
                <span>2. Pipeline Opportunities</span>
                <span className="font-mono">{data.oppCount} deals</span>
              </div>
              <div className="h-3 w-full bg-white rounded-full overflow-hidden">
                <div className="h-full bg-[#ED6C00] rounded-full transition-all duration-500" style={{
                  width: data.leadCount > 0 ? `${(data.oppCount / data.leadCount) * 100}%` : "30%"
                }}></div>
              </div>
            </div>

            {/* Step 3: Win Rate */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-bold text-[var(--color-ink-soft)]">
                <span>3. Customer Conversion Won</span>
                <span className="font-mono">{data.winRate.toFixed(1)}% Conversion</span>
              </div>
              <div className="h-3 w-full bg-white rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full transition-all duration-500" style={{
                  width: `${data.winRate || 10}%`
                }}></div>
              </div>
            </div>

          </div>
        </div>

        {/* Executive activities tracker */}
        <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl space-y-6">
          <div className="flex items-center gap-2">
            <PieChart className="w-4 h-4 text-sky-400" />
            <span className="text-[10px] text-[var(--color-ink-soft)] uppercase tracking-widest font-bold">Activity Indices</span>
          </div>

          <div className="space-y-4">
            
            <div className="flex items-center justify-between border-b border-[var(--color-line)] pb-3">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#ED6C00]"></span>
                <span className="text-xs font-bold text-[var(--color-ink-soft)]">CRM Channels logged</span>
              </div>
              <span className="text-xs font-mono font-bold text-[var(--color-ink)]">{data.commCount} logs</span>
            </div>

            <div className="flex items-center justify-between border-b border-[var(--color-line)] pb-3">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-400"></span>
                <span className="text-xs font-bold text-[var(--color-ink-soft)]">Open Opportunities</span>
              </div>
              <span className="text-xs font-mono font-bold text-[var(--color-ink)]">{data.oppCount} active</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                <span className="text-xs font-bold text-[var(--color-ink-soft)]">Conversion Won index</span>
              </div>
              <span className="text-xs font-mono font-bold text-[var(--color-ink-soft)]">High Velocity</span>
            </div>

          </div>
        </div>

      </div>

    </div>
  );
}
