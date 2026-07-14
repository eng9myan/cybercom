'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Users, Building2, Award, FileText, Shield, AlertTriangle,
  Clock, ArrowUpRight, TrendingUp, ShieldCheck, UserCheck, FileWarning
} from 'lucide-react';

/* ─── Quick‐link cards that route into sub‐pages ─── */
const QUICK_LINKS = [
  {
    title: 'Employee Directory',
    desc: 'Search, view, and manage complete employee profiles, portal setup, bank details, and spouse records.',
    href: '/hr/employees',
    icon: Users,
    accent: '#A855F7',
    bg: 'from-purple-500/8 to-purple-500/3',
    border: 'border-purple-500/15',
    metric: '342',
    metricLabel: 'Active Employees',
  },
  {
    title: 'Department Hierarchy',
    desc: 'Organizational tree with dynamic child headcount rollup across Executive, Logistics, and Retail branches.',
    href: '/hr/departments',
    icon: Building2,
    accent: '#00F0FF',
    bg: 'from-cyan-500/8 to-cyan-500/3',
    border: 'border-cyan-500/15',
    metric: '12',
    metricLabel: 'Departments',
  },
  {
    title: 'Health Insurance',
    desc: 'Manage group health insurance schemes, coverage tiers (VIP, A, B, C), providers, and monthly deductions.',
    href: '/hr/insurance',
    icon: Award,
    accent: '#E67E22',
    bg: 'from-orange-500/8 to-orange-500/3',
    border: 'border-orange-500/15',
    metric: '3 Tiers',
    metricLabel: 'Active Plans',
  },
  {
    title: 'Document Expiry',
    desc: 'Monitor passports, residency permits, work permits, and driving licenses with proactive deadline alerts.',
    href: '/hr/documents',
    icon: FileText,
    accent: '#F59E0B',
    bg: 'from-amber-500/8 to-amber-500/3',
    border: 'border-amber-500/15',
    metric: '1',
    metricLabel: 'Critical Alerts',
  },
  {
    title: 'Employee Requests',
    desc: 'Review, approve, or reject leave requests, salary certificates, insurance upgrades, and fallback rules.',
    href: '/hr/requests',
    icon: Shield,
    accent: '#EC4899',
    bg: 'from-pink-500/8 to-pink-500/3',
    border: 'border-pink-500/15',
    metric: '2',
    metricLabel: 'Pending Review',
  },
];

/* ─── Recent activity feed (mock) ─── */
const RECENT_ACTIVITY = [
  { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10', text: 'Rami Khasawneh — Written Warning issued for safety violation.', time: '2 hours ago' },
  { icon: Shield, color: 'text-pink-400', bg: 'bg-pink-500/10', text: 'Ahmad Masri — Annual Leave request submitted (8 days, Jun 15–22).', time: '3 hours ago' },
  { icon: FileWarning, color: 'text-amber-400', bg: 'bg-amber-500/10', text: 'Khaled Jaber — Passport expires in 5 days. Critical alert triggered.', time: '5 hours ago' },
  { icon: UserCheck, color: 'text-emerald-400', bg: 'bg-emerald-500/10', text: 'Sara Haddad — Salary certificate request approved and sent to portal.', time: '6 hours ago' },
  { icon: Award, color: 'text-orange-400', bg: 'bg-orange-500/10', text: 'Rami Khasawneh — Spouse insurance upgrade to Grade A approved by GM.', time: '1 day ago' },
  { icon: TrendingUp, color: 'text-cyan-400', bg: 'bg-cyan-500/10', text: 'Noor Al-Fayegh — Career promotion to Senior Warehouse Coordinator.', time: '2 days ago' },
];

export default function HRDashboard() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">HR & People Command</h1>
          <p className="page-subtitle">Cycom human capital overview — employee records, departments, insurance, and administrative requests.</p>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Headcount</span>
            <p className="text-2xl font-black text-white">342</p>
          </div>
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400">
            <Users className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Warnings</span>
            <p className="text-2xl font-black text-[#EF4444]">3</p>
          </div>
          <div className="p-3 rounded-xl bg-red-500/10 text-red-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Expiring Documents</span>
            <p className="text-2xl font-black text-[#F59E0B]">3</p>
          </div>
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400">
            <FileWarning className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Biometric Devices</span>
            <p className="text-2xl font-black text-[#10B981]">18 Online</p>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Quick Links Grid + Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left 2 Columns — Module Quick Links */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">HR Modules</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {QUICK_LINKS.map((card, i) => {
              const Icon = card.icon;
              return (
                <motion.div
                  key={card.href}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                >
                  <Link
                    href={card.href}
                    className={`glass-card p-5 block group hover:shadow-lg transition-all duration-300 bg-gradient-to-br ${card.bg} ${card.border}`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="p-2.5 rounded-xl" style={{ background: `${card.accent}15` }}>
                        <Icon className="w-5 h-5" style={{ color: card.accent }} />
                      </div>
                      <div className="flex items-center gap-1 text-slate-500 group-hover:text-white transition-colors">
                        <ArrowUpRight className="w-4 h-4" />
                      </div>
                    </div>
                    <h3 className="text-sm font-bold text-white mb-1 group-hover:text-[#E67E22] transition-colors">{card.title}</h3>
                    <p className="text-[11px] text-slate-400 leading-relaxed mb-4">{card.desc}</p>
                    <div className="flex items-center justify-between pt-3 border-t border-white/5">
                      <span className="text-lg font-black text-white">{card.metric}</span>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">{card.metricLabel}</span>
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Right Column — Recent Activity */}
        <div className="space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Recent Activity</h2>
          <div className="glass-card p-5 space-y-1">
            {RECENT_ACTIVITY.map((item, i) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: 8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.15 + i * 0.05 }}
                  className="flex items-start gap-3 p-3 rounded-xl hover:bg-white/3 transition-colors"
                >
                  <div className={`p-2 rounded-lg ${item.bg} flex-shrink-0 mt-0.5`}>
                    <Icon className={`w-3.5 h-3.5 ${item.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-300 leading-relaxed">{item.text}</p>
                    <span className="text-[10px] text-slate-500 mt-1 block">{item.time}</span>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Org Quick Stats */}
          <div className="glass-card p-5 border-cyan-500/10 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">Organization Snapshot</h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center pb-2.5 border-b border-white/5">
                <span className="text-slate-400">Departments</span>
                <span className="text-white font-bold">12</span>
              </div>
              <div className="flex justify-between items-center pb-2.5 border-b border-white/5">
                <span className="text-slate-400">Insurance Enrollees</span>
                <span className="text-white font-bold">342 / 342</span>
              </div>
              <div className="flex justify-between items-center pb-2.5 border-b border-white/5">
                <span className="text-slate-400">Portal Access Active</span>
                <span className="text-white font-bold">289 users</span>
              </div>
              <div className="flex justify-between items-center pb-2.5 border-b border-white/5">
                <span className="text-slate-400">Pending Leave Requests</span>
                <span className="text-[#F59E0B] font-bold">2 awaiting</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Retail Distribution</span>
                <span className="text-white font-bold">58.2%</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
