'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCycomList, m2oName, fmtDate, type Many2One } from '@/lib/cycomModels';
import { 
  Wrench, Plus, Trash2, CheckCircle, Clock, 
  Settings2, Activity, ShieldAlert, AlertTriangle, ShieldCheck
} from 'lucide-react';

interface Equipment {
  id: string;
  name: string;
  model: string;
  category: 'Biometric Reader' | 'POS Register' | 'Warehouse Forklift' | 'Server';
  tech: string;
  status: 'Operational' | 'Under Repair' | 'Broken';
}

interface MaintenanceRequest {
  id: string;
  title: string;
  equipId: string;
  equipName: string;
  type: 'Preventive' | 'Corrective';
  dateRequested: string;
  assignedTo: string;
  status: 'New' | 'In Progress' | 'Repaired';
}

const INITIAL_EQUIPMENT: Equipment[] = [
  { id: 'EQ-01', name: 'Gate A Biometric ZK', model: 'ZK-Teco MultiBio 800', category: 'Biometric Reader', tech: 'Khaled Jaber', status: 'Operational' },
  { id: 'EQ-02', name: 'Counter 1 Retail POS', model: 'HP Engage One Pro', category: 'POS Register', tech: 'Ahmad Masri', status: 'Under Repair' },
  { id: 'EQ-03', name: 'Amman North Forklift', model: 'Toyota 8FGU25', category: 'Warehouse Forklift', tech: 'Rami Khasawneh', status: 'Broken' },
  { id: 'EQ-04', name: 'HQ ERP Main Server', model: 'Dell PowerEdge R760', category: 'Server', tech: 'Lina Qudah', status: 'Operational' },
];

type CycomMaintenanceRequest = {
  id: number;
  name?: string;
  equipment_id?: Many2One;
  stage_id?: Many2One;
  priority?: string;
  create_date?: string;
};

const mapMaintenanceStatus = (stageName: string): MaintenanceRequest['status'] => {
  const n = stageName.toLowerCase();
  if (n.includes('progress') || n.includes('repair')) return 'In Progress';
  if (n.includes('done') || n.includes('repaired') || n.includes('complete')) return 'Repaired';
  return 'New';
};

const mapMaintenanceRequest = (r: CycomMaintenanceRequest): MaintenanceRequest => ({
  id: r.name || `MNT-${r.id}`,
  title: r.name || '—',
  equipId: r.equipment_id ? String(r.equipment_id[0]) : '—',
  equipName: m2oName(r.equipment_id, '—'),
  type: 'Corrective',
  dateRequested: fmtDate(r.create_date),
  assignedTo: '—',
  status: mapMaintenanceStatus(m2oName(r.stage_id)),
});

