'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import {
  Users, DollarSign, Clock, ShoppingCart, Package, 
  BarChart2, FileText, Shield, Settings, TrendingUp, 
  MessageSquare, BookOpen, Layers, UserCheck, HelpCircle, 
  FolderOpen, ShieldAlert, CreditCard, Mail, 
  Wrench, Car, Briefcase, FileSignature, Building2, 
  ChevronDown, Star, CalendarOff, Award, PenTool,
  Send, LayoutGrid, ArrowLeft, MapPin, Server, Plus, Clipboard, Activity, Calculator, CheckCircle, Laptop, Edit3,
  Sparkles
} from 'lucide-react';
import { useCompany } from '@/context/CompanyContext';

interface SidebarItem {
  label: string;
  href: string;
  icon: React.ComponentType<any>;
  dot: string;
}

interface ModuleConfig {
  title: string;
  icon: React.ComponentType<any>;
  items: SidebarItem[];
}

const MODULE_SIDEBARS: Record<string, ModuleConfig> = {
  setup: {
    title: 'Cycom Setup',
    icon: Sparkles,
    items: [
      { label: 'Setup Hub', href: '/setup', icon: LayoutGrid, dot: '#A855F7' },
      { label: 'Company', href: '/setup/company', icon: Building2, dot: '#E67E22' },
      { label: 'Chart of Accounts', href: '/setup', icon: Calculator, dot: '#5DADE2' },
      { label: 'Payroll Structure', href: '/setup', icon: DollarSign, dot: '#10B981' },
      { label: 'Warehouse', href: '/setup', icon: Package, dot: '#F59E0B' }
    ]
  },
  sign: {
    title: 'eSign Documents',
    icon: PenTool,
    items: [
      { label: 'Dashboard', href: '/sign', icon: BarChart2, dot: '#F43F5E' },
      { label: 'Templates', href: '/sign/templates', icon: FileText, dot: '#A855F7' },
      { label: 'Signature Requests', href: '/sign/requests', icon: Send, dot: '#00F0FF' }
    ]
  },
  sales: {
    title: 'Sales & Pricing',
    icon: TrendingUp,
    items: [
      { label: 'Overview', href: '/sales', icon: BarChart2, dot: '#3B82F6' },
      { label: 'Orders Registry', href: '/sales/orders', icon: Package, dot: '#10B981' },
      { label: 'Approvals', href: '/sales/approvals', icon: UserCheck, dot: '#F59E0B' }
    ]
  },
  pos: {
    title: 'Point of Sale',
    icon: ShoppingCart,
    items: [
      { label: 'Session Manager', href: '/pos', icon: BarChart2, dot: '#EF4444' },
      { label: 'Cash Drawer', href: '/pos#register', icon: DollarSign, dot: '#10B981' },
      { label: 'Advance & Pledge', href: '/pos#pledges', icon: FileText, dot: '#5DADE2' }
    ]
  },
  attendance: {
    title: 'Attendance',
    icon: Clock,
    items: [
      { label: 'Biometric Terminals', href: '/attendance', icon: Server, dot: '#F59E0B' },
      { label: 'Live event stream', href: '/attendance#logs', icon: Activity, dot: '#10B981' },
      { label: 'Overtime calculator', href: '/attendance#overtime', icon: Calculator, dot: '#EF4444' },
      { label: 'Geofence config', href: '/attendance#geofence', icon: MapPin, dot: '#3B82F6' },
      { label: 'Punch corrections', href: '/attendance#corrections', icon: Edit3, dot: '#EC4899' }
    ]
  },
  plm: {
    title: 'Manufacturing & PLM',
    icon: Layers,
    items: [
      { label: 'BOM Selector', href: '/plm', icon: Layers, dot: '#A855F7' },
      { label: 'Cost Analysis', href: '/plm#rollup', icon: Calculator, dot: '#10B981' },
      { label: 'ECO approvals', href: '/plm#ecos', icon: CheckCircle, dot: '#EF4444' }
    ]
  },
  expenses: {
    title: 'Expenses Claim',
    icon: FileSignature,
    items: [
      { label: 'Overview', href: '/expenses', icon: BarChart2, dot: '#EC4899' },
      { label: 'Log Expense', href: '/expenses#log', icon: Plus, dot: '#3B82F6' },
      { label: 'Approvals Queue', href: '/expenses#approvals', icon: Clipboard, dot: '#F59E0B' },
      { label: 'Ledger Record', href: '/expenses#ledger', icon: FileText, dot: '#10B981' }
    ]
  },
  project: {
    title: 'Project Management',
    icon: Layers,
    items: [
      { label: 'Kanban Board', href: '/project', icon: Layers, dot: '#3B82F6' },
      { label: 'Timesheets Logs', href: '/project#timesheets', icon: Clock, dot: '#10B981' },
      { label: 'Create Task', href: '/project#create', icon: Plus, dot: '#F59E0B' }
    ]
  }
};

