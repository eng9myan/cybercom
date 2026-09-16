"use client";

import { useEffect, useState } from "react";
import { MapPinned, BusFront, Users } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, Loading, ErrorNote, Field } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { TransportZone, Bus, TransportSubscription, Student } from "@/lib/types";

const TRIPS = [
  { v: "full_trip", l: "Full Trip (Two-Way)" },
  { v: "half_morning", l: "Half — Morning" },
  { v: "half_afternoon", l: "Half — Afternoon" },
  { v: "custom", l: "Custom" },
];

export default function TransportPage() {
  const [zones, setZones] = useState<TransportZone[]>([]);
  const [buses, setBuses] = useState<Bus[]>([]);
  const [subs, setSubs] = useState<TransportSubscription[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [zName, setZName] = useState("Zone 1");
  const [zFee, setZFee] = useState("1000");
  const [bId, setBId] = useState("Bus #1");
  const [bCap, setBCap] = useState("30");
  const [sStudent, setSStudent] = useState("");
  const [sZone, setSZone] = useState("");
  const [sTrip, setSTrip] = useState("full_trip");
  const [sBus, setSBus] = useState("");
  const toast = useToast();

  const load = async () => {
    try {
      const [z, b, s, st] = await Promise.all([
        cyed.list<TransportZone>("transport/zones/"),
        cyed.list<Bus>("transport/buses/"),
        cyed.list<TransportSubscription>("transport/subscriptions/"),
        cyed.list<Student>("sis/students/"),
      ]);
      setZones(z); setBuses(b); setSubs(s); setStudents(st);
      if (!sStudent && st.length) setSStudent(st[0].id);
      if (!sZone && z.length) setSZone(z[0].id);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load transport");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const addZone = async () => {
    try { await cyed.create("transport/zones/", { name: zName, base_fee: zFee }); toast.push("Zone added"); await load(); }
    catch (e) { toast.push(e instanceof Error ? e.message : "Zone failed", "bad"); }
  };
  const addBus = async () => {
    try { await cyed.create("transport/buses/", { identifier: bId, capacity: parseInt(bCap) || 30 }); toast.push("Bus added"); await load(); }
    catch (e) { toast.push(e instanceof Error ? e.message : "Bus failed", "bad"); }
  };
  const addSub = async () => {
    if (!sStudent || !sZone) return;
    try {
      await cyed.create("transport/subscriptions/", { student: sStudent, zone: sZone, trip_type: sTrip, assigned_bus: sBus || null });
      toast.push("Subscription created — fee auto-calculated");
      await load();
    } catch (e) { toast.push(e instanceof Error ? e.message : "Subscription failed (duplicate or bus full)", "bad"); }
  };

  const studentName = (id: string) => { const s = students.find((x) => x.id === id); return s ? `${s.first_name} ${s.last_name}` : "—"; };
  const zoneName = (id: string) => zones.find((z) => z.id === id)?.name || "—";

  if (loading) return <Loading label="Loading transport…" />;

  const subCols: Column<TransportSubscription>[] = [
    { key: "student", header: "Student", render: (s) => <span style={{ fontWeight: 600 }}>{studentName(s.student)}</span> },
    { key: "zone", header: "Zone", render: (s) => zoneName(s.zone), width: 110 },
    { key: "trip", header: "Trip", render: (s) => TRIPS.find((t) => t.v === s.trip_type)?.l || s.trip_type },
    { key: "fee", header: "Fee", render: (s) => `$${s.fee_amount}`, align: "right", width: 100 },
    { key: "status", header: "Status", render: (s) => <Badge value={s.status} />, width: 110 },
  ];

  return (
    <div>
      <PageHeader title="Transport & Fleet" subtitle="Zones, buses, and student bus subscriptions" />
      {error && <ErrorNote error={error} />}

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))" }}>
        <StatCard label="Zones" value={zones.length} accent="cyan" icon={<MapPinned size={17} />} />
        <StatCard label="Buses" value={buses.length} accent="blue" icon={<BusFront size={17} />} />
        <StatCard label="Subscriptions" value={subs.length} accent="violet" icon={<Users size={17} />} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        <Panel title="Zones">
          <div className="space-y-1 mb-3">
            {zones.map((z) => (
              <div key={z.id} className="text-sm" style={{ display: "flex", justifyContent: "space-between", padding: "0.3rem 0", borderBottom: "1px solid var(--border)" }}>
                <span>{z.name}</span><span style={{ color: "var(--muted)" }}>${z.base_fee}</span>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", gap: 6, alignItems: "end" }}>
            <div style={{ flex: 1 }}><Field label="Name"><input className="input" value={zName} onChange={(e) => setZName(e.target.value)} /></Field></div>
            <div style={{ width: 90 }}><Field label="Base fee"><input className="input" value={zFee} onChange={(e) => setZFee(e.target.value)} /></Field></div>
            <button className="btn btn-ghost" onClick={addZone}>Add</button>
          </div>
        </Panel>
        <Panel title="Buses">
          <div className="space-y-1 mb-3">
            {buses.map((b) => (
              <div key={b.id} className="text-sm" style={{ display: "flex", justifyContent: "space-between", padding: "0.3rem 0", borderBottom: "1px solid var(--border)" }}>
                <span>{b.identifier}</span><span style={{ color: "var(--muted)" }}>{b.seats_available ?? b.capacity} free / {b.capacity}</span>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", gap: 6, alignItems: "end" }}>
            <div style={{ flex: 1 }}><Field label="Identifier"><input className="input" value={bId} onChange={(e) => setBId(e.target.value)} /></Field></div>
            <div style={{ width: 80 }}><Field label="Capacity"><input className="input" value={bCap} onChange={(e) => setBCap(e.target.value)} /></Field></div>
            <button className="btn btn-ghost" onClick={addBus}>Add</button>
          </div>
        </Panel>
      </div>

      <Panel title="New subscription — fee auto-calculated from zone × trip" className="mb-4">
        <div style={{ display: "flex", gap: 8, alignItems: "end", flexWrap: "wrap" }}>
          <div style={{ minWidth: 160 }}><Field label="Student"><select className="input" value={sStudent} onChange={(e) => setSStudent(e.target.value)}>{students.map((s) => <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>)}</select></Field></div>
          <div style={{ width: 130 }}><Field label="Zone"><select className="input" value={sZone} onChange={(e) => setSZone(e.target.value)}>{zones.map((z) => <option key={z.id} value={z.id}>{z.name}</option>)}</select></Field></div>
          <div style={{ width: 170 }}><Field label="Trip type"><select className="input" value={sTrip} onChange={(e) => setSTrip(e.target.value)}>{TRIPS.map((t) => <option key={t.v} value={t.v}>{t.l}</option>)}</select></Field></div>
          <div style={{ width: 130 }}><Field label="Bus"><select className="input" value={sBus} onChange={(e) => setSBus(e.target.value)}><option value="">—</option>{buses.map((b) => <option key={b.id} value={b.id}>{b.identifier}</option>)}</select></Field></div>
          <button className="btn btn-primary" onClick={addSub} disabled={!students.length || !zones.length}>Subscribe</button>
        </div>
      </Panel>

      <DataTable columns={subCols} rows={subs} emptyLabel="No subscriptions yet." />
    </div>
  );
}
