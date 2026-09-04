'use client';

import React, { useState, useEffect } from 'react';
import { useCycomList, m2oName, fmtDate, type Many2One } from '@/lib/cycomModels';
import { Wrench, Trash2, Settings2, Activity, ShieldAlert } from 'lucide-react';
import { useT } from '@/lib/i18n';

type EqStatusKey = 'operational' | 'underRepair' | 'broken';
type CategoryKey = 'biometric' | 'pos' | 'forklift' | 'server';
type ReqStatusKey = 'new' | 'inProgress' | 'repaired';
type ReqTypeKey = 'preventive' | 'corrective';

interface Equipment {
  id: string;
  name: string;
  model: string;
  category: CategoryKey;
  tech: string;
  status: EqStatusKey;
}

interface MaintenanceRequest {
  id: string;
  title: string;
  equipId: string;
  equipName: string;
  type: ReqTypeKey;
  dateRequested: string;
  assignedTo: string;
  status: ReqStatusKey;
}

const INITIAL_EQUIPMENT: Equipment[] = [
  { id: 'EQ-01', name: 'Gate A Biometric ZK', model: 'ZK-Teco MultiBio 800', category: 'biometric', tech: 'Khaled Jaber', status: 'operational' },
  { id: 'EQ-02', name: 'Counter 1 Retail POS', model: 'HP Engage One Pro', category: 'pos', tech: 'Ahmad Masri', status: 'underRepair' },
  { id: 'EQ-03', name: 'Amman North Forklift', model: 'Toyota 8FGU25', category: 'forklift', tech: 'Rami Khasawneh', status: 'broken' },
  { id: 'EQ-04', name: 'HQ ERP Main Server', model: 'Dell PowerEdge R760', category: 'server', tech: 'Lina Qudah', status: 'operational' },
];

type CycomMaintenanceRequest = {
  id: number;
  name?: string;
  equipment_id?: Many2One;
  stage_id?: Many2One;
  priority?: string;
  create_date?: string;
};

const mapReqStatus = (stageName: string): ReqStatusKey => {
  const n = stageName.toLowerCase();
  if (n.includes('progress') || n.includes('repair')) return 'inProgress';
  if (n.includes('done') || n.includes('repaired') || n.includes('complete')) return 'repaired';
  return 'new';
};

const mapMaintenanceRequest = (r: CycomMaintenanceRequest): MaintenanceRequest => ({
  id: r.name || `MNT-${r.id}`,
  title: r.name || '—',
  equipId: r.equipment_id ? String(r.equipment_id[0]) : '—',
  equipName: m2oName(r.equipment_id, '—'),
  type: 'corrective',
  dateRequested: fmtDate(r.create_date),
  assignedTo: '—',
  status: mapReqStatus(m2oName(r.stage_id)),
});

const EQ_TONE: Record<EqStatusKey, string> = { operational: 'badge-green', underRepair: 'badge-cyan', broken: 'badge-red' };
const CAT_TONE: Record<CategoryKey, string> = { biometric: 'badge-blue', pos: 'badge-orange', forklift: 'badge-purple', server: 'badge-green' };
const REQ_TONE: Record<ReqStatusKey, string> = { repaired: 'badge-green', inProgress: 'badge-cyan', new: 'badge-yellow' };

