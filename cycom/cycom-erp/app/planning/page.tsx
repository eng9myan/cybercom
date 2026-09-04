'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCycomList, m2oName, type Many2One } from '@/lib/cycomModels';
import { create, unlink } from '@/lib/cycom';
import {
  Clock, AlertTriangle, Trash2
} from 'lucide-react';
import { useT } from '@/lib/i18n';

interface ShiftSlot {
  id: string;
  employeeName: string;
  role: string;
  department: 'Sales' | 'Warehouse' | 'Finance' | 'IT';
  day: 'Mon' | 'Tue' | 'Wed' | 'Thu' | 'Fri' | 'Sat' | 'Sun';
  hours: number;
  timeRange: string;
}

type CycomPlanningSlot = {
  id: number;
  resource_id?: Many2One;
  role_id?: Many2One;
  start_datetime?: string;
  end_datetime?: string;
  state?: string;
};

const DAY_ABBRS: ShiftSlot['day'][] = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const mapPlanningSlot = (r: CycomPlanningSlot): ShiftSlot => {
  const start = r.start_datetime ? new Date(r.start_datetime.replace(' ', 'T') + 'Z') : null;
  const end = r.end_datetime ? new Date(r.end_datetime.replace(' ', 'T') + 'Z') : null;
  const hours = start && end ? Math.round((end.getTime() - start.getTime()) / 3600000) : 0;
  const day: ShiftSlot['day'] = start ? DAY_ABBRS[start.getDay()] : 'Mon';
  const fmt = (d: Date) => d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  const timeRange = start && end ? `${fmt(start)} - ${fmt(end)}` : '—';
  return {
    id: `SFT-${r.id}`,
    employeeName: m2oName(r.resource_id, '—'),
    role: m2oName(r.role_id, '—'),
    department: 'Sales',
    day,
    hours,
    timeRange,
  };
};

const DEPT_COLORS = {
  Sales: 'bg-blue-500/10 text-blue-400 border-blue-500/25',
  Warehouse: 'bg-orange-500/10 text-orange-400 border-orange-500/25',
  Finance: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25',
  IT: 'bg-purple-500/10 text-purple-400 border-purple-500/25',
};

const DAY_KEY: Record<ShiftSlot['day'], string> = {
  Mon: 'planningDash.dayMon', Tue: 'planningDash.dayTue', Wed: 'planningDash.dayWed',
  Thu: 'planningDash.dayThu', Fri: 'planningDash.dayFri', Sat: 'planningDash.daySat', Sun: 'planningDash.daySun',
};

