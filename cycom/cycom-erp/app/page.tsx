'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  Users, DollarSign, Clock, ShoppingCart, Package,
  BarChart2, FileText, Shield, Settings, TrendingUp,
  MessageSquare, BookOpen, Layers, UserCheck, HelpCircle,
  FolderOpen, ShieldAlert, CreditCard, Mail,
  Wrench, Car, Briefcase, FileSignature, CalendarOff, Award, PenTool,
  Sparkles
} from 'lucide-react';

// Cycom modules launcher
const CYCOM_MODULES = [
  { id: 'setup', label: 'Setup', href: '/setup', icon: Sparkles, color: 'from-fuchsia-500 to-purple-600', group: 'Administration' },
  { id: 'discuss', label: 'Discuss', href: '/discuss', icon: MessageSquare, color: 'from-purple-500 to-indigo-500', group: 'Communication' },
  { id: 'sign', label: 'eSign', href: '/sign', icon: PenTool, color: 'from-rose-500 to-pink-500', group: 'Communication' },
  { id: 'sales', label: 'Sales', href: '/sales', icon: TrendingUp, color: 'from-blue-500 to-cyan-500', group: 'Sales' },
  { id: 'pos', label: 'Point of Sale', href: '/pos', icon: ShoppingCart, color: 'from-orange-500 to-red-500', group: 'Sales' },
  { id: 'accounting', label: 'Accounting', href: '/accounting', icon: FileText, color: 'from-teal-500 to-emerald-500', group: 'Finance' },
  { id: 'inventory', label: 'Inventory', href: '/inventory', icon: Package, color: 'from-amber-500 to-orange-500', group: 'Operations' },
  { id: 'hr', label: 'Employees', href: '/hr', icon: Users, color: 'from-indigo-500 to-blue-500', group: 'Human Resources' },
  { id: 'payroll', label: 'Payroll', href: '/payroll', icon: DollarSign, color: 'from-emerald-500 to-green-500', group: 'Human Resources' },
  { id: 'attendance', label: 'Attendance', href: '/attendance', icon: Clock, color: 'from-yellow-500 to-amber-500', group: 'Human Resources' },
  { id: 'recruitment', label: 'Recruitment', href: '/recruitment', icon: UserCheck, color: 'from-blue-400 to-indigo-500', group: 'Human Resources' },
  { id: 'project', label: 'Project', href: '/project', icon: Layers, color: 'from-cyan-500 to-blue-500', group: 'Services' },
  { id: 'helpdesk', label: 'Helpdesk', href: '/helpdesk', icon: HelpCircle, color: 'from-purple-400 to-purple-600', group: 'Services' },
  { id: 'marketing', label: 'Marketing', href: '/marketing', icon: Mail, color: 'from-pink-500 to-rose-500', group: 'Marketing' },
  { id: 'plm', label: 'Manufacturing', href: '/plm', icon: Wrench, color: 'from-slate-500 to-slate-700', group: 'Operations' },
  { id: 'fleet', label: 'Fleet', href: '/fleet', icon: Car, color: 'from-sky-500 to-blue-600', group: 'Operations' },
  { id: 'documents', label: 'Documents', href: '/documents', icon: FolderOpen, color: 'from-indigo-400 to-purple-500', group: 'Productivity' },
  { id: 'settings', label: 'Settings', href: '/settings', icon: Settings, color: 'from-gray-600 to-gray-800', group: 'Administration' }
];

export default function AppLauncher() {
  const [searchTerm, setSearchTerm] = useState('');

  // In the future, this will filter based on the logged-in user's permissions array
  const filteredModules = CYCOM_MODULES.filter(m => 
    m.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#0a0f1e] text-white p-8 font-sans relative overflow-hidden">
      {/* Background Orbs for glassmorphic effect */}
      <div className="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[40%] h-[40%] bg-purple-500/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
        <header className="flex items-center justify-between mb-12">
          <div>
            <h1 className="text-3xl font-black bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
              Welcome to Cycom
            </h1>
            <p className="text-slate-400 mt-1">Select an app to get started.</p>
          </div>

          <div className="relative w-64">
            <input 
              type="text" 
              placeholder="Search apps..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
            />
          </div>
        </header>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
          {filteredModules.map((mod) => {
            const Icon = mod.icon;
            return (
              <Link 
                href={mod.href} 
                key={mod.id}
                className="group flex flex-col items-center gap-3 transition-transform hover:-translate-y-1"
              >
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
            No applications found matching "{searchTerm}"
          </div>
        )}
      </div>
    </div>
  );
}
