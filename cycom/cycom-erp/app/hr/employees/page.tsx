'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users, Search, Filter, Plus, ShieldAlert,
  Phone, Mail, CheckCircle, CreditCard, X,
  FileSpreadsheet
} from 'lucide-react';
import { searchRead } from '@/lib/cycom';
import { useT } from '@/lib/i18n';

/**
 * Employee Directory
 * --------------------
 * Visual design is unchanged from the original Cycom mockup. The ONLY substantive change
 * is that data is now sourced from Cycom's `hr.employee` model (via /api/cycom/call) instead
 * of a hardcoded INITIAL list.
 */

type Employee = {
  id: string;       // formatted code, e.g. EMP-00249
  rawId: number;    // Cycom numeric id
  name: string;
  role: string;
  department: string;
  email: string;
  phone: string;
  location: string;
  joined: string;
  spouse: string;
  portalAccess: boolean;
  singleDevice: string;
  bank: string;
  iban: string;
  grade: string;
};

type CycomEmployeeRecord = {
  id: number;
  name?: string;
  work_email?: string | false;
  work_phone?: string | false;
  work_location_id?: [number, string] | false;
  department_id?: [number, string] | false;
  job_title?: string | false;
  create_date?: string;
  parent_id?: [number, string] | false;
};

function formatJoined(create_date?: string): string {
  if (!create_date) return '—';
  // Cycom returns "YYYY-MM-DD HH:mm:ss"
  const d = new Date(create_date.replace(' ', 'T') + 'Z');
  if (isNaN(d.getTime())) return create_date;
  return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
}

function cycomToEmployee(r: CycomEmployeeRecord): Employee {
  return {
    rawId: r.id,
    id: `EMP-${String(r.id).padStart(5, '0')}`,
    name: r.name || '—',
    role: (r.job_title as string) || 'Unassigned',
    department: r.department_id ? r.department_id[1] : 'Unassigned',
    email: (r.work_email as string) || '—',
    phone: (r.work_phone as string) || '—',
    location: r.work_location_id ? r.work_location_id[1] : '—',
    joined: formatJoined(r.create_date),
    spouse: 'N/A',
    portalAccess: false,
    singleDevice: 'N/A',
    bank: 'N/A',
    iban: 'N/A',
    grade: 'N/A',
  };
}

