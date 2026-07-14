'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, MapPin, Calendar, FileText, CheckCircle2, 
  AlertTriangle, RefreshCw, Clock, ArrowRight, UserCheck
} from 'lucide-react';
import { useCycomList, fmtCode, m2oName, type Many2One } from '@/lib/cycomModels';

interface PortalLeave {
  id: string;
  type: string;
  startDate: string;
  endDate: string;
  reason: string;
  status: 'Pending' | 'Approved' | 'Rejected';
}

interface PortalPayslip {
  id: string;
  period: string;
  baseSalary: number;
  netSalary: number;
  datePaid: string;
}

const INITIAL_LEAVES: PortalLeave[] = [
  { id: 'LV-390', type: 'Annual Leave', startDate: '2026-06-15', endDate: '2026-06-22', reason: 'Family trip to Aqaba', status: 'Pending' },
  { id: 'LV-382', type: 'Sick Leave', startDate: '2026-05-12', endDate: '2026-05-13', reason: 'Flu recovery', status: 'Approved' },
];

const INITIAL_PAYSLIPS: PortalPayslip[] = [
  { id: 'PS-1209', period: 'May 2026', baseSalary: 750, netSalary: 884, datePaid: '2026-05-28' },
  { id: 'PS-1192', period: 'April 2026', baseSalary: 750, netSalary: 750, datePaid: '2026-04-28' },
];

