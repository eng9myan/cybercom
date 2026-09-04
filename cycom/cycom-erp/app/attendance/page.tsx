'use client';

import React, { useState } from 'react';
import { useCycomList, fmtCode, fmtDate, m2oName, m2oId, type Many2One } from '@/lib/cycomModels';
import {
  RefreshCw, CheckCircle
} from 'lucide-react';
import { useT } from '@/lib/i18n';

interface ZkDevice {
  id: string;
  name: string;
  ipAddress: string;
  port: number;
  location: string;
  status: 'Online' | 'Offline';
  lastSynced: string;
}

interface BiometricLog {
  id: string;
  employeeName: string;
  employeeId: string;
  device: string;
  timestamp: string;
  type: 'Check-In' | 'Check-Out';
  method: 'Face ID' | 'Fingerprint' | 'RFID Card';
}

type CycomZkMachine = {
  id: number;
  name?: string;
  ip?: string;
  state?: string;
  last_activity?: string;
};

type CycomAttendanceLog = {
  id: number;
  employee_id: Many2One;
  check_in?: string;
  check_out?: string;
  worked_hours?: number;
};

const mapDevice = (r: CycomZkMachine): ZkDevice => ({
  id: fmtCode('DEV', r.id),
  name: r.name || `Device ${r.id}`,
  ipAddress: r.ip || '—',
  port: 4370,
  location: r.name || '—',
  status: r.state === 'online' ? 'Online' : 'Offline',
  lastSynced: fmtDate(r.last_activity),
});

const mapAttendanceLog = (r: CycomAttendanceLog): BiometricLog => ({
  id: fmtCode('LOG', r.id, 3),
  employeeName: m2oName(r.employee_id),
  employeeId: fmtCode('EMP', m2oId(r.employee_id) ?? 0),
  device: '—',
  timestamp: r.check_in
    ? new Date(r.check_in.replace(' ', 'T') + 'Z').toLocaleTimeString()
    : '—',
  type: 'Check-In',
  method: 'Fingerprint',
});