export default function MaintenancePage() {
  const { rows: liveRequests, loading } = useCycomList<CycomMaintenanceRequest, MaintenanceRequest>(
    'maintenance.request', [], ['name', 'equipment_id', 'stage_id', 'priority', 'create_date'],
    mapMaintenanceRequest,
  );
  const [equipment, setEquipment] = useState<Equipment[]>(INITIAL_EQUIPMENT);
  const [requests, setRequests] = useState<MaintenanceRequest[]>([]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (!loading) setRequests(liveRequests); }, [loading]);

  // New Request Form states
  const [reqTitle, setReqTitle] = useState('');
  const [selectedEquipId, setSelectedEquipId] = useState('EQ-02');
  const [reqType, setReqType] = useState<'Preventive' | 'Corrective'>('Corrective');
  const [assignedTech, setAssignedTech] = useState('Khaled Jaber');

  const handleCreateRequest = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reqTitle) return;

    const targetEquip = equipment.find(eq => eq.id === selectedEquipId)!;

    const newReq: MaintenanceRequest = {
      id: `MNT-${Math.floor(104 + Math.random() * 90)}`,
      title: reqTitle,
      equipId: selectedEquipId,
      equipName: targetEquip.name,
      type: reqType,
      dateRequested: new Date().toISOString().split('T')[0],
      assignedTo: assignedTech,
      status: 'New'
    };

    setRequests([newReq, ...requests]);

    // Update equipment status if corrective
    if (reqType === 'Corrective') {
      setEquipment(equipment.map(eq => eq.id === selectedEquipId ? { ...eq, status: 'Broken' } : eq));
    }

    setReqTitle('');
  };

  const handleStartRequest = (id: string, equipId: string) => {
    setRequests(requests.map(req => req.id === id ? { ...req, status: 'In Progress' } : req));
    setEquipment(equipment.map(eq => eq.id === equipId ? { ...eq, status: 'Under Repair' } : eq));
  };

  const handleResolveRequest = (id: string, equipId: string) => {
    setRequests(requests.map(req => req.id === id ? { ...req, status: 'Repaired' } : req));
    setEquipment(equipment.map(eq => eq.id === equipId ? { ...eq, status: 'Operational' } : eq));
  };

  const handleDeleteRequest = (id: string) => {
    setRequests(requests.filter(r => r.id !== id));
  };

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Maintenance & Equipment</h1>
          <p className="page-subtitle">Standard Cycom Maintenance workflows. Log hardware breakdowns, schedule audits, and assign technicians.</p>
        </div>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Assets</span>
            <p className="text-2xl font-black text-white">{equipment.length} items</p>
          </div>
          <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400">
            <Settings2 className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Operational Ratio</span>
            <p className="text-2xl font-black text-[#10B981]">
              {Math.round((equipment.filter(e => e.status === 'Operational').length / equipment.length) * 100)}%
            </p>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
            <Activity className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Broken Assets</span>
            <p className="text-2xl font-black text-[#EF4444]">
              {equipment.filter(e => e.status === 'Broken').length} assets
            </p>
          </div>
          <div className="p-3 rounded-xl bg-red-500/10 text-red-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Requests</span>
            <p className="text-2xl font-black text-[#F59E0B]">
              {requests.filter(r => r.status !== 'Repaired').length} requests
            </p>
          </div>
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400">
            <Wrench className="w-5 h-5" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column - Breakdown Form */}
        <div className="glass-card p-5 space-y-4 h-fit">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Log Breakdown Request</h2>
            <Wrench className="w-4 h-4 text-[#E67E22]" />
          </div>

          <form onSubmit={handleCreateRequest} className="space-y-3 text-xs">
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Select Target Asset</label>
              <select 
                value={selectedEquipId} 
                onChange={e => setSelectedEquipId(e.target.value)}
                className="input-field"
              >
                {equipment.map(eq => (
                  <option key={eq.id} value={eq.id}>{eq.name} (Status: {eq.status})</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Fault Title / Issue</label>
              <input 
                type="text" 
                required 
                placeholder="e.g. Engine overheating" 
                value={reqTitle}
                onChange={e => setReqTitle(e.target.value)}
                className="input-field"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Action Type</label>
                <select 
                  value={reqType} 
                  onChange={e => setReqType(e.target.value as any)}
                  className="input-field"
                >
                  <option value="Corrective">Corrective Repair</option>
                  <option value="Preventive">Preventive Audit</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Technician</label>
                <select 
                  value={assignedTech} 
                  onChange={e => setAssignedTech(e.target.value)}
                  className="input-field"
                >
                  <option value="Khaled Jaber">Khaled Jaber</option>
                  <option value="Ahmad Masri">Ahmad Masri</option>
                  <option value="Rami Khasawneh">Rami Khasawneh</option>
                  <option value="Lina Qudah">Lina Qudah</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn-primary w-full py-2">
              Generate Maintenance Request
            </button>
          </form>
        </div>

        {/* Right Column - Assets List & Active Requests */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Active Maintenance Requests Queue */}
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">Active Maintenance Tasks</h2>
            
            <div className="space-y-3">
              {requests.map(req => (
                <div key={req.id} className="p-4 rounded-xl bg-white/3 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-black text-white">{req.id}</span>
                      <span className="text-[10px] text-slate-500">{req.dateRequested}</span>
                      <span className={`badge text-[9px] ${
                        req.type === 'Preventive' ? 'badge-blue' : 'badge-orange'
                      }`}>{req.type}</span>
                      <span className={`badge text-[9px] ${
                        req.status === 'Repaired' ? 'badge-green' :
                        req.status === 'In Progress' ? 'badge-cyan' : 'badge-yellow'
                      }`}>{req.status}</span>
                    </div>
                    <p className="text-xs text-slate-200 font-bold">{req.title}</p>
                    <p className="text-[11px] text-slate-400">Asset: <strong>{req.equipName}</strong> ({req.equipId}) · Assigned Tech: {req.assignedTo}</p>
                  </div>
                  
                  <div className="flex gap-1.5 flex-shrink-0">
                    {req.status === 'New' && (
                      <button 
                        onClick={() => handleStartRequest(req.id, req.equipId)}
                        className="p-1 px-2 text-[10px] font-bold rounded bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/25 text-[#00F0FF]"
                      >
                        Start Work
                      </button>
                    )}
                    {req.status === 'In Progress' && (
                      <button 
                        onClick={() => handleResolveRequest(req.id, req.equipId)}
                        className="p-1 px-2 text-[10px] font-bold rounded bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/25 text-[#10B981] flex items-center gap-1"
                      >
                        Complete Repair
                      </button>
                    )}
                    <button 
                      onClick={() => handleDeleteRequest(req.id)}
                      className="p-1 rounded hover:bg-red-500/20 text-[#EF4444]"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Equipment Registry */}
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">Corporate Equipment Asset Registry</h2>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Asset ID</th>
                    <th>Equipment Name</th>
                    <th>Model Spec</th>
                    <th>Category</th>
                    <th>Technician</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {equipment.map(eq => (
                    <tr key={eq.id}>
                      <td className="font-mono text-xs">{eq.id}</td>
                      <td className="font-bold text-slate-300">{eq.name}</td>
                      <td className="text-xs text-slate-400">{eq.model}</td>
                      <td>
                        <span className={`badge text-[9px] ${
                          eq.category === 'Biometric Reader' ? 'badge-blue' :
                          eq.category === 'POS Register' ? 'badge-orange' :
                          eq.category === 'Warehouse Forklift' ? 'badge-purple' : 'badge-green'
                        }`}>{eq.category}</span>
                      </td>
                      <td>{eq.tech}</td>
                      <td>
                        <span className={`badge text-[9px] ${
                          eq.status === 'Operational' ? 'badge-green' :
                          eq.status === 'Under Repair' ? 'badge-cyan' : 'badge-red'
                        }`}>{eq.status}</span>
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