const getModuleConfig = (segment: string): ModuleConfig => {
  if (MODULE_SIDEBARS[segment]) {
    return MODULE_SIDEBARS[segment];
  }
  // Generic Fallback Config
  const title = segment.charAt(0).toUpperCase() + segment.slice(1);
  return {
    title: title,
    icon: Layers,
    items: [
      { label: `${title} Dashboard`, href: `/${segment}`, icon: BarChart2, dot: '#3B82F6' }
    ]
  };
};

export default function CycomSidebar() {
  const pathname = usePathname() || '';
  const { activeCompany, setActiveCompany, allCompanies } = useCompany();
  const [companySwitcherOpen, setCompanySwitcherOpen] = useState(false);
  
  // Extract active module segment
  const segment = pathname.split('/')[1] || '';
  const moduleConfig = getModuleConfig(segment);
  const ModuleIcon = moduleConfig.icon;

  return (
    <aside className="w-[240px] h-screen flex flex-col flex-shrink-0 bg-gradient-to-b from-[#0a0f1e] to-[#080d18] border-r border-white/5 font-sans relative z-30">
      {/* Brand Header */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/5 flex-shrink-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#E67E22] to-[#5DADE2] flex items-center justify-center text-xs font-bold text-white shadow-lg shadow-orange-500/10">
          CY
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-0.5">
            <span className="text-[14px] font-black text-[#E67E22] tracking-wide">CY</span>
            <span className="text-[14px] font-black text-white tracking-wide">COM</span>
            <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-orange-500/20 text-[#E67E22] ml-2 border border-orange-500/30">ERP</span>
          </div>
          <div className="text-[9px] text-[#5DADE2] font-semibold uppercase tracking-wider mt-0.5">
            Cycom
          </div>
        </div>
      </div>

      {/* Launcher Back Button */}
      <div className="px-3 pt-3 pb-2 border-b border-white/5 flex-shrink-0">
        <Link 
          href="/" 
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-white/4 border border-white/8 hover:border-white/15 hover:bg-white/6 transition-all text-xs font-bold text-slate-300 hover:text-white"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Apps Launcher</span>
        </Link>
      </div>

      {/* Company Switcher */}
      <div className="px-3 pt-2 pb-1 flex-shrink-0">
        <button 
          onClick={() => setCompanySwitcherOpen(!companySwitcherOpen)}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl bg-white/3 border border-white/8 hover:border-white/12 transition-all text-left group"
        >
          <span className="text-base">{activeCompany.icon}</span>
          <div className="flex-1 min-w-0">
            <p className="text-[11px] font-bold text-white truncate">{activeCompany.shortName}</p>
            <p className="text-[9px] text-slate-500 font-medium truncate">{activeCompany.name}</p>
          </div>
          <ChevronDown className={`w-3.5 h-3.5 text-slate-500 transition-transform ${companySwitcherOpen ? 'rotate-180' : ''}`} />
        </button>
        
        {companySwitcherOpen && (
          <div className="mt-1.5 rounded-xl bg-[#0f1526] border border-white/10 overflow-hidden shadow-xl shadow-black/30 animate-slide-up">
            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest px-3 pt-2.5 pb-1">Switch Company</p>
            {allCompanies.map(company => (
              <button
                key={company.id}
                onClick={() => { setActiveCompany(company); setCompanySwitcherOpen(false); }}
                className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-all ${
                  activeCompany.id === company.id 
                    ? 'bg-orange-500/10 text-white' 
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                }`}
              >
                <span className="text-sm">{company.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-bold truncate">{company.shortName}</p>
                  <p className="text-[9px] text-slate-500 truncate">{company.name}</p>
                </div>
                {activeCompany.id === company.id && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#E67E22] shadow-lg shadow-orange-500/50" />
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Active Module Indicator */}
      <div className="px-5 py-4 border-b border-white/5 bg-white/[0.01] flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-orange-500/10 border border-orange-500/20 text-[#E67E22]">
            <ModuleIcon className="w-4.5 h-4.5" />
          </div>
          <div className="min-w-0">
            <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">Active Module</span>
            <h2 className="text-xs font-black text-white truncate uppercase tracking-wider">{moduleConfig.title}</h2>
          </div>
        </div>
      </div>

      {/* Dynamic Navigation Links */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {moduleConfig.items.map((item) => {
          const Icon = item.icon;
          // Determine if active based on path prefix
          const baseHref = item.href.split('#')[0];
          const active = pathname === baseHref || (baseHref !== '/' && pathname.startsWith(baseHref + '/'));
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all border ${
                active
                  ? 'bg-gradient-to-br from-orange-500/12 to-blue-500/8 border-orange-500/25 text-white shadow-md shadow-orange-500/5'
                  : 'border-transparent text-slate-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <Icon className={`w-4 h-4 ${active ? 'text-[#E67E22]' : 'text-slate-500'}`} />
              <span className={`text-[12.5px] ${active ? 'font-semibold' : 'font-medium'} truncate`}>
                {item.label}
              </span>
              <span
                className="ml-auto w-1.5 h-1.5 rounded-full flex-shrink-0"
                style={{
                  background: active ? item.dot : 'rgba(255,255,255,0.05)',
                  boxShadow: active ? `0 0 8px ${item.dot}` : 'none',
                }}
              />
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
