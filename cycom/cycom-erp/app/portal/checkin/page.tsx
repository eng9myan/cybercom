'use client';

import React, { useState } from 'react';
import { MapPin, ShieldAlert, CheckCircle2, ShieldCheck, Wifi } from 'lucide-react';

export default function MobileCheckInPortal() {
  const [deviceBound, setDeviceBound] = useState('iPhone 15 Pro Max (Bound)');
  const [gpsLatitude, setGpsLatitude] = useState('31.9522');
  const [gpsLongitude, setGpsLongitude] = useState('35.9106');
  const [status, setStatus] = useState<'Idle' | 'Checking' | 'Success' | 'OutsideGeofence' | 'MismatchDevice'>('Idle');

  const triggerCheck = () => {
    setStatus('Checking');
    setTimeout(() => {
      // If HQ coords, return success, otherwise trigger geofence warning
      if (gpsLatitude === '31.9522' && gpsLongitude === '35.9106') {
        setStatus('Success');
      } else {
        setStatus('OutsideGeofence');
      }
    }, 1200);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Mobile Check-In</h1>
          <p className="page-subtitle">Perform daily shifts clock in/out with hardware device binding and GPS geofence checks (portal_check_in).</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Device verification & coordinates input */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Identity & Location Check</h2>
          <div className="space-y-3 text-sm">
            <div>
              <span className="text-xs text-slate-500 block">Hardware Fingerprint ID</span>
              <span className="font-mono text-slate-200 font-semibold">{deviceBound}</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Simulated Latitude</label>
                <input 
                  type="text" 
                  className="input-field font-mono" 
                  value={gpsLatitude}
                  onChange={(e) => setGpsLatitude(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Simulated Longitude</label>
                <input 
                  type="text" 
                  className="input-field font-mono" 
                  value={gpsLongitude}
                  onChange={(e) => setGpsLongitude(e.target.value)}
                />
              </div>
            </div>
            <p className="text-[10px] text-slate-500">
              Note: The default coordinates match Amman HQ office. Modify them to test GPS geofence restrictions.
            </p>

            <button 
              onClick={triggerCheck}
              disabled={status === 'Checking'}
              className="btn-primary w-full py-2.5 flex items-center justify-center gap-2"
            >
              <MapPin className="w-4 h-4" /> 
              {status === 'Checking' ? 'Verifying GPS & Hardware...' : 'Clock In Now'}
            </button>
          </div>
        </div>

        {/* Right Column - Status result */}
        <div className="glass-card p-6 flex flex-col justify-center items-center text-center space-y-4 min-h-[300px]">
          {status === 'Idle' && (
            <>
              <Wifi className="w-12 h-12 text-slate-500 animate-pulse" />
              <h3 className="text-base font-bold text-white">System Ready</h3>
              <p className="text-xs text-slate-400 max-w-xs">Waiting for coordinates verification. Stand inside the permitted office geofence to register.</p>
            </>
          )}

          {status === 'Checking' && (
            <>
              <div className="w-10 h-10 border-4 border-cyan-500/20 border-t-cyan-400 rounded-full animate-spin" />
              <h3 className="text-base font-bold text-white">Verifying Location Bounds</h3>
              <p className="text-xs text-slate-400 max-w-xs">Connecting to Cycom GPS geofence controller...</p>
            </>
          )}

          {status === 'Success' && (
            <>
              <CheckCircle2 className="w-12 h-12 text-emerald-400" />
              <h3 className="text-base font-bold text-white">Clock In Successful</h3>
              <p className="text-xs text-slate-400 max-w-xs">Check-in recorded at <strong>08:00 AM</strong>. Normalized check-in applied. Have a great day!</p>
            </>
          )}

          {status === 'OutsideGeofence' && (
            <>
              <ShieldAlert className="w-12 h-12 text-rose-400" />
              <h3 className="text-base font-bold text-white">Location Verification Failed</h3>
              <p className="text-xs text-slate-400 max-w-xs">GPS coordinates are outside the permitted warehouse geofence bounds. Access denied.</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