export default function AttendanceDashboard() {
  const t = useT();
  const { rows: devices, loading: devicesLoading, reload: reloadDevices } = useCycomList<CycomZkMachine, ZkDevice>(
    'zk.machine', // TODO: verify model name
    [],
    ['name', 'ip', 'state', 'last_activity'],
    mapDevice,
    { limit: 100 },
  );
  const { rows: logs, loading: logsLoading, reload: reloadLogs } = useCycomList<CycomAttendanceLog, BiometricLog>(
    'hr.attendance',
    [],
    ['employee_id', 'check_in', 'check_out', 'worked_hours'],
    mapAttendanceLog,
    { limit: 50, order: 'check_in desc' },
  );
  const loading = devicesLoading || logsLoading;
  const [isSyncing, setIsSyncing] = useState(false);

  // New device form states
  const [devName, setDevName] = useState('');
  const [devIp, setDevIp] = useState('');
  const [devPort, setDevPort] = useState(4370);
  const [devLoc, setDevLoc] = useState('');

  // Weekly Overtime Eligibility states
  const [weeklyEmp, setWeeklyEmp] = useState('Ahmad Masri');
  const [weeklyContractHours, setWeeklyContractHours] = useState(48);
  const [weeklyActualHours, setWeeklyActualHours] = useState(54);

  // Geofence states
  const [geofenceLat, setGeofenceLat] = useState(31.9522); // Amman coords
  const [geofenceLng, setGeofenceLng] = useState(35.9250);
  const [geofenceRadius, setGeofenceRadius] = useState(150); // meters

  // Missed Punch Correction Form
  const [corrEmp, setCorrEmp] = useState('Ahmad Masri');
  const [corrDate, setCorrDate] = useState('');
  const [corrType, setCorrType] = useState<'Check-In' | 'Check-Out'>('Check-In');
  const [corrReason, setCorrReason] = useState('');
  const [corrSuccess, setCorrSuccess] = useState(false);

  // Syncing — triggers a live reload from Backend
  const triggerSync = () => {
    setIsSyncing(true);
    setTimeout(() => {
      setIsSyncing(false);
      reloadLogs();
      reloadDevices();
    }, 1200);
  };

  const handleAddDevice = (e: React.FormEvent) => {
    e.preventDefault();
    if (!devName || !devIp) return;
    // TODO: call Backend create API to register device, then reload
    setDevName('');
    setDevIp('');
    setDevLoc('');
  };

  const handleCorrectionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!corrDate || !corrReason) return;
    setCorrSuccess(true);
    setTimeout(() => {
      setCorrSuccess(false);
      setCorrDate('');
      setCorrReason('');
    }, 3000);
  };

  // Weekly OT Calculator logic
  const extraHours = weeklyActualHours - weeklyContractHours;
  const isEligible = extraHours > 0;

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>{t('attendanceMain.loading')}</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('attendanceMain.title')}</h1>
          <p className="page-subtitle">{t('attendanceMain.subtitle')}</p>
        </div>
        <button
          onClick={triggerSync}
          disabled={isSyncing}
          className="btn-primary flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
          {isSyncing ? t('attendanceMain.syncing') : t('attendanceMain.syncDevices')}
        </button>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column - Device Terminal & Add form */}
        <div className="space-y-6">

          {/* Devices List */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('attendanceMain.terminalsHeading')}</h2>
              <span className="text-[10px] bg-emerald-500/20 text-[#10B981] border border-emerald-500/30 px-2 py-0.5 rounded font-bold">
                hs_zk_attendance
              </span>
            </div>

            <div className="space-y-3">
              {devices.map(dev => (
                <div key={dev.id} className="p-3.5 rounded-xl bg-white/3 border border-white/5 flex items-center justify-between hover:border-white/10 transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">{dev.name}</span>
                      <span className="text-[9px] text-slate-500 font-mono">{dev.id}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">{dev.location}</p>
                    <p className="text-[9px] text-slate-500 font-mono" dir="ltr">{dev.ipAddress}:{dev.port}</p>
                  </div>
                  <div className="text-end space-y-1">
                    <span className={`badge text-[9px] ${dev.status === 'Online' ? 'badge-green' : 'badge-red'}`}>
                      {dev.status}
                    </span>
                    <p className="text-[9px] text-slate-500 font-bold">{t('attendanceMain.syncLabel', { date: dev.lastSynced })}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Add Device Form */}
          <div className="glass-card p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-2">{t('attendanceMain.registerDevice')}</h3>
            <form onSubmit={handleAddDevice} className="space-y-3">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('attendanceMain.deviceName')}</label>
                <input
                  type="text"
                  required
                  placeholder={t('attendanceMain.deviceNamePh')}
                  value={devName}
                  onChange={e => setDevName(e.target.value)}
                  className="input-field py-1"
                />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-2 space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('attendanceMain.ipAddress')}</label>
                  <input
                    type="text"
                    required
                    placeholder="192.168.10.X"
                    value={devIp}
                    onChange={e => setDevIp(e.target.value)}
                    className="input-field py-1 font-mono"
                    dir="ltr"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('attendanceMain.port')}</label>
                  <input
                    type="number"
                    required
                    value={devPort}
                    onChange={e => setDevPort(parseInt(e.target.value) || 4370)}
                    className="input-field py-1 font-mono"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('attendanceMain.physicalLocation')}</label>
                <input
                  type="text"
                  placeholder={t('attendanceMain.physicalLocationPh')}
                  value={devLoc}
                  onChange={e => setDevLoc(e.target.value)}
                  className="input-field py-1"
                />
              </div>
              <button type="submit" className="btn-primary w-full py-1.5 mt-2">
                {t('attendanceMain.addDeviceBtn')}
              </button>
            </form>
          </div>

        </div>

        {/* Middle Column - Live Logs and Weekly OT Checker */}
        <div className="space-y-6 lg:col-span-2">

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

            {/* Live Logs Viewer */}
            <div className="glass-card p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('attendanceMain.liveLogsHeading')}</h2>
                <div className="flex items-center gap-1.5 text-[#10B981]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-ping" />
                  <span className="text-[10px] font-bold">{t('attendanceMain.realtimeStream')}</span>
                </div>
              </div>

              <div className="space-y-2 max-h-[320px] overflow-y-auto">
                {logs.map(log => (
                  <div key={log.id} className="p-3 rounded-xl bg-white/3 border border-white/5 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-bold text-white">{log.employeeName} ({log.employeeId})</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{log.device} · <span className="font-semibold text-slate-500">{log.method}</span></p>
                    </div>
                    <div className="text-end">
                      <span className={`badge text-[9px] ${log.type === 'Check-In' ? 'badge-green' : 'badge-orange'}`}>
                        {log.type === 'Check-In' ? t('attendanceMain.checkIn') : t('attendanceMain.checkOut')}
                      </span>
                      <p className="text-[9px] text-slate-500 font-mono mt-1">{log.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Weekly Overtime Eligibility Checker */}
            <div className="glass-card p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('attendanceMain.weeklyOtHeading')}</h2>
                <span className="text-[10px] bg-orange-500/20 text-[#E67E22] border border-orange-500/30 px-2 py-0.5 rounded font-bold">
                  hr_attendance_weekly_overtime_eligibility
                </span>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">{t('attendanceMain.employeeProfile')}</span>
                    <select
                      value={weeklyEmp}
                      onChange={e => setWeeklyEmp(e.target.value)}
                      className="bg-transparent border-none outline-none font-bold text-white text-end"
                    >
                      <option value="Ahmad Masri">Ahmad Masri</option>
                      <option value="Sara Haddad">Sara Haddad</option>
                      <option value="Rami Khasawneh">Rami Khasawneh</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-slate-400 font-semibold">
                      <span>{t('attendanceMain.contractHoursWeek')}</span>
                      <span>{t('attendanceMain.hrsN', { n: weeklyContractHours })}</span>
                    </div>
                    <input
                      type="range"
                      min="35"
                      max="60"
                      value={weeklyContractHours}
                      onChange={e => setWeeklyContractHours(parseInt(e.target.value))}
                      className="w-full accent-[#E67E22] bg-white/5 rounded-lg appearance-none h-1"
                    />
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-slate-400 font-semibold">
                      <span>{t('attendanceMain.actualLoggedHours')}</span>
                      <span>{t('attendanceMain.hrsN', { n: weeklyActualHours })}</span>
                    </div>
                    <input
                      type="range"
                      min="30"
                      max="70"
                      value={weeklyActualHours}
                      onChange={e => setWeeklyActualHours(parseInt(e.target.value))}
                      className="w-full accent-[#5DADE2] bg-white/5 rounded-lg appearance-none h-1"
                    />
                  </div>
                </div>

                <div className={`p-4 rounded-xl border ${
                  isEligible
                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                    : 'bg-white/3 border-white/5 text-slate-400'
                } space-y-2 text-xs`}>
                  <div className="flex justify-between">
                    <span>{t('attendanceMain.otStatus')}</span>
                    <span className="font-bold">{isEligible ? t('attendanceMain.eligible') : t('attendanceMain.ineligible')}</span>
                  </div>
                  <div className="flex justify-between border-t border-white/5 pt-1 mt-1">
                    <span>{t('attendanceMain.calculatedExtra')}</span>
                    <span className="font-mono font-bold">{t('attendanceMain.extraHoursVal', { sign: isEligible ? '+' : '', n: isEligible ? extraHours : 0 })}</span>
                  </div>
                  {isEligible && (
                    <p className="text-[10px] text-emerald-500/80 leading-snug mt-2">
                      {t('attendanceMain.ruleMatchNote')}
                    </p>
                  )}
                </div>
              </div>
            </div>

          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

            {/* Geofence Zone Configurator */}
            <div className="glass-card p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('attendanceMain.geofenceHeading')}</h2>
                <span className="text-[10px] bg-blue-500/20 text-[#5DADE2] border border-blue-500/30 px-2 py-0.5 rounded font-bold">
                  hr_attendance_geofence_config
                </span>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="text-[9px] text-slate-500 uppercase font-bold">{t('attendanceMain.latCenter')}</label>
                    <input
                      type="number"
                      step="0.0001"
                      value={geofenceLat}
                      onChange={e => setGeofenceLat(parseFloat(e.target.value) || 0)}
                      className="input-field py-1"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] text-slate-500 uppercase font-bold">{t('attendanceMain.lngCenter')}</label>
                    <input
                      type="number"
                      step="0.0001"
                      value={geofenceLng}
                      onChange={e => setGeofenceLng(parseFloat(e.target.value) || 0)}
                      className="input-field py-1"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>{t('attendanceMain.geofenceRadiusLabel')}</span>
                    <span className="font-bold text-[#E67E22]">{t('attendanceMain.metersN', { n: geofenceRadius })}</span>
                  </div>
                  <input
                    type="range"
                    min="20"
                    max="500"
                    step="10"
                    value={geofenceRadius}
                    onChange={e => setGeofenceRadius(parseInt(e.target.value))}
                    className="w-full accent-[#E67E22] bg-white/5 rounded-lg appearance-none h-1"
                  />
                </div>

                {/* SVG Visual map indicator */}
                <div className="h-[120px] rounded-xl bg-black/40 border border-white/5 flex items-center justify-center relative overflow-hidden">
                  <div className="absolute inset-0 bg-mesh opacity-20" />
                  {/* SVG Grid */}
                  <svg className="w-full h-full text-slate-600" viewBox="0 0 200 120">
                    <defs>
                      <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                        <path d="M 20 0 L 0 0 0 20" fill="none" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.1" />
                      </pattern>
                    </defs>
                    <rect width="100%" height="100%" fill="url(#grid)" />
                    {/* Geofence circular radius */}
                    <circle cx="100" cy="60" r={geofenceRadius / 4} fill="rgba(230, 126, 34, 0.08)" stroke="#E67E22" strokeWidth="1.5" strokeDasharray="3 3" />
                    {/* HQ Pin */}
                    <circle cx="100" cy="60" r="4" fill="#5DADE2" />
                    <text x="108" y="63" className="text-[8px] font-bold fill-slate-400 uppercase tracking-widest">{t('attendanceMain.officeHq')}</text>
                  </svg>
                  <span className="absolute bottom-2 start-2 text-[8px] text-slate-500 font-mono">{t('attendanceMain.zoomNote')}</span>
                </div>
              </div>
            </div>

            {/* Attendance correction request form */}
            <div className="glass-card p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('attendanceMain.correctionHeading')}</h2>
                <span className="text-[10px] bg-red-500/20 text-[#EF4444] border border-red-500/30 px-2 py-0.5 rounded font-bold">
                  hr_attendance_schedule_normalization
                </span>
              </div>

              {corrSuccess ? (
                <div className="h-[180px] flex flex-col items-center justify-center text-center space-y-3 text-xs text-emerald-400">
                  <CheckCircle className="w-10 h-10 animate-bounce" />
                  <div>
                    <p className="font-bold">{t('attendanceMain.correctionSubmitted')}</p>
                    <p className="text-[10px] text-slate-500 mt-1">{t('attendanceMain.correctionSubmittedNote')}</p>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleCorrectionSubmit} className="space-y-2 text-xs">
                  <div className="space-y-1">
                    <label className="text-[9px] text-slate-500 uppercase font-bold">{t('attendanceMain.employee')}</label>
                    <select
                      value={corrEmp}
                      onChange={e => setCorrEmp(e.target.value)}
                      className="input-field py-1"
                    >
                      <option value="Ahmad Masri">Ahmad Masri (EMP-029)</option>
                      <option value="Sara Haddad">Sara Haddad (EMP-034)</option>
                      <option value="Rami Khasawneh">Rami Khasawneh (EMP-088)</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <label className="text-[9px] text-slate-500 uppercase font-bold">{t('attendanceMain.targetDate')}</label>
                      <input
                        type="date"
                        required
                        value={corrDate}
                        onChange={e => setCorrDate(e.target.value)}
                        className="input-field py-1"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[9px] text-slate-500 uppercase font-bold">{t('attendanceMain.punchType')}</label>
                      <select
                        value={corrType}
                        onChange={e => setCorrType(e.target.value as any)}
                        className="input-field py-1"
                      >
                        <option value="Check-In">{t('attendanceMain.checkIn')}</option>
                        <option value="Check-Out">{t('attendanceMain.checkOut')}</option>
                      </select>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[9px] text-slate-500 uppercase font-bold">{t('attendanceMain.correctionReason')}</label>
                    <input
                      type="text"
                      required
                      placeholder={t('attendanceMain.correctionReasonPh')}
                      value={corrReason}
                      onChange={e => setCorrReason(e.target.value)}
                      className="input-field py-1"
                    />
                  </div>
                  <button type="submit" className="btn-primary w-full py-1.5 mt-2">
                    {t('attendanceMain.submitCorrection')}
                  </button>
                </form>
              )}
            </div>

          </div>

        </div>

      </div>

    </div>
  );
}
