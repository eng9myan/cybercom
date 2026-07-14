'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft, Fuel, Wrench, Calendar, Plus, Clock, 
  MapPin, DollarSign, X, CheckCircle2, ShieldAlert
} from 'lucide-react';
import { call } from '@/lib/cycom';
import { LoadingCard } from '@/components/CycomEmptyStates';

interface VehicleDetails {
  id: number;
  name: string;
  license_plate: string;
  make?: string;
  model?: string;
  year?: number;
  fuel_type: string;
  odometer_km: number;
  state: string;
  driver_id?: number;
  insurance_expiry?: string;
  license_expiry?: string;
}

interface MaintenanceLog {
  id: number;
  maintenance_date: string;
  maintenance_type: string;
  cost: number;
  service_provider: string;
  odometer_km: number;
  next_service_km?: number;
  notes?: string;
}

interface FuelLog {
  id: number;
  log_date: string;
  liters: number;
  price_per_liter: number;
  total_cost: number;
  fuel_station: string;
  odometer_km: number;
}

export default function VehicleLogsDetail() {
  const router = useRouter();
  const params = useParams();
  const idStr = params?.id as string;
  const vehicleId = parseInt(idStr);

  const [vehicle, setVehicle] = useState<VehicleDetails | null>(null);
  const [maintenance, setMaintenance] = useState<MaintenanceLog[]>([]);
  const [fuel, setFuel] = useState<FuelLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'maintenance' | 'fuel'>('maintenance');

  // Modals state
  const [showMaintModal, setShowMaintModal] = useState(false);
  const [showFuelModal, setShowFuelModal] = useState(false);
  const [saving, setSaving] = useState(false);

  // Maint form fields
  const [maintDate, setMaintDate] = useState(new Date().toISOString().split('T')[0]);
  const [maintType, setMaintType] = useState('preventative');
  const [maintCost, setMaintCost] = useState('');
  const [maintProvider, setMaintProvider] = useState('');
  const [maintOdo, setMaintOdo] = useState('');
  const [maintNextOdo, setMaintNextOdo] = useState('');
  const [maintNotes, setMaintNotes] = useState('');

  // Fuel form fields
  const [fuelDate, setFuelDate] = useState(new Date().toISOString().split('T')[0]);
  const [fuelLiters, setFuelLiters] = useState('');
  const [fuelPrice, setFuelPrice] = useState('');
  const [fuelStation, setFuelStation] = useState('');
  const [fuelOdo, setFuelOdo] = useState('');

  const fetchLogs = async () => {
    if (!vehicleId) return;
    try {
      const vData = await call<any>({
        model: 'fleet.vehicle',
        method: 'read',
        args: [vehicleId]
      });

      const mLogs = await call<any[]>({
        model: 'cy.fleet.maintenance',
        method: 'search_read',
        args: [[['vehicle_id', '=', vehicleId]]]
      });

      const fLogs = await call<any[]>({
        model: 'cy.fleet.fuel',
        method: 'search_read',
        args: [[['vehicle_id', '=', vehicleId]]]
      });

      if (vData) {
        setVehicle({
          ...vData,
          odometer_km: Number(vData.odometer_km ?? vData.odometer ?? 0)
        });
        setMaintenance(mLogs || []);
        setFuel(fLogs || []);
      }
    } catch (err: any) {
      alert('Error fetching logs: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [vehicleId]);

  // Submit Maintenance Log
  const handleSaveMaintenance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vehicle) return;
    const odoVal = parseFloat(maintOdo);
    
    if (odoVal < vehicle.odometer_km) {
      alert(`Invalid mileage: Odometer entry (${odoVal} km) cannot be lower than the vehicle's current odometer (${vehicle.odometer_km} km).`);
      return;
    }

    setSaving(true);
    try {
      await call({
        model: 'cy.fleet.maintenance',
        method: 'create',
        args: [{
          vehicle_id: vehicleId,
          maintenance_date: maintDate,
          maintenance_type: maintType,
          cost: parseFloat(maintCost),
          service_provider: maintProvider || null,
          odometer_km: odoVal,
          next_service_km: maintNextOdo ? parseFloat(maintNextOdo) : null,
          notes: maintNotes || null,
          tenant_id: 1,
          company_id: 1
        }]
      });

      // Update vehicle odometer
      await call({
        model: 'fleet.vehicle',
        method: 'write',
        args: [vehicleId, { odometer_km: odoVal, odometer: odoVal }]
      });

      alert('Maintenance log recorded successfully!');
      setShowMaintModal(false);
      fetchLogs();
    } catch (err: any) {
      alert('Error: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  // Submit Fuel Log
  const handleSaveFuel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vehicle) return;
    const odoVal = parseFloat(fuelOdo);
    
    if (odoVal < vehicle.odometer_km) {
      alert(`Invalid mileage: Odometer entry (${odoVal} km) cannot be lower than the vehicle's current odometer (${vehicle.odometer_km} km).`);
      return;
    }

    setSaving(true);
    const costVal = parseFloat(fuelLiters) * parseFloat(fuelPrice);
    try {
      await call({
        model: 'cy.fleet.fuel',
        method: 'create',
        args: [{
          vehicle_id: vehicleId,
          log_date: fuelDate,
          liters: parseFloat(fuelLiters),
          price_per_liter: parseFloat(fuelPrice),
          total_cost: costVal,
          fuel_station: fuelStation || null,
          odometer_km: odoVal,
          tenant_id: 1,
          company_id: 1
        }]
      });

      // Update vehicle odometer
      await call({
        model: 'fleet.vehicle',
        method: 'write',
        args: [vehicleId, { odometer_km: odoVal, odometer: odoVal }]
      });

      alert('Fuel log recorded successfully!');
      setShowFuelModal(false);
      fetchLogs();
    } catch (err: any) {
      alert('Error: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8"><LoadingCard label="Loading vehicle logs…" /></div>;
  if (!vehicle) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-center text-slate-400">Vehicle not found.</div>;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      {/* Header */}
      <div className="max-w-5xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push('/fleet')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
              {vehicle.make} {vehicle.model}
              <span className="text-sm font-normal text-slate-500 font-mono">({vehicle.license_plate})</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">Current Mileage: <span className="text-cyan-400 font-bold font-mono">{vehicle.odometer_km.toLocaleString()} km</span></p>
          </div>
        </div>

        <div className="flex gap-2">
          <button 
            onClick={() => setShowFuelModal(true)}
            className="btn-secondary flex items-center gap-1.5"
          >
            <Fuel className="w-4 h-4 text-emerald-400" /> Log Fuel Log
          </button>
          <button 
            onClick={() => setShowMaintModal(true)}
            className="btn-primary flex items-center gap-1.5"
          >
            <Wrench className="w-4 h-4" /> Log Maintenance
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="lg:col-span-1 glass-card p-6 space-y-4 h-fit">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5 pb-2">Vehicle Specifications</h3>
          <div className="space-y-3">
            <div>
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Manufacturer / Brand</span>
              <div className="text-slate-200 font-medium mt-0.5">{vehicle.make || '—'}</div>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Model Year</span>
              <div className="text-slate-200 font-medium mt-0.5">{vehicle.year || '—'}</div>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Fuel Type</span>
              <div className="text-slate-200 capitalize mt-0.5">{vehicle.fuel_type}</div>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Odometer reading</span>
              <div className="text-slate-200 font-mono mt-0.5">{vehicle.odometer_km.toLocaleString()} km</div>
            </div>
          </div>
        </div>

        {/* Logs Log Panel */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex gap-2 border-b border-white/5 pb-3">
            {[
              { id: 'maintenance', label: 'Maintenance History', icon: <Wrench className="w-4 h-4" /> },
              { id: 'fuel', label: 'Fuel Logs', icon: <Fuel className="w-4 h-4" /> }
            ].map(t => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id as any)}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 font-semibold transition ${
                  activeTab === t.id 
                    ? 'bg-slate-900 border border-slate-800 text-cyan-400 shadow-inner' 
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {t.icon} {t.label}
              </button>
            ))}
          </div>

          {activeTab === 'maintenance' && (
            <div className="glass-card p-6">
              {maintenance.length === 0 ? (
                <div className="text-center py-8 text-slate-500">No maintenance events recorded for this vehicle.</div>
              ) : (
                <div className="space-y-4">
                  {maintenance.map((m) => (
                    <div key={m.id} className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl flex justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                            m.maintenance_type === 'preventative' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                          }`}>{m.maintenance_type}</span>
                          <span className="font-semibold text-slate-200">{m.service_provider || 'External Service'}</span>
                        </div>
                        <div className="text-[10px] text-slate-500">Odometer: {m.odometer_km.toLocaleString()} km • Date: {m.maintenance_date}</div>
                        {m.notes && <p className="text-slate-400 text-xs mt-1 italic">"{m.notes}"</p>}
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-white">{m.cost.toLocaleString()} JOD</div>
                        {m.next_service_km && <div className="text-[10px] text-slate-500 mt-1">Next Service: {m.next_service_km.toLocaleString()} km</div>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'fuel' && (
            <div className="glass-card p-6">
              {fuel.length === 0 ? (
                <div className="text-center py-8 text-slate-500">No fuel fill logs found for this vehicle.</div>
              ) : (
                <div className="space-y-4">
                  {fuel.map((f) => (
                    <div key={f.id} className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl flex justify-between gap-4">
                      <div className="space-y-1">
                        <div className="font-semibold text-slate-200">{f.fuel_station || 'Gas Station'}</div>
                        <div className="text-[10px] text-slate-500">Odometer: {f.odometer_km.toLocaleString()} km • Date: {f.log_date}</div>
                        <div className="text-[10px] text-slate-400 mt-1">{f.liters} Liters @ {f.price_per_liter} JOD/L</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-emerald-400">{f.total_cost.toLocaleString()} JOD</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Log Maintenance Modal */}
      <AnimatePresence>
        {showMaintModal && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <h3 className="font-bold text-slate-200">Log Vehicle Maintenance</h3>
                <button onClick={() => setShowMaintModal(false)} className="p-1 hover:bg-slate-800 rounded-lg transition">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleSaveMaintenance} className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-slate-400">Date</label>
                    <input 
                      type="date" required value={maintDate} onChange={e => setMaintDate(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-slate-400">Type</label>
                    <select 
                      value={maintType} onChange={e => setMaintType(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    >
                      <option value="preventative">Preventative</option>
                      <option value="corrective">Corrective</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-slate-400">Cost (JOD)</label>
                    <input 
                      type="number" step="0.01" required placeholder="50.00"
                      value={maintCost} onChange={e => setMaintCost(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-slate-400">Odometer (km)</label>
                    <input 
                      type="number" required placeholder={vehicle.odometer_km.toString()}
                      value={maintOdo} onChange={e => setMaintOdo(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1 col-span-2">
                    <label className="text-slate-400">Service Provider</label>
                    <input 
                      type="text" placeholder="Gargour Auto Services"
                      value={maintProvider} onChange={e => setMaintProvider(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1 col-span-2">
                    <label className="text-slate-400">Next Service Odometer Limit (km)</label>
                    <input 
                      type="number" placeholder="Odometer + 10000 km"
                      value={maintNextOdo} onChange={e => setMaintNextOdo(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-slate-400">Notes / Remarks</label>
                  <textarea 
                    rows={3} placeholder="Describe the maintenance done..."
                    value={maintNotes} onChange={e => setMaintNotes(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg p-3 text-slate-200 outline-none"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-white/5">
                  <button 
                    type="button" onClick={() => setShowMaintModal(false)}
                    className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition font-semibold"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" disabled={saving}
                    className="px-5 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-semibold shadow-lg shadow-blue-600/15 transition"
                  >
                    Save Log
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Log Fuel Modal */}
      <AnimatePresence>
        {showFuelModal && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <h3 className="font-bold text-slate-200">Log Vehicle Fueling</h3>
                <button onClick={() => setShowFuelModal(false)} className="p-1 hover:bg-slate-800 rounded-lg transition">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleSaveFuel} className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-slate-400">Date</label>
                    <input 
                      type="date" required value={fuelDate} onChange={e => setFuelDate(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-slate-400">Odometer (km)</label>
                    <input 
                      type="number" required placeholder={vehicle.odometer_km.toString()}
                      value={fuelOdo} onChange={e => setFuelOdo(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-slate-400">Liters</label>
                    <input 
                      type="number" step="0.01" required placeholder="45.5"
                      value={fuelLiters} onChange={e => setFuelLiters(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-slate-400">Price per Liter (JOD)</label>
                    <input 
                      type="number" step="0.001" required placeholder="0.950"
                      value={fuelPrice} onChange={e => setFuelPrice(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-slate-400">Gas Station Name</label>
                  <input 
                    type="text" placeholder="Manaseer Gas Station"
                    value={fuelStation} onChange={e => setFuelStation(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-white/5">
                  <button 
                    type="button" onClick={() => setShowFuelModal(false)}
                    className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition font-semibold"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" disabled={saving}
                    className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-white font-semibold shadow-lg shadow-emerald-600/15 transition"
                  >
                    Save Fuel Log
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
