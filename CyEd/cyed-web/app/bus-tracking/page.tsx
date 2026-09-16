"use client";

import { useEffect, useRef, useState } from "react";
import { cyed } from "@/lib/cyed";
import { PageHeader, Loading, ErrorNote, Empty, Field } from "@/components/ui";
import { Panel } from "@/components/kit";
import { Gauge, MapPin } from "lucide-react";
import type { Bus } from "@/lib/types";

type LatLng = { lat: number; lng: number };
type Live = {
  location: { lat: string; lng: string; speed_kmh: string } | null;
  route: { stops: { id: string; name: string; lat: string | null; lng: string | null; sequence: number }[] } | null;
  etas: { name: string; eta_min: number; distance_km: number }[];
};

function project(points: LatLng[], w: number, h: number, pad = 28) {
  const lats = points.map((p) => p.lat), lngs = points.map((p) => p.lng);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  const sx = (lng: number) => pad + ((lng - minLng) / (maxLng - minLng || 1)) * (w - 2 * pad);
  const sy = (lat: number) => pad + ((maxLat - lat) / (maxLat - minLat || 1)) * (h - 2 * pad);
  return { sx, sy };
}

export default function BusTrackingPage() {
  const [buses, setBuses] = useState<Bus[]>([]);
  const [busId, setBusId] = useState("");
  const [live, setLive] = useState<Live | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const b = await cyed.list<Bus>("transport/buses/");
        setBuses(b);
        if (b.length) setBusId(b[0].id);
      } catch (e) { setError(e instanceof Error ? e.message : "Failed to load buses"); }
      finally { setLoading(false); }
    })();
  }, []);

  useEffect(() => {
    if (!busId) return;
    const poll = async () => {
      try { setLive(await cyed.get<Live>(`transport/buses/${busId}/live/`)); setError(null); }
      catch (e) { setError(e instanceof Error ? e.message : "Failed to load live position"); }
    };
    poll();
    timer.current = setInterval(poll, 5000);
    return () => { if (timer.current) clearInterval(timer.current); };
  }, [busId]);

  if (loading) return <Loading label="Loading bus tracking…" />;

  const W = 640, H = 380;
  const stops = (live?.route?.stops || []).filter((s) => s.lat != null && s.lng != null)
    .map((s) => ({ ...s, lat: Number(s.lat), lng: Number(s.lng) }));
  const busPt = live?.location ? { lat: Number(live.location.lat), lng: Number(live.location.lng) } : null;
  const all: LatLng[] = [...stops, ...(busPt ? [busPt] : [])];
  const { sx, sy } = project(all.length ? all : [{ lat: 0, lng: 0 }], W, H);

  return (
    <div>
      <PageHeader
        title="Live Bus Tracking"
        subtitle="Real-time position + ETAs (polls every 5s)"
        action={<span className="status status-ok"><span className="live-dot" style={{ marginRight: 4 }} />live · 5s</span>}
      />
      {error && <ErrorNote error={error} />}

      <div style={{ width: 280, marginBottom: 12 }}>
        <Field label="Bus">
          <select className="input" value={busId} onChange={(e) => setBusId(e.target.value)}>
            {buses.map((b) => <option key={b.id} value={b.id}>{b.identifier}</option>)}
          </select>
        </Field>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 260px", gap: 16, alignItems: "start" }}>
        <div className="card" style={{ padding: 8 }}>
          {all.length === 0 || (!busPt && stops.length === 0) ? (
            <Empty label="No GPS pings or route stops yet for this bus." />
          ) : (
            <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", background: "radial-gradient(600px 400px at 30% 20%, #0f1d3a, #0a1120)", borderRadius: 12 }}>
              <defs>
                <linearGradient id="route-grad" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" />
                  <stop offset="100%" stopColor="#22d3ee" />
                </linearGradient>
                <filter id="glow"><feGaussianBlur stdDeviation="3" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
              </defs>
              {/* subtle grid */}
              {Array.from({ length: 8 }).map((_, i) => (
                <line key={`h${i}`} x1={0} y1={(H / 8) * i} x2={W} y2={(H / 8) * i} stroke="rgba(255,255,255,0.04)" />
              ))}
              {stops.length > 1 && (
                <polyline points={stops.map((s) => `${sx(s.lng)},${sy(s.lat)}`).join(" ")} fill="none" stroke="url(#route-grad)" strokeWidth={2.5} strokeDasharray="6 5" strokeLinecap="round" />
              )}
              {stops.map((s) => (
                <g key={s.id}>
                  <circle cx={sx(s.lng)} cy={sy(s.lat)} r={5} fill="#8b5cf6" filter="url(#glow)" />
                  <text x={sx(s.lng) + 9} y={sy(s.lat) + 3} fontSize={9} fill="#a3b1cc">{s.name}</text>
                </g>
              ))}
              {busPt && (
                <g filter="url(#glow)">
                  <circle cx={sx(busPt.lng)} cy={sy(busPt.lat)} r={12} fill="none" stroke="#22d3ee" strokeWidth={1.5} opacity={0.6}>
                    <animate attributeName="r" values="9;18;9" dur="1.8s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.7;0;0.7" dur="1.8s" repeatCount="indefinite" />
                  </circle>
                  <circle cx={sx(busPt.lng)} cy={sy(busPt.lat)} r={8} fill="#22d3ee" stroke="#fff" strokeWidth={2} />
                  <text x={sx(busPt.lng) + 13} y={sy(busPt.lat) + 3} fontSize={10} fill="#e8eef9" fontWeight={700}>Bus</text>
                </g>
              )}
            </svg>
          )}
        </div>

        <Panel title={<div className="flex items-center gap-2"><MapPin size={15} style={{ color: "var(--cyan)" }} /><span className="label">Estimated arrivals</span></div>}>
          {live?.location ? (
            <div className="flex items-center gap-2 text-xs mb-3" style={{ color: "var(--muted)" }}>
              <Gauge size={13} /> Speed {Number(live.location.speed_kmh).toFixed(0)} km/h
            </div>
          ) : <div className="text-xs mb-3" style={{ color: "var(--muted)" }}>Awaiting first GPS ping…</div>}
          <div className="space-y-1">
            {(live?.etas || []).map((e, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", padding: "5px 0", borderBottom: "1px solid var(--border)" }}>
                <span>{e.name}</span>
                <span className="grad-text" style={{ fontWeight: 700 }}>{e.eta_min} min</span>
              </div>
            ))}
          </div>
          {(!live?.etas || live.etas.length === 0) && <Empty label="No ETAs (need a route + position)." />}
        </Panel>
      </div>
    </div>
  );
}