export default function PortalDashboard() {
  const { rows: liveLeaves, loading: leavesLoading } = useCycomList<any, PortalLeave>(
    'hr.leave',
    [],
    ['leave_type', 'start_date', 'end_date', 'days', 'status'],
    (r) => {
      let status: 'Pending' | 'Approved' | 'Rejected' = 'Pending';
      if (r.status === 'approved' || r.state === 'validate') status = 'Approved';
      else if (r.status === 'rejected' || r.state === 'refuse') status = 'Rejected';
      return {
        id: fmtCode('LV', r.id, 3),
        type: r.holiday_status_id ? m2oName(r.holiday_status_id) : (r.leave_type ? r.leave_type.toUpperCase() + ' Leave' : 'Leave'),
        startDate: r.date_from ? r.date_from.split(' ')[0] : (r.start_date ? String(r.start_date) : '—'),
        endDate: r.date_to ? r.date_to.split(' ')[0] : (r.end_date ? String(r.end_date) : '—'),
        reason: r.name || 'Personal leave',
        status
      };
    }
  );

  const { rows: livePayslips, loading: paysLoading } = useCycomList<any, PortalPayslip>(
    'hr.payslip',
    [],
    ['period', 'gross', 'net', 'status'],
    (r) => ({
      id: fmtCode('PS', r.id, 4),
      period: r.period || 'Monthly Payslip',
      baseSalary: Number(r.gross ?? 0),
      netSalary: Number(r.net ?? 0),
      datePaid: r.date_to ? r.date_to.split(' ')[0] : (r.period ? `${r.period}-28` : '—')
    })
  );

  const [leaves, setLeaves] = useState<PortalLeave[]>(INITIAL_LEAVES);
  const [payslips, setPayslips] = useState<PortalPayslip[]>(INITIAL_PAYSLIPS);

  useEffect(() => {
    if (!leavesLoading && liveLeaves.length > 0) {
      setLeaves(liveLeaves);
    }
  }, [liveLeaves, leavesLoading]);

  useEffect(() => {
    if (!paysLoading && livePayslips.length > 0) {
      setPayslips(livePayslips);
    }
  }, [livePayslips, paysLoading]);
  
  // Leave form states
  const [leaveType, setLeaveType] = useState('Annual Leave');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [leaveReason, setLeaveReason] = useState('');
  const [leaveSuccess, setLeaveSuccess] = useState(false);

  // Check-In Location states
  const [gpsLat, setGpsLat] = useState('31.9522'); // HQ
  const [gpsLng, setGpsLng] = useState('35.9250');
  const [checkInStatus, setCheckInStatus] = useState<'idle' | 'success' | 'out_of_bounds'>('idle');
  const [lastCheckTime, setLastCheckTime] = useState<string | null>(null);

  // GPS Simulators helper
  const setSimulatedLocation = (preset: 'HQ' | 'Outside') => {
    if (preset === 'HQ') {
      setGpsLat('31.9522');
      setGpsLng('35.9250');
    } else {
      setGpsLat('31.9745'); // roughly 4km away
      setGpsLng('35.8430');
    }
    setCheckInStatus('idle');
  };

  // Distance calculator helper (Haversine formula)
  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    const R = 6371e3; // Earth radius in meters
    const phi1 = lat1 * Math.PI/180;
    const phi2 = lat2 * Math.PI/180;
    const deltaPhi = (lat2-lat1) * Math.PI/180;
    const deltaLambda = (lon2-lon1) * Math.PI/180;

    const a = Math.sin(deltaPhi/2) * Math.sin(deltaPhi/2) +
              Math.cos(phi1) * Math.cos(phi2) *
              Math.sin(deltaLambda/2) * Math.sin(deltaLambda/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c; // in meters
  };

  // Perform geofence check (Cycom: hr_attendance_geofence_config)
  const handleCheckIn = () => {
    const lat = parseFloat(gpsLat);
    const lng = parseFloat(gpsLng);
    
    // HQ Coords
    const hqLat = 31.9522;
    const hqLng = 35.9250;
    const allowedRadius = 150; // 150 meters

    const distance = calculateDistance(lat, lng, hqLat, hqLng);

    if (distance <= allowedRadius) {
      setCheckInStatus('success');
      setLastCheckTime(new Date().toLocaleTimeString());
    } else {
      setCheckInStatus('out_of_bounds');
    }
  };

  const handleLeaveSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!startDate || !endDate || !leaveReason) return;

    const newLeave: PortalLeave = {
      id: `LV-${Math.floor(391 + Math.random() * 200)}`,
      type: leaveType,
      startDate: startDate,
      endDate: endDate,
      reason: leaveReason,
      status: 'Pending'
    };

    setLeaves([newLeave, ...leaves]);
    setLeaveSuccess(true);
    setStartDate('');
    setEndDate('');
    setLeaveReason('');
    setTimeout(() => setLeaveSuccess(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Employee Self-Service Portal</h1>
          <p className="page-subtitle">Submit leaf requests, verify GPS coordinates for mobile check-in, and download historical payslips.</p>
        </div>
        <div className="flex gap-2 items-center text-xs text-slate-400">
          <Clock className="w-4 h-4 text-cyan-400" />
          <span>Active Session: <strong>Ahmad Masri (EMP-029)</strong></span>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column - Geofenced Mobile Check-In */}
        <div className="space-y-6">
          
          {/* Mobile Check-In Console */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Mobile GPS Check-In</h2>
              <span className="text-[10px] bg-blue-500/20 text-[#5DADE2] border border-blue-500/30 px-2 py-0.5 rounded font-bold">
                portal_check_in
              </span>
            </div>

            <div className="space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-white/3 border border-white/5 space-y-2">
                <p className="font-bold text-slate-300">HQ Geofence Constraint</p>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Checked coordinates must be within <strong>150 meters</strong> of HQ Center (31.9522, 35.9250).
                </p>
              </div>

              {/* GPS coordinates mock inputs */}
              <div className="grid grid-cols-2 gap-2 font-mono">
                <div className="space-y-1">
                  <label className="text-[9px] text-slate-500 uppercase font-bold">Latitude (GPS)</label>
                  <input 
                    type="number" 
                    step="0.0001" 
                    value={gpsLat}
                    onChange={e => { setGpsLat(e.target.value); setCheckInStatus('idle'); }}
                    className="input-field py-1"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[9px] text-slate-500 uppercase font-bold">Longitude (GPS)</label>
                  <input 
                    type="number" 
                    step="0.0001" 
                    value={gpsLng}
                    onChange={e => { setGpsLng(e.target.value); setCheckInStatus('idle'); }}
                    className="input-field py-1"
                  />
                </div>
              </div>

              {/* Coordinates Simulator presets */}
              <div className="flex gap-2">
                <button 
                  onClick={() => setSimulatedLocation('HQ')}
                  className="flex-1 py-1 rounded bg-[#10B981]/10 hover:bg-[#10B981]/20 border border-[#10B981]/25 text-[#10B981] font-bold text-[10px]"
                >
                  Preset: At HQ
                </button>
                <button 
                  onClick={() => setSimulatedLocation('Outside')}
                  className="flex-1 py-1 rounded bg-[#EF4444]/10 hover:bg-[#EF4444]/20 border border-[#EF4444]/25 text-[#EF4444] font-bold text-[10px]"
                >
                  Preset: Outside
                </button>
              </div>

              {/* Check-In Status Messages */}
              <AnimatePresence mode="wait">
                {checkInStatus === 'success' && (
                  <motion.div 
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 space-y-1"
                  >
                    <div className="flex items-center gap-2 font-bold">
                      <UserCheck className="w-4 h-4 animate-bounce" />
                      <span>Check-In Verified</span>
                    </div>
                    <p className="text-[10px] text-emerald-500/80">
                      Coordinates matched geofence profile successfully at {lastCheckTime}. Log written to biometric sync database.
                    </p>
                  </motion.div>
                )}
                {checkInStatus === 'out_of_bounds' && (
                  <motion.div 
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-[#EF4444] space-y-1"
                  >
                    <div className="flex items-center gap-2 font-bold">
                      <AlertTriangle className="w-4 h-4 animate-pulse" />
                      <span>Check-In Blocked</span>
                    </div>
                    <p className="text-[10px] text-red-500/80">
                      Out of Bounds Exception: Simulated GPS distance exceeds maximum allowed 150m radius from office HQ center.
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>

              <button 
                onClick={handleCheckIn}
                className="btn-primary w-full py-2 flex items-center justify-center gap-2"
              >
                <MapPin className="w-4 h-4" /> Trigger Check-In Scan
              </button>
            </div>
          </div>

        </div>

        {/* Right Column - Leaves Center & Payslip History */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Leaves Request Center */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Leave Request Center</h2>
              <span className="text-[10px] bg-purple-500/20 text-[#A855F7] border border-[#A855F7]/30 px-2 py-0.5 rounded font-bold">
                portal_leaves
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Form */}
              {leaveSuccess ? (
                <div className="h-[200px] flex flex-col items-center justify-center text-center space-y-3 text-xs text-emerald-400">
                  <CheckCircle2 className="w-10 h-10 animate-bounce" />
                  <div>
                    <p className="font-bold">Leave Request Logged</p>
                    <p className="text-[10px] text-slate-500 mt-1">Request successfully routed to your department supervisor for approval validation.</p>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleLeaveSubmit} className="space-y-3 text-xs">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Leave Category</label>
                    <select 
                      value={leaveType} 
                      onChange={e => setLeaveType(e.target.value)}
                      className="input-field"
                    >
                      <option value="Annual Leave">Annual Leave</option>
                      <option value="Sick Leave">Sick Leave</option>
                      <option value="Emergency Leave">Emergency Leave</option>
                      <option value="Unpaid Leave">Unpaid Leave</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-500 uppercase">Start Date</label>
                      <input 
                        type="date" 
                        required 
                        value={startDate}
                        onChange={e => setStartDate(e.target.value)}
                        className="input-field py-1"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-500 uppercase">End Date</label>
                      <input 
                        type="date" 
                        required 
                        value={endDate}
                        onChange={e => setEndDate(e.target.value)}
                        className="input-field py-1"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Reason description</label>
                    <input 
                      type="text" 
                      required 
                      placeholder="Specify reason detail..." 
                      value={leaveReason}
                      onChange={e => setLeaveReason(e.target.value)}
                      className="input-field"
                    />
                  </div>
                  <button type="submit" className="btn-primary w-full py-2">
                    Submit Leave Request
                  </button>
                </form>
              )}

              {/* Requests history */}
              <div className="space-y-2">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-white/5 pb-2">Request History</p>
                <div className="space-y-2 max-h-[180px] overflow-y-auto">
                  {leaves.map(lv => (
                    <div key={lv.id} className="p-3 rounded-xl bg-white/3 border border-white/5 flex items-center justify-between">
                      <div>
                        <p className="text-xs font-bold text-white">{lv.type}</p>
                        <p className="text-[10px] text-slate-400 mt-0.5">{lv.startDate} ➔ {lv.endDate}</p>
                        <p className="text-[9px] text-slate-500 italic mt-0.5 truncate max-w-[150px]">{lv.reason}</p>
                      </div>
                      <span className={`badge text-[9px] ${
                        lv.status === 'Approved' ? 'badge-green' :
                        lv.status === 'Rejected' ? 'badge-red' : 'badge-yellow'
                      }`}>{lv.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Personal Payslips Registry */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Personal Payslip Records</h2>
              <span className="text-[10px] bg-emerald-500/20 text-[#10B981] border border-[#10B981]/30 px-2 py-0.5 rounded font-bold">
                portal_employee_payslip
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Slip ID</th>
                    <th>Period</th>
                    <th>Base Wage</th>
                    <th>Net Deposited</th>
                    <th>Payment Date</th>
                    <th className="text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {payslips.map(ps => (
                    <tr key={ps.id}>
                      <td className="font-mono text-xs">{ps.id}</td>
                      <td className="font-bold text-slate-300">{ps.period}</td>
                      <td className="font-mono">JOD {ps.baseSalary}</td>
                      <td className="font-mono font-bold text-white">JOD {ps.netSalary}</td>
                      <td>{ps.datePaid}</td>
                      <td className="text-right">
                        <button className="p-1 px-2 text-[10px] font-bold rounded bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/25 text-[#10B981]">
                          Download PDF
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
