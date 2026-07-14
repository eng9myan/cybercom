'use client';

import React, { useState } from 'react';
import { Calendar, Plus, MessageSquare, Clock } from 'lucide-react';

const BALANCES = [
  { type: 'Annual Leave', total: 21, taken: 6.5, remaining: 14.5, unit: 'days', color: 'border-cyan-500/20' },
  { type: 'Sick Leave', total: 14, taken: 2, remaining: 12, unit: 'days', color: 'border-purple-500/20' },
  { type: 'Maternity/Paternity', total: 90, taken: 0, remaining: 90, unit: 'days', color: 'border-orange-500/20' },
];

export default function MyLeavesPortal() {
  const [leaveType, setLeaveType] = useState('Annual Leave');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [notes, setNotes] = useState('');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Leave Requests</h1>
          <p className="page-subtitle">Submit leave applications and monitor your remaining leave balances (portal_leaves).</p>
        </div>
      </div>

      {/* Leave Balances */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {BALANCES.map((b) => (
          <div key={b.type} className={`glass-card p-5 border ${b.color} space-y-3`}>
            <span className="text-xs text-slate-500 font-bold uppercase">{b.type}</span>
            <div className="flex justify-between items-end">
              <span className="text-3xl font-black text-white">{b.remaining} <span className="text-xs text-slate-400 font-normal">{b.unit}</span></span>
              <div className="text-right text-[10px] text-slate-500">
                <span>Total: {b.total} • Taken: {b.taken}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Form and History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Request Form */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Request Leave</h2>
          <div className="space-y-3 text-sm">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Leave Type</label>
              <select 
                className="input-field" 
                value={leaveType}
                onChange={(e) => setLeaveType(e.target.value)}
              >
                <option value="Annual Leave">Annual Leave</option>
                <option value="Sick Leave">Sick Leave</option>
                <option value="Unpaid Leave">Unpaid Leave (Trigger fallback)</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Start Date</label>
                <input 
                  type="date" 
                  className="input-field font-mono" 
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">End Date</label>
                <input 
                  type="date" 
                  className="input-field font-mono" 
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Notes / Reason</label>
              <textarea 
                className="input-field min-h-[80px]" 
                placeholder="Reason for requesting leave..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
            <button className="btn-primary w-full py-2.5">
              Submit Request
            </button>
          </div>
        </div>

        {/* History */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">My Leave Applications</h2>
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-white/5 border border-white/5 flex justify-between items-center text-xs">
              <div className="space-y-1">
                <span className="font-bold text-slate-200 block">Annual Leave</span>
                <span className="text-slate-500 block">8 days (Jun 15 - Jun 22)</span>
              </div>
              <span className="badge badge-yellow">Pending Review</span>
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/5 flex justify-between items-center text-xs">
              <div className="space-y-1">
                <span className="font-bold text-slate-200 block">Sick Leave</span>
                <span className="text-slate-500 block">2 days (Jun 12 - Jun 13)</span>
              </div>
              <div className="text-right space-y-1">
                <span className="badge badge-red block">Rejected</span>
                <span className="text-[10px] text-amber-500 block">Fell back to unpaid</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
