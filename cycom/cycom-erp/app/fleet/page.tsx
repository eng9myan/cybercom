'use client';

import React from 'react';
import Link from 'next/link';
import { Car, Fuel, Wrench, Settings } from 'lucide-react';
import { useCycomList, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';

type CycomVehicle = {
  id: number;
  name?: string;
  license_plate?: string | false;
  model_id?: Many2One;
  driver_id?: Many2One;
  odometer?: number;
  odometer_km?: number;
  state_id?: Many2One;
  state?: string;
  make?: string;
  model?: string;
};

interface FleetVehicle {
  rawId: number;
  id: string;
  plateNumber: string;
  model: string;
  driver: string;
  odometer: number;
  status: string;
}

const mapVehicle = (v: CycomVehicle): FleetVehicle => ({
  rawId: v.id,
  id: `VEH-${String(v.id).padStart(3, '0')}`,
  plateNumber: (v.license_plate as string) || '—',
  model: v.model || (v.model_id ? m2oName(v.model_id) : (v.name || '—')),
  driver: v.driver_id ? m2oName(v.driver_id, 'Unassigned') : 'Unassigned',
  odometer: Number(v.odometer_km ?? v.odometer ?? 0),
  status: v.state || (v.state_id ? m2oName(v.state_id) : 'Active'),
});

export default function FleetPage() {
  const { rows: vehicles, loading, error } = useCycomList<CycomVehicle, FleetVehicle>(
    'fleet.vehicle',
    [],
    ['name', 'license_plate', 'model_id', 'driver_id', 'odometer', 'odometer_km', 'state_id', 'state', 'model', 'make'],
    mapVehicle,
    { limit: 200, order: 'id desc' },
  );

  return (
    <div className="space-y-6 text-xs md:text-sm">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Fleet Management</h1>
          <p className="page-subtitle">Vehicles, drivers, maintenance history, and fuel logging command center.</p>
        </div>
      </div>

      {loading && <LoadingCard label="Loading fleet vehicles…" />}
      {error && <ErrorCard error={error} hint="Fleet requires the fleet module." />}
      {!loading && !error && vehicles.length === 0 && <EmptyCard label="No vehicles tracked yet." />}

      {!loading && !error && vehicles.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {vehicles.map((v) => (
            <div key={v.rawId} className="glass-card p-5 space-y-4 flex flex-col justify-between hover:border-cyan-500/20 transition-all duration-300">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400">
                      <Car className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-cyan-400 font-bold bg-cyan-950/40 border border-cyan-800/30 px-2 py-0.5 rounded">{v.id}</span>
                      <h3 className="text-sm font-bold text-white mt-1">{v.model}</h3>
                    </div>
                  </div>
                </div>

                <div className="space-y-1.5 text-xs border-t border-white/5 pt-3">
                  <div className="flex justify-between"><span className="text-slate-500">Plate</span><span className="text-slate-200 font-mono">{v.plateNumber}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Driver</span><span className="text-slate-200">{v.driver}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Odometer</span><span className="text-slate-200 font-mono">{v.odometer.toLocaleString()} km</span></div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Status</span>
                    <span className={`font-semibold capitalize ${
                      v.status === 'active' || v.status === 'Active' ? 'text-emerald-400' : 'text-amber-400'
                    }`}>{v.status}</span>
                  </div>
                </div>
              </div>

              <div className="border-t border-white/5 pt-3 mt-2 flex gap-2">
                <Link 
                  href={`/fleet/vehicles/${v.rawId}`}
                  className="flex-1 text-center py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition rounded-lg text-xs font-semibold text-slate-300 flex items-center justify-center gap-1.5"
                >
                  <Settings className="w-3.5 h-3.5" /> Details & Logs
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
