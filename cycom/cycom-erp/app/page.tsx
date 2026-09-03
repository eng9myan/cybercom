'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  Users, DollarSign, Clock, ShoppingCart, Package,
  TrendingUp, MessageSquare, Layers, UserCheck, HelpCircle,
  FolderOpen, Mail, Wrench, Car, FileSignature, PenTool,
  Sparkles, FileText, Settings, ChevronDown,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

const CYCOM_MODULES = [
  { id: 'setup', label: 'Setup', href: '/setup', icon: Sparkles, color: 'from-fuchsia-500 to-purple-600' },
  { id: 'discuss', label: 'Discuss', href: '/discuss', icon: MessageSquare, color: 'from-purple-500 to-indigo-500' },
  { id: 'sign', label: 'eSign', href: '/sign', icon: PenTool, color: 'from-rose-500 to-pink-500' },
  { id: 'sales', label: 'Sales', href: '/sales', icon: TrendingUp, color: 'from-blue-500 to-cyan-500' },
  { id: 'pos', label: 'Point of Sale', href: '/pos', icon: ShoppingCart, color: 'from-orange-500 to-red-500' },
  { id: 'accounting', label: 'Accounting', href: '/accounting', icon: FileText, color: 'from-teal-500 to-emerald-500' },
  { id: 'purchase', label: 'Purchase', href: '/purchase', icon: Package, color: 'from-amber-500 to-yellow-600' },
  { id: 'inventory', label: 'Inventory', href: '/inventory', icon: Package, color: 'from-amber-500 to-orange-500' },
  { id: 'hr', label: 'Employees', href: '/hr', icon: Users, color: 'from-indigo-500 to-blue-500' },
  { id: 'payroll', label: 'Payroll', href: '/payroll', icon: DollarSign, color: 'from-emerald-500 to-green-500' },
  { id: 'attendance', label: 'Attendance', href: '/attendance', icon: Clock, color: 'from-yellow-500 to-amber-500' },
  { id: 'recruitment', label: 'Recruitment', href: '/recruitment', icon: UserCheck, color: 'from-blue-400 to-indigo-500' },
  { id: 'project', label: 'Project', href: '/project', icon: Layers, color: 'from-cyan-500 to-blue-500' },
  { id: 'helpdesk', label: 'Helpdesk', href: '/helpdesk', icon: HelpCircle, color: 'from-purple-400 to-purple-600' },
  { id: 'marketing', label: 'Marketing', href: '/marketing', icon: Mail, color: 'from-pink-500 to-rose-500' },
  { id: 'plm', label: 'Manufacturing', href: '/plm', icon: Wrench, color: 'from-slate-500 to-slate-700' },
  { id: 'fleet', label: 'Fleet', href: '/fleet', icon: Car, color: 'from-sky-500 to-blue-600' },
  { id: 'documents', label: 'Documents', href: '/documents', icon: FolderOpen, color: 'from-indigo-400 to-purple-500' },
  { id: 'settings', label: 'Settings', href: '/settings', icon: Settings, color: 'from-gray-600 to-gray-800' },
];

// Functional roles → the modules each one works in. 'gm' sees everything.
const ROLE_MODULES: Record<string, string[] | 'all'> = {
  gm: 'all',
  accounting_officer: ['accounting', 'purchase', 'documents', 'sign', 'discuss'],
  hr_officer: ['hr', 'payroll', 'attendance', 'recruitment', 'documents', 'discuss'],
  supply_chain_officer: ['inventory', 'purchase', 'sales', 'documents', 'discuss'],
  ops_manager: ['sales', 'pos', 'project', 'helpdesk', 'plm', 'fleet', 'marketing', 'discuss'],
};

const ROLES = [
  { id: 'gm', label: 'General Manager' },
  { id: 'accounting_officer', label: 'Accounting Officer' },
  { id: 'hr_officer', label: 'HR Officer' },
  { id: 'supply_chain_officer', label: 'Supply Chain Officer' },
  { id: 'ops_manager', label: 'Operations Manager' },
];

export default function AppLauncher() {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [switcherOpen, setSwitcherOpen] = useState(false);

  const role = user?.role || 'gm';
  const allowed = ROLE_MODULES[role] ?? 'all';
  const roleLabel = ROLES.find((r) => r.id === role)?.label || 'General Manager';

  const visibleModules = CYCOM_MODULES.filter(
    (m) => allowed === 'all' || allowed.includes(m.id),
  );
  const filteredModules = visibleModules.filter((m) =>
    m.label.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <div className="min-h-screen bg-[#0a0f1e] text-white p-8 font-sans relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[40%] h-[40%] bg-purple-500/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
        <header className="flex items-center justify-between mb-10 gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-black bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
              Welcome to Cycom
            </h1>
            <p className="text-slate-400 mt-1">
              Signed in as <span className="text-[var(--cy-orange)] font-semibold">{user?.name || roleLabel}</span> · {roleLabel}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Role switcher (dev) — log in as a role to see its scoped apps */}
            <div className="relative">
              <button
                onClick={() => setSwitcherOpen((o) => !o)}
                className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm hover:border-white/20 transition-all"
              >
                <UserCheck className="w-4 h-4 text-[var(--cy-blue)]" />
                {roleLabel}
                <ChevronDown className="w-4 h-4 text-slate-500" />
              </button>
              {switcherOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-[#0c1122] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-20">
                  <div className="px-3 py-2 text-[0.7rem] uppercase font-bold text-slate-500 border-b border-white/5">
                    View as role
                  </div>
                  {ROLES.map((r) => (
                    <a
                      key={r.id}
                      href={`/api/cycom/dev-login?role=${r.id}`}
                      className={`block px-3 py-2.5 text-sm hover:bg-white/5 transition-colors ${
                        r.id === role ? 'text-[var(--cy-orange)] font-semibold' : 'text-slate-300'
                      }`}
                    >
                      {r.label}
                    </a>
                  ))}
                </div>
              )}
            </div>

            <div className="relative w-56">
              <input
                type="text"
                placeholder="Search apps…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                aria-label="Search apps"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500/50 transition-all"
              />
            </div>
          </div>
        </header>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
          {filteredModules.map((mod) => {
            const Icon = mod.icon;
            return (
              <Link href={mod.href} key={`${mod.id}`} className="group flex flex-col items-center gap-3 transition-transform hover:-translate-y-1">
                <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${mod.color} p-0.5 shadow-lg shadow-black/20 group-hover:shadow-xl transition-all`}>
                  <div className="w-full h-full bg-black/20 backdrop-blur-sm rounded-[14px] flex items-center justify-center border border-white/20 group-hover:bg-transparent transition-colors">
                    <Icon className="w-8 h-8 text-white drop-shadow-md" />
                  </div>
                </div>
                <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors text-center">
                  {mod.label}
                </span>
              </Link>
            );
          })}
        </div>

        {filteredModules.length === 0 && (
          <div className="text-center py-20 text-slate-500">
            No apps {searchTerm ? `matching "${searchTerm}"` : `for the ${roleLabel} role`}.
          </div>
        )}
      </div>
    </div>
  );
}