export default function MaintenancePage() {
  const t = useT();
  const { rows: liveRequests, loading } = useCycomList<CycomMaintenanceRequest, MaintenanceRequest>(
    'maintenance.request', [], ['name', 'equipment_id', 'stage_id', 'priority', 'create_date'],
    mapMaintenanceRequest,
  );
  const [equipment, setEquipment] = useState<Equipment[]>(INITIAL_EQUIPMENT);
  const [requests, setRequests] = useState<MaintenanceRequest[]>([]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (!loading) setRequests(liveRequests); }, [loading]);

  const [reqTitle, setReqTitle] = useState('');
  const [selectedEquipId, setSelectedEquipId] = useState('EQ-02');
  const [reqType, setReqType] = useState<ReqTypeKey>('corrective');
  const [assignedTech, setAssignedTech] = useState('Khaled Jaber');

  const eqStatusLabel: Record<EqStatusKey, string> = {
    operational: t('maintenance.eqOperational'),
    underRepair: t('maintenance.eqUnderRepair'),
    broken: t('maintenance.eqBroken'),
  };
  const catLabel: Record<CategoryKey, string> = {
    biometric: 'Biometric Reader', pos: 'POS Register', forklift: 'Warehouse Forklift', server: 'Server',
  };
  const reqStatusLabel: Record<ReqStatusKey, string> = {
    new: t('maintenance.stNew'), inProgress: t('maintenance.stInProgress'), repaired: t('maintenance.stRepaired'),
  };
  const reqTypeLabel: Record<ReqTypeKey, string> = {
    preventive: t('maintenance.typePreventive'), corrective: t('maintenance.typeCorrective'),
  };

  const handleCreateRequest = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reqTitle) return;
    const targetEquip = equipment.find((eq) => eq.id === selectedEquipId)!;
    const newReq: MaintenanceRequest = {
      id: `MNT-${Math.floor(104 + Math.random() * 90)}`,
      title: reqTitle,
      equipId: selectedEquipId,
      equipName: targetEquip.name,
      type: reqType,
      dateRequested: new Date().toISOString().split('T')[0],
      assignedTo: assignedTech,
      status: 'new',
    };
    setRequests([newReq, ...requests]);
    if (reqType === 'corrective') {
      setEquipment(equipment.map((eq) => (eq.id === selectedEquipId ? { ...eq, status: 'broken' } : eq)));
    }
    setReqTitle('');
  };

  const handleStartRequest = (id: string, equipId: string) => {
    setRequests(requests.map((req) => (req.id === id ? { ...req, status: 'inProgress' } : req)));
    setEquipment(equipment.map((eq) => (eq.id === equipId ? { ...eq, status: 'underRepair' } : eq)));
  };

  const handleResolveRequest = (id: string, equipId: string) => {
    setRequests(requests.map((req) => (req.id === id ? { ...req, status: 'repaired' } : req)));
    setEquipment(equipment.map((eq) => (eq.id === equipId ? { ...eq, status: 'operational' } : eq)));
  };

  const handleDeleteRequest = (id: string) => setRequests(requests.filter((r) => r.id !== id));

  if (loading) return <div style={{ padding: '2rem', color: '#ccc' }}>{t('common.loading')}</div>;

  const operationalPct = Math.round((equipment.filter((e) => e.status === 'operational').length / equipment.length) * 100);

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('maintenance.title')}</h1>
          <p className="page-subtitle">{t('maintenance.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label={t('maintenance.totalAssets')} value={t('maintenance.itemsN', { n: equipment.length })} icon={<Settings2 className="w-5 h-5" />} tone="blue" />
        <Stat label={t('maintenance.operationalRatio')} value={`${operationalPct}%`} icon={<Activity className="w-5 h-5" />} tone="emerald" />
        <Stat label={t('maintenance.brokenAssets')} value={t('maintenance.assetsN', { n: equipment.filter((e) => e.status === 'broken').length })} icon={<ShieldAlert className="w-5 h-5" />} tone="red" />
        <Stat label={t('maintenance.activeRequests')} value={t('maintenance.requestsN', { n: requests.filter((r) => r.status !== 'repaired').length })} icon={<Wrench className="w-5 h-5" />} tone="amber" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card p-5 space-y-4 h-fit">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('maintenance.logBreakdown')}</h2>
            <Wrench className="w-4 h-4 text-[#E67E22]" />
          </div>
          <form onSubmit={handleCreateRequest} className="space-y-3 text-xs">
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase">{t('maintenance.selectTargetAsset')}</label>
              <select value={selectedEquipId} onChange={(e) => setSelectedEquipId(e.target.value)} className="input-field">
                {equipment.map((eq) => (
                  <option key={eq.id} value={eq.id}>{t('maintenance.assetStatus', { name: eq.name, status: eqStatusLabel[eq.status] })}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase">{t('maintenance.faultTitle')}</label>
              <input type="text" required placeholder={t('maintenance.faultPlaceholder')} value={reqTitle} onChange={(e) => setReqTitle(e.target.value)} className="input-field" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('maintenance.actionType')}</label>
                <select value={reqType} onChange={(e) => setReqType(e.target.value as ReqTypeKey)} className="input-field">
                  <option value="corrective">{t('maintenance.correctiveRepair')}</option>
                  <option value="preventive">{t('maintenance.preventiveAudit')}</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('maintenance.technician')}</label>
                <select value={assignedTech} onChange={(e) => setAssignedTech(e.target.value)} className="input-field">
                  <option value="Khaled Jaber">Khaled Jaber</option>
                  <option value="Ahmad Masri">Ahmad Masri</option>
                  <option value="Rami Khasawneh">Rami Khasawneh</option>
                  <option value="Lina Qudah">Lina Qudah</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn-primary w-full py-2">{t('maintenance.generateRequest')}</button>
          </form>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">{t('maintenance.activeTasks')}</h2>
            <div className="space-y-3">
              {requests.map((req) => (
                <div key={req.id} className="p-4 rounded-xl bg-white/3 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-black text-white">{req.id}</span>
                      <span className="text-[10px] text-slate-500">{req.dateRequested}</span>
                      <span className={`badge text-[9px] ${req.type === 'preventive' ? 'badge-blue' : 'badge-orange'}`}>{reqTypeLabel[req.type]}</span>
                      <span className={`badge text-[9px] ${REQ_TONE[req.status]}`}>{reqStatusLabel[req.status]}</span>
                    </div>
                    <p className="text-xs text-slate-200 font-bold">{req.title}</p>
                    <p className="text-[11px] text-slate-400">{t('maintenance.assetLine', { name: req.equipName, id: req.equipId, tech: req.assignedTo })}</p>
                  </div>
                  <div className="flex gap-1.5 flex-shrink-0">
                    {req.status === 'new' && (
                      <button onClick={() => handleStartRequest(req.id, req.equipId)} className="p-1 px-2 text-[10px] font-bold rounded bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/25 text-[#00F0FF]">
                        {t('maintenance.startWork')}
                      </button>
                    )}
                    {req.status === 'inProgress' && (
                      <button onClick={() => handleResolveRequest(req.id, req.equipId)} className="p-1 px-2 text-[10px] font-bold rounded bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/25 text-[#10B981] flex items-center gap-1">
                        {t('maintenance.completeRepair')}
                      </button>
                    )}
                    <button onClick={() => handleDeleteRequest(req.id)} className="p-1 rounded hover:bg-red-500/20 text-[#EF4444]">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">{t('maintenance.equipmentRegistry')}</h2>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('maintenance.assetId')}</th>
                    <th>{t('maintenance.equipmentName')}</th>
                    <th>{t('maintenance.modelSpec')}</th>
                    <th>{t('maintenance.category')}</th>
                    <th>{t('maintenance.technician')}</th>
                    <th>{t('common.status')}</th>
                  </tr>
                </thead>
                <tbody>
                  {equipment.map((eq) => (
                    <tr key={eq.id}>
                      <td className="font-mono text-xs">{eq.id}</td>
                      <td className="font-bold text-slate-300">{eq.name}</td>
                      <td className="text-xs text-slate-400">{eq.model}</td>
                      <td><span className={`badge text-[9px] ${CAT_TONE[eq.category]}`}>{catLabel[eq.category]}</span></td>
                      <td>{eq.tech}</td>
                      <td><span className={`badge text-[9px] ${EQ_TONE[eq.status]}`}>{eqStatusLabel[eq.status]}</span></td>
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

function Stat({ label, value, icon, tone }: { label: string; value: string; icon: React.ReactNode; tone: 'blue' | 'emerald' | 'red' | 'amber' }) {
  const colors = {
    blue: 'bg-blue-500/10 text-blue-400',
    emerald: 'bg-emerald-500/10 text-emerald-400',
    red: 'bg-red-500/10 text-red-400',
    amber: 'bg-amber-500/10 text-amber-400',
  }[tone];
  return (
    <div className="stat-card flex items-center justify-between">
      <div>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{label}</span>
        <p className="text-2xl font-black text-white">{value}</p>
      </div>
      <div className={`p-3 rounded-xl ${colors}`}>{icon}</div>
    </div>
  );
}
