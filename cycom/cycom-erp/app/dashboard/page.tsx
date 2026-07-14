'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart2, TrendingUp, Users, DollarSign, Package, 
  ShoppingCart, RefreshCw, ArrowUpRight, CheckCircle2 
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

const GRAPH_DATA = [
  { month: 'Jan', revenue: 1900000, cost: 1600000 },
  { month: 'Feb', revenue: 2100000, cost: 1750000 },
  { month: 'Mar', revenue: 2000000, cost: 1700000 },
  { month: 'Apr', revenue: 2300000, cost: 1850000 },
  { month: 'May', revenue: 2400000, cost: 1900000 },
  { month: 'Jun', revenue: 2480000, cost: 1950000 },
];

const ALERTS = [
  { source: 'Inventory', type: 'Discrepancy', desc: '5 units shortfall olive oil premium Zarqa', urgency: 'High' },
  { source: 'Sales Pricing', type: 'Margin Override', desc: 'SO-1091 discount requested 18% (limit 10%)', urgency: 'High' },
  { source: 'Biometrics', type: 'Device Offline', desc: 'Zarqa Retail Shop Gate device offline', urgency: 'Medium' },
  { source: 'HR Expiry', type: 'Passport Expiry', desc: 'Passport of Khaled Jaber expiring in 5 days', urgency: 'Medium' },
];

export default function CommandCenter() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Global Command Center</h1>
          <p className="page-subtitle">Real-time enterprise metrics, sales margins, and operational alerts across all Cycom domains.</p>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <RefreshCw className="w-4 h-4 text-cyan-400" /> Refresh telemetry
        </button>
      </div>

      {/* Main Revenue Chart */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Revenue & Operation Costs</h2>
            <p className="text-2xl font-black text-white mt-1">JOD 2.48M <span className="text-xs text-emerald-400 font-semibold">+8.3% this month</span></p>
          </div>
          <span className="badge badge-cyan font-mono text-[10px]">Real-time analytics</span>
        </div>
        <div className="h-[280px] w-full text-slate-300 text-xs">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={GRAPH_DATA}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00F0FF" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#00F0FF" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#E67E22" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#E67E22" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="month" stroke="#475569" />
              <YAxis stroke="#475569" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.07)' }}
                labelStyle={{ color: '#94A3B8' }}
              />
              <Area type="monotone" dataKey="revenue" stroke="#00F0FF" fillOpacity={1} fill="url(#colorRevenue)" strokeWidth={2} />
              <Area type="monotone" dataKey="cost" stroke="#E67E22" fillOpacity={1} fill="url(#colorCost)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 columns - Live alerts */}
        <div className="glass-card p-6 lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">System Telemetry Alerts</h2>
            <span className="text-xs text-slate-500 font-mono">4 unresolved events</span>
          </div>

          <div className="space-y-3">
            {ALERTS.map((alert, index) => (
              <div key={index} className="flex justify-between items-start p-4 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="badge badge-purple">{alert.source}</span>
                    <span className="text-xs text-slate-300 font-bold">{alert.type}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{alert.desc}</p>
                </div>
                <span className={`badge ${alert.urgency === 'High' ? 'badge-red' : 'badge-yellow'}`}>
                  {alert.urgency}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Right column - Quick operational status */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">Modules Pulse</h3>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-white/5">
              <span className="text-slate-400 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
                HR & Employees
              </span>
              <span className="text-white font-mono font-bold">342 active</span>
            </div>
            <div className="flex justify-between items-center pb-2 border-b border-white/5">
              <span className="text-slate-400 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
                POS Cash registers
              </span>
              <span className="text-white font-mono font-bold">7 open</span>
            </div>
            <div className="flex justify-between items-center pb-2 border-b border-white/5">
              <span className="text-slate-400 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
                Warehouse Locks
              </span>
              <span className="text-[#10B981] font-mono font-bold">Guards healthy</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
                Biometric ZK devices
              </span>
              <span className="text-white font-mono font-bold">18 online</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