export default function PlanningPage() {
  const t = useT();
  const DEPT_LABEL: Record<ShiftSlot['department'], string> = {
    Sales: t('planningDash.deptSales'), Warehouse: t('planningDash.deptWarehouse'),
    Finance: t('planningDash.deptFinance'), IT: t('planningDash.deptIt'),
  };
  const { rows: liveSlots, loading } = useCycomList<CycomPlanningSlot, ShiftSlot>(
    'planning.slot', [], ['resource_id', 'role_id', 'start_datetime', 'end_datetime', 'state'],
    mapPlanningSlot,
  );
  const [shifts, setShifts] = useState<ShiftSlot[]>([]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (!loading) setShifts(liveSlots); }, [loading]);

  // New slot form states
  const [empName, setEmpName] = useState('Ahmad Masri');
  const [role, setRole] = useState('Staff Operator');
  const [dept, setDept] = useState<'Sales' | 'Warehouse' | 'Finance' | 'IT'>('Sales');
  const [day, setDay] = useState<'Mon' | 'Tue' | 'Wed' | 'Thu' | 'Fri' | 'Sat' | 'Sun'>('Mon');
  const [hours, setHours] = useState('8');
  const [timeRange, setTimeRange] = useState('08:00 - 16:00');

  // Conflict state warning
  const [warningMsg, setWarningMsg] = useState<string | null>(null);

  const checkConflict = (newShift: Omit<ShiftSlot, 'id'>) => {
    // 1. Overlapping shift check (same employee, same day)
    const overlap = shifts.find(s => s.employeeName === newShift.employeeName && s.day === newShift.day);
    if (overlap) {
      return t('planningDash.conflictAlert', {
        employee: newShift.employeeName, range: overlap.timeRange, day: t(DAY_KEY[newShift.day]),
      });
    }

    // 2. Weekly Hour Limit Check (> 48 hours)
    const existingHours = shifts.filter(s => s.employeeName === newShift.employeeName).reduce((acc, curr) => acc + curr.hours, 0);
    if (existingHours + newShift.hours > 48) {
      return t('planningDash.hoursWarning', {
        employee: newShift.employeeName, hours: existingHours + newShift.hours,
      });
    }

    return null;
  };

  // day (Mon..Sun) + "HH:MM - HH:MM" → concrete ISO datetimes in the current week.
  const slotDatetimes = (dayAbbr: string, range: string): { start: string; end: string } => {
    const order = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const targetDow = order.indexOf(dayAbbr);
    const base = new Date();
    base.setDate(base.getDate() + ((targetDow - base.getDay() + 7) % 7));
    const [from, to] = range.split('-').map((s) => s.trim());
    const mk = (hm: string) => {
      const [h, m] = hm.split(':').map((n) => parseInt(n) || 0);
      const d = new Date(base);
      d.setHours(h, m, 0, 0);
      return d.toISOString();
    };
    return { start: mk(from || '08:00'), end: mk(to || '16:00') };
  };

  const handleCreateSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsedHours = parseInt(hours) || 8;
    const newShift = {
      employeeName: empName,
      role: role,
      department: dept,
      day: day,
      hours: parsedHours,
      timeRange: timeRange
    };

    const conflict = checkConflict(newShift);
    setWarningMsg(conflict);

    const { start, end } = slotDatetimes(day, timeRange);
    try {
      const id = await create('planning.slot', {
        resource_name: empName,
        role,
        department: dept.toLowerCase(),
        start_datetime: start,
        end_datetime: end,
      });
      setShifts([...shifts, { id: `SFT-${id}`, ...newShift }]);
    } catch {
      /* keep form populated for retry */
    }
  };

  const handleDeleteShift = async (id: string) => {
    setShifts(shifts.filter(s => s.id !== id));
    const rawId = id.replace('SFT-', '');
    try { await unlink('planning.slot', [rawId as unknown as number]); } catch { /* swallow */ }
  };

  const DAYS: Array<'Mon' | 'Tue' | 'Wed' | 'Thu' | 'Fri' | 'Sat' | 'Sun'> = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>{t('planningDash.loading')}</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('planningDash.title')}</h1>
          <p className="page-subtitle">{t('planningDash.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column - Shift Creator */}
        <div className="space-y-6">
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('planningDash.formHeading')}</h2>
              <Clock className="w-4 h-4 text-[#EF4444]" />
            </div>

            <form onSubmit={handleCreateSlot} className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('planningDash.employee')}</label>
                <select
                  value={empName}
                  onChange={e => setEmpName(e.target.value)}
                  className="input-field"
                >
                  <option value="Ahmad Masri">Ahmad Masri</option>
                  <option value="Sara Haddad">Sara Haddad</option>
                  <option value="Rami Khasawneh">Rami Khasawneh</option>
                  <option value="Khaled Jaber">Khaled Jaber</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('planningDash.categoryDept')}</label>
                  <select
                    value={dept}
                    onChange={e => setDept(e.target.value as any)}
                    className="input-field"
                  >
                    <option value="Sales">{t('planningDash.deptSales')}</option>
                    <option value="Warehouse">{t('planningDash.deptWarehouse')}</option>
                    <option value="Finance">{t('planningDash.deptFinance')}</option>
                    <option value="IT">{t('planningDash.deptIt')}</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('planningDash.jobRoleTitle')}</label>
                  <input
                    type="text"
                    required
                    placeholder={t('planningDash.jobRoleTitlePh')}
                    value={role}
                    onChange={e => setRole(e.target.value)}
                    className="input-field"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('planningDash.weekday')}</label>
                  <select
                    value={day}
                    onChange={e => setDay(e.target.value as any)}
                    className="input-field"
                  >
                    {DAYS.map(d => <option key={d} value={d}>{t(DAY_KEY[d])}</option>)}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('planningDash.hours')}</label>
                  <input
                    type="number"
                    required
                    value={hours}
                    onChange={e => setHours(e.target.value)}
                    className="input-field font-mono"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('planningDash.timeRange')}</label>
                  <input
                    type="text"
                    required
                    placeholder={t('planningDash.timeRangePh')}
                    value={timeRange}
                    onChange={e => setTimeRange(e.target.value)}
                    className="input-field font-mono"
                  />
                </div>
              </div>

              {/* Conflict Warnings Box */}
              <AnimatePresence>
                {warningMsg && (
                  <motion.div
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 5 }}
                    className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-[#EF4444] text-[10px] leading-relaxed flex gap-2"
                  >
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <span>{warningMsg}</span>
                  </motion.div>
                )}
              </AnimatePresence>

              <button type="submit" className="btn-primary w-full py-2">
                {t('planningDash.allocateBtn')}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column - Visual Shift Timeline Calendar */}
        <div className="lg:col-span-2 space-y-6">

          {/* Calendar timeline visual board */}
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">{t('planningDash.boardHeading')}</h2>

            <div className="grid grid-cols-8 gap-2 text-center text-xs font-bold border-b border-white/5 pb-2">
              <div className="text-start text-slate-500">{t('planningDash.employeeCol')}</div>
              {DAYS.map(d => <div key={d} className="text-slate-400">{t(DAY_KEY[d])}</div>)}
            </div>

            <div className="space-y-3 pt-2">
              {['Ahmad Masri', 'Sara Haddad', 'Rami Khasawneh', 'Khaled Jaber'].map(emp => {
                const empWeeklyHours = shifts.filter(s => s.employeeName === emp).reduce((acc, curr) => acc + curr.hours, 0);
                return (
                  <div key={emp} className="grid grid-cols-8 gap-2 items-center min-h-[48px] py-1 border-b border-white/3 last:border-none">
                    <div className="text-start">
                      <p className="text-xs font-bold text-white truncate">{emp.split(' ')[0]}</p>
                      <p className="text-[9px] text-slate-500 font-mono font-bold mt-0.5">{t('planningDash.hoursTotalN', { n: empWeeklyHours })}</p>
                    </div>
                    {DAYS.map(d => {
                      const dayShifts = shifts.filter(s => s.employeeName === emp && s.day === d);
                      return (
                        <div key={d} className="h-full flex flex-col gap-1 justify-center">
                          {dayShifts.map(s => (
                            <div
                              key={s.id}
                              className={`p-1.5 rounded text-[9px] border leading-tight flex flex-col text-center font-bold ${DEPT_COLORS[s.department]}`}
                              title={`${s.role} (${s.timeRange})`}
                            >
                              <span>{s.role.split(' ')[0]}</span>
                              <span className="text-[8px] opacity-70 font-mono font-semibold">{s.hours}h</span>
                            </div>
                          ))}
                          {dayShifts.length === 0 && (
                            <div className="h-8 rounded bg-white/2 border border-dashed border-white/5 flex items-center justify-center text-[9px] text-slate-700 font-bold">{t('planningDash.off')}</div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Slots List */}
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">{t('planningDash.ledgerHeading')}</h2>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('planningDash.colSlotId')}</th>
                    <th>{t('planningDash.colEmployeeName')}</th>
                    <th>{t('planningDash.colDeptCategory')}</th>
                    <th>{t('planningDash.colRoleTitle')}</th>
                    <th>{t('planningDash.colDay')}</th>
                    <th>{t('planningDash.colHours')}</th>
                    <th>{t('planningDash.colTimePeriod')}</th>
                    <th className="text-end">{t('planningDash.colActions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {shifts.map(s => (
                    <tr key={s.id}>
                      <td className="font-mono text-xs">{s.id}</td>
                      <td className="font-bold text-slate-300">{s.employeeName}</td>
                      <td>
                        <span className={`badge text-[9px] ${
                          s.department === 'Sales' ? 'badge-blue' :
                          s.department === 'Warehouse' ? 'badge-orange' :
                          s.department === 'Finance' ? 'badge-green' : 'badge-purple'
                        }`}>{DEPT_LABEL[s.department]}</span>
                      </td>
                      <td>{s.role}</td>
                      <td className="font-bold">{t(DAY_KEY[s.day])}</td>
                      <td className="font-mono font-bold">{t('planningDash.hrsN', { n: s.hours })}</td>
                      <td className="font-mono text-slate-400">{s.timeRange}</td>
                      <td className="text-end">
                        <button
                          onClick={() => handleDeleteShift(s.id)}
                          className="p-1 rounded hover:bg-red-500/20 text-[#EF4444]"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
