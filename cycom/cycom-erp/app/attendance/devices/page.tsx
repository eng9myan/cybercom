'use client';

import React from 'react';
import { Cpu, RefreshCw, Radio, MapPin, Plus } from 'lucide-react';
import { useCycomList, fmtCode, fmtDate } from '@/lib/cycomModels';
import { useT } from '@/lib/i18n';

type CycomZkMachine = {
  id: number;
  name?: string;
  ip?: string;
  state?: string;
  last_activity?: string;
};

type DeviceRow = {
  id: string;
  name: string;
  type: string;
  ip: string;
  port: string;
  status: 'Online' | 'Offline';
  lastSync: string;
  recordsCount: string;
};

const mapDevice = (r: CycomZkMachine): DeviceRow => ({
  id: fmtCode('DEV', r.id, 3),
  name: r.name || `Device ${r.id}`,
  type: 'ZK Teco',
  ip: r.ip || '—',
  port: '4370',
  status: r.state === 'online' ? 'Online' : 'Offline',
  lastSync: fmtDate(r.last_activity),
  recordsCount: '—',
});

export default function BiometricDevices() {
  const t = useT();
  const { rows: devices, loading, reload } = useCycomList<CycomZkMachine, DeviceRow>(
    'zk.machine', // TODO: verify model name
    [],
    ['name', 'ip', 'state', 'last_activity'],
    mapDevice,
    { limit: 100 },
  );

  const syncDevice = (_id: string) => {
    reload();
  };

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>{t('attendanceMain.loading')}</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('attendanceDevices.title')}</h1>
          <p className="page-subtitle">{t('attendanceDevices.subtitle')}</p>
        </div>
        <div className="flex gap-3">
          <button className="btn-secondary flex items-center gap-2">
            <Radio className="w-4 h-4 text-emerald-400" /> {t('attendanceDevices.pingAll')}
          </button>
          <button className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> {t('attendanceDevices.addDevice')}
          </button>
        </div>
      </div>

      {/* Geofence Configuration Section */}
      <div className="glass-card p-6 border-cyan-500/20 bg-cyan-950/10">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-xl border border-cyan-500/10">
            <MapPin className="w-6 h-6" />
          </div>
          <div className="space-y-2 flex-1">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-bold text-white">{t('attendanceDevices.geofenceConfigTitle')}</h3>
              <span className="badge badge-cyan">{t('attendanceDevices.enabled')}</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed max-w-3xl">
              {t('attendanceDevices.geofenceDesc')}
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs pt-2">
              <div>
                <span className="text-slate-500 block">{t('attendanceDevices.ammanCoords')}</span>
                <span className="text-slate-200 font-mono" dir="ltr">31.9522° N, 35.9106° E (100m radius)</span>
              </div>
              <div>
                <span className="text-slate-500 block">{t('attendanceDevices.zarqaCoords')}</span>
                <span className="text-slate-200 font-mono" dir="ltr">32.0608° N, 36.0942° E (150m radius)</span>
              </div>
              <div>
                <span className="text-slate-500 block">{t('attendanceDevices.irbidCoords')}</span>
                <span className="text-slate-200 font-mono" dir="ltr">32.5568° N, 35.8469° E (120m radius)</span>
              </div>
              <div>
                <span className="text-slate-500 block">{t('attendanceDevices.fingerprintLocks')}</span>
                <span className="text-[#10B981] font-semibold">{t('attendanceDevices.singleDeviceActive')}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Devices List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {devices.map((d) => (
          <div key={d.id} className="glass-card p-6 space-y-4">
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-lg border ${
                  d.status === 'Online'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                }`}>
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{d.name}</h3>
                  <p className="text-xs text-slate-400">{d.type}</p>
                </div>
              </div>
              <span className={`badge ${d.status === 'Online' ? 'badge-green' : 'badge-red'}`}>
                {d.status}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs bg-black/35 p-3 rounded-lg border border-white/5 font-mono">
              <div>
                <span className="text-slate-500 block">{t('attendanceDevices.ipAddress')}</span>
                <span className="text-slate-300" dir="ltr">{d.ip}:{d.port}</span>
              </div>
              <div>
                <span className="text-slate-500 block">{t('attendanceDevices.recordCount')}</span>
                <span className="text-slate-300">{d.recordsCount}</span>
              </div>
              <div>
                <span className="text-slate-500 block">{t('attendanceDevices.lastSynced')}</span>
                <span className="text-slate-300">{d.lastSync}</span>
              </div>
              <div>
                <span className="text-slate-500 block">{t('attendanceDevices.connectionProtocol')}</span>
                <span className="text-slate-300">TCP/IP SDK</span>
              </div>
            </div>

            {d.status === 'Online' && (
              <div className="flex gap-2 justify-end pt-2 border-t border-white/5">
                <button
                  onClick={() => syncDevice(d.id)}
                  className="btn-secondary py-1 px-3 text-xs flex items-center gap-1.5 hover:bg-cyan-500/10 hover:text-cyan-400 hover:border-cyan-500/30 transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" /> {t('attendanceDevices.pullRecords')}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
