'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCycomList, m2oName, type Many2One } from '@/lib/cycomModels';
import { 
  Clock, Plus, Calendar, AlertTriangle, CheckCircle, 
  Trash2, User, UserPlus, Info, CheckSquare
} from 'lucide-react';

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

export default function PlanningPage() {
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
      return `Conflict Alert: ${newShift.employeeName} is already scheduled for shift (${overlap.timeRange}) on ${newShift.day}. Overlapping slots detected.`;
    }

    // 2. Weekly Hour Limit Check (> 48 hours)
    const existingHours = shifts.filter(s => s.employeeName === newShift.employeeName).reduce((acc, curr) => acc + curr.hours, 0);
    if (existingHours + newShift.hours > 48) {
      return `Warning: Scheduling this slot puts ${newShift.employeeName} at ${existingHours + newShift.hours} hours this week, exceeding standard 48 hours limit.`;
    }

    return null;
  };

  const handleCreateSlot = (e: React.FormEvent) => {
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
    if (conflict) {
      setWarningMsg(conflict);
      // We still record it in Cycom warning mode, but flag it
    } else {
      setWarningMsg(null);
    }

    const slot: ShiftSlot = {
      id: `SFT-${Math.floor(10 + Math.random() * 90)}`,
      ...newShift
    };

    setShifts([...shifts, slot]);
  };

  const handleDeleteShift = (id: string) => {
    setShifts(shifts.filter(s => s.id !== id));
  };

  const DAYS: Array<'Mon' | 'Tue' | 'Wed' | 'Thu' | 'Fri' | 'Sat' | 'Sun'> = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Planning & Shift Schedules</h1>
          <p className="page-subtitle">Schedule staff roster shifts, audit overlapping hour conflicts, and track weekly work thresholds.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column - Shift Creator */}
        <div className="space-y-6">
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Roster Planner Form</h2>
              <Clock className="w-4 h-4 text-[#EF4444]" />
            </div>

            <form onSubmit={handleCreateSlot} className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Employee</label>
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
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Category / Dept</label>
                  <select 
                    value={dept} 
                    onChange={e => setDept(e.target.value as any)}
                    className="input-field"
                  >
                    <option value="Sales">Sales Operations</option>
                    <option value="Warehouse">Warehouse Supply</option>
                    <option value="Finance">Finance Accounting</option>
                    <option value="IT">IT Infrastructure</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Job Role Title</label>
                  <input 
                    type="text" 
                    required 
                    placeholder="e.g. Day Clerk" 
                    value={role}
                    onChange={e => setRole(e.target.value)}
                    className="input-field"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Weekday</label>
                  <select 
                    value={day} 
                    onChange={e => setDay(e.target.value as any)}
                    className="input-field"
                  >
                    {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Hours</label>
                  <input 
                    type="number" 
                    required 
                    value={hours} 
                    onChange={e => setHours(e.target.value)}
                    className="input-field font-mono"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Time Range</label>
                  <input 
                    type="text" 
                    required 
                    placeholder="08:00-16:00" 
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
                Allocate Shift Slot
              </button>
            </form>
          </div>
        </div>

        {/* Right Column - Visual Shift Timeline Calendar */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Calendar timeline visual board */}
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">Weekly Schedule Board</h2>
            
            <div className="grid grid-cols-8 gap-2 text-center text-xs font-bold border-b border-white/5 pb-2">
              <div className="text-left text-slate-500">Employee</div>
              {DAYS.map(d => <div key={d} className="text-slate-400">{d}</div>)}
            </div>

            <div className="space-y-3 pt-2">
              {['Ahmad Masri', 'Sara Haddad', 'Rami Khasawneh', 'Khaled Jaber'].map(emp => {
                const empWeeklyHours = shifts.filter(s => s.employeeName === emp).reduce((acc, curr) => acc + curr.hours, 0);
                return (
                  <div key={emp} className="grid grid-cols-8 gap-2 items-center min-h-[48px] py-1 border-b border-white/3 last:border-none">
                    <div className="text-left">
                      <p className="text-xs font-bold text-white truncate">{emp.split(' ')[0]}</p>
                      <p className="text-[9px] text-slate-500 font-mono font-bold mt-0.5">{empWeeklyHours} hrs total</p>
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
                            <div className="h-8 rounded bg-white/2 border border-dashed border-white/5 flex items-center justify-center text-[9px] text-slate-700 font-bold">OFF</div>
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
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">Shift Registry Ledger</h2>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Slot ID</th>
                    <th>Employee Name</th>
                    <th>Dept Category</th>
                    <th>Role Title</th>
                    <th>Day</th>
                    <th>Hours</th>
                    <th>Time Period</th>
                    <th className="text-right">Actions</th>
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
                        }`}>{s.department}</span>
                      </td>
                      <td>{s.role}</td>
                      <td className="font-bold">{s.day}</td>
                      <td className="font-mono font-bold">{s.hours} hrs</td>
                      <td className="font-mono text-slate-400">{s.timeRange}</td>
                      <td className="text-right">
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