export default function EmployeeDirectory() {
  const t = useT();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEmp, setSelectedEmp] = useState<Employee | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    searchRead<CycomEmployeeRecord>(
      'hr.employee',
      [['active', '=', true]],
      ['name', 'work_email', 'work_phone', 'work_location_id', 'department_id', 'job_title', 'create_date', 'parent_id'],
      { limit: 500, order: 'name asc' },
    )
      .then((rows) => {
        if (cancelled) return;
        setEmployees(rows.map(cycomToEmployee));
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load employees from Cycom');
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredEmployees = employees.filter(emp =>
    emp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('hrEmployees.title')}</h1>
          <p className="page-subtitle">{t('hrEmployees.subtitle')}</p>
        </div>
        <div className="flex gap-3">
          <Link href="/hr/employees/import" className="btn-secondary flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-emerald-500" /> {t('hrEmployees.importEmployees')}
          </Link>
          <button className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> {t('hrEmployees.addEmployee')}
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute start-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder={t('hrEmployees.searchPh')}
            className="input-field !ps-10 !py-2.5"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <Filter className="w-4 h-4" /> {t('hrEmployees.filters')}
        </button>
      </div>

      {loading && (
        <div className="glass-card p-8 text-center text-slate-400 text-sm">
          {t('hrEmployees.loading')}
        </div>
      )}

      {error && (
        <div className="glass-card p-6 border border-rose-500/30 bg-rose-500/5 text-sm">
          <p className="text-rose-300 font-semibold mb-1">{t('hrEmployees.loadError')}</p>
          <p className="text-rose-400/80 text-xs">{error}</p>
          <p className="text-slate-500 text-[10px] mt-2">{t('hrEmployees.loadErrorHint')}</p>
        </div>
      )}

      {/* Directory Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredEmployees.map((emp, i) => (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.05 }}
            key={emp.id}
            onClick={() => setSelectedEmp(emp)}
            className="glass-card p-6 cursor-pointer relative group flex flex-col justify-between"
          >
            <div>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className="text-[10px] font-mono text-cyan-400 font-bold bg-cyan-950/40 border border-cyan-800/30 px-2 py-0.5 rounded">
                    {emp.id}
                  </span>
                  <h3 className="text-lg font-bold text-white mt-2 group-hover:text-[#E67E22] transition-colors">{emp.name}</h3>
                  <p className="text-xs text-slate-400">{emp.role}</p>
                </div>
                <div className="flex flex-col items-end gap-1.5">
                  <span className="badge badge-purple">{emp.department}</span>
                  <span className="text-[10px] text-slate-500">{emp.location}</span>
                </div>
              </div>

              <div className="space-y-2 border-t border-white/5 pt-4 text-xs text-slate-400">
                <div className="flex items-center gap-2">
                  <Mail className="w-3.5 h-3.5 text-slate-500" />
                  <span>{emp.email}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Phone className="w-3.5 h-3.5 text-slate-500" />
                  <span>{emp.phone}</span>
                </div>
              </div>
            </div>

            <div className="border-t border-white/5 pt-4 mt-4 flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5">
                {emp.portalAccess ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                ) : (
                  <ShieldAlert className="w-4 h-4 text-amber-500" />
                )}
                <span className="text-slate-500">{t('hrEmployees.portalLabel')}</span>
                <span className={emp.portalAccess ? 'text-emerald-400 font-semibold' : 'text-amber-500 font-semibold'}>
                  {emp.portalAccess ? t('hrEmployees.portalActive') : t('hrEmployees.portalPending')}
                </span>
              </div>
              <span className="text-slate-500">{t('hrEmployees.joined', { date: emp.joined })}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {!loading && !error && filteredEmployees.length === 0 && (
        <div className="glass-card p-8 text-center text-slate-500 text-sm">
          {t('hrEmployees.noEmployees')}
        </div>
      )}

      {/* Detail Slide-out Overlay */}
      <AnimatePresence>
        {selectedEmp && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedEmp(null)}
              className="fixed inset-0 bg-black z-40"
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 end-0 bottom-0 w-full max-w-lg bg-[#0B0F19] border-s border-white/10 p-8 z-50 overflow-y-auto space-y-6"
            >
              <div className="flex justify-between items-center pb-4 border-b border-white/5">
                <div>
                  <span className="text-xs font-mono text-cyan-400 font-bold bg-cyan-950/40 border border-cyan-800/30 px-2 py-0.5 rounded">
                    {selectedEmp.id}
                  </span>
                  <h2 className="text-2xl font-bold text-white mt-2">{selectedEmp.name}</h2>
                  <p className="text-sm text-slate-400">{selectedEmp.role}</p>
                </div>
                <button
                  onClick={() => setSelectedEmp(null)}
                  className="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Profile Details */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">{t('hrEmployees.employmentDetails')}</h3>
                  <div className="grid grid-cols-2 gap-4 bg-white/5 p-4 rounded-xl border border-white/5 text-sm">
                    <div>
                      <span className="text-xs text-slate-500 block">{t('hrEmployees.department')}</span>
                      <span className="text-slate-200 font-semibold">{selectedEmp.department}</span>
                    </div>
                    <div>
                      <span className="text-xs text-slate-500 block">{t('hrEmployees.workLocation')}</span>
                      <span className="text-slate-200 font-semibold">{selectedEmp.location}</span>
                    </div>
                    <div>
                      <span className="text-xs text-slate-500 block">{t('hrEmployees.dateJoined')}</span>
                      <span className="text-slate-200 font-semibold">{selectedEmp.joined}</span>
                    </div>
                    <div>
                      <span className="text-xs text-slate-500 block">{t('hrEmployees.healthGrade')}</span>
                      <span className="text-slate-200 font-semibold">{selectedEmp.grade}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">{t('hrEmployees.familySocial')}</h3>
                  <div className="grid grid-cols-2 gap-4 bg-white/5 p-4 rounded-xl border border-white/5 text-sm">
                    <div>
                      <span className="text-xs text-slate-500 block">{t('hrEmployees.spouseName')}</span>
                      <span className="text-slate-200 font-semibold">{selectedEmp.spouse}</span>
                    </div>
                    <div>
                      <span className="text-xs text-slate-500 block">{t('hrEmployees.portalStatus')}</span>
                      <span className={selectedEmp.portalAccess ? 'text-emerald-400 font-semibold' : 'text-amber-500 font-semibold'}>
                        {selectedEmp.portalAccess ? t('hrEmployees.portalAutoActive') : t('hrEmployees.portalDenied')}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">{t('hrEmployees.securitySection')}</h3>
                  <div className="bg-white/5 p-4 rounded-xl border border-white/5 text-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-xs text-slate-500 block">{t('hrEmployees.singleDeviceBinding')}</span>
                        <span className="text-slate-200 font-semibold">{selectedEmp.singleDevice}</span>
                      </div>
                      <span className={`badge ${selectedEmp.singleDevice !== 'N/A' ? 'badge-cyan' : 'badge-red'}`}>
                        {selectedEmp.singleDevice !== 'N/A' ? t('hrEmployees.locked') : t('hrEmployees.noDevice')}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-500">
                      {t('hrEmployees.singleDeviceNote')}
                    </p>
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">{t('hrEmployees.bankSection')}</h3>
                  <div className="bg-white/5 p-4 rounded-xl border border-white/5 text-sm space-y-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded bg-cyan-950/40 text-cyan-400 border border-cyan-800/30">
                        <CreditCard className="w-5 h-5" />
                      </div>
                      <div>
                        <span className="text-xs text-slate-500 block">{t('hrEmployees.bankName')}</span>
                        <span className="text-slate-200 font-semibold">{selectedEmp.bank}</span>
                      </div>
                    </div>
                    <div>
                      <span className="text-xs text-slate-500 block">{t('hrEmployees.ibanNumber')}</span>
                      <span className="text-slate-200 font-mono select-all text-xs font-semibold text-slate-300 block bg-black/40 p-2 rounded border border-white/5 mt-1" dir="ltr">
                        {selectedEmp.iban}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
