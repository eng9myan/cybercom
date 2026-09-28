'use client';

import React, { useMemo, useRef, useState } from 'react';
import { Save, Plus, X, Move } from 'lucide-react';
import { useT } from '@/lib/i18n';
import { DEFAULT_SIZE, FlatLocationNode, occupancyHexColor } from '@/lib/warehouseHeat';

const PX_PER_UNIT = 40;

interface Draft {
  pos_x: number | null;
  pos_y: number | null;
  size_w: number;
  size_d: number;
}

interface Warehouse2DEditorProps {
  warehouseId: string;
  nodes: FlatLocationNode[];
  onSaved: () => void;
}

export default function Warehouse2DEditor({ warehouseId, nodes, onSaved }: Warehouse2DEditorProps) {
  const t = useT();
  const canvasRef = useRef<HTMLDivElement>(null);

  const initialDraft = useMemo(() => {
    const d: Record<string, Draft> = {};
    nodes.forEach((n) => {
      const def = DEFAULT_SIZE[n.location_type] || { w: 1, d: 1 };
      d[n.id] = {
        pos_x: n.pos_x,
        pos_y: n.pos_y,
        size_w: n.size_w ?? def.w,
        size_d: n.size_d ?? def.d,
      };
    });
    return d;
  }, [nodes]);

  const [draft, setDraft] = useState<Record<string, Draft>>(initialDraft);
  const [editMode, setEditMode] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [dragId, setDragId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const dragOffset = useRef({ x: 0, y: 0 });

  const placed = nodes.filter((n) => draft[n.id]?.pos_x !== null);
  const unplaced = nodes.filter((n) => draft[n.id]?.pos_x === null);
  const selected = selectedId ? nodes.find((n) => n.id === selectedId) : null;

  const nextFreeSlot = (): { x: number; y: number } => {
    const count = placed.length;
    const cols = 6;
    return { x: (count % cols) * 3, y: Math.floor(count / cols) * 3 };
  };

  const handlePlace = (id: string) => {
    const slot = nextFreeSlot();
    setDraft((d) => ({ ...d, [id]: { ...d[id], pos_x: slot.x, pos_y: slot.y } }));
    setEditMode(true);
  };

  const handleRemove = (id: string) => {
    setDraft((d) => ({ ...d, [id]: { ...d[id], pos_x: null, pos_y: null } }));
    setSelectedId(null);
  };

  const handlePointerDown = (e: React.PointerEvent, id: string) => {
    if (!editMode) { setSelectedId(id); return; }
    e.currentTarget.setPointerCapture(e.pointerId);
    const rect = canvasRef.current?.getBoundingClientRect();
    const cur = draft[id];
    if (!rect || !cur) return;
    dragOffset.current = {
      x: e.clientX - rect.left - (cur.pos_x ?? 0) * PX_PER_UNIT,
      y: e.clientY - rect.top - (cur.pos_y ?? 0) * PX_PER_UNIT,
    };
    setDragId(id);
    setSelectedId(id);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!dragId) return;
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = Math.max(0, Math.round((e.clientX - rect.left - dragOffset.current.x) / PX_PER_UNIT));
    const y = Math.max(0, Math.round((e.clientY - rect.top - dragOffset.current.y) / PX_PER_UNIT));
    setDraft((d) => ({ ...d, [dragId]: { ...d[dragId], pos_x: x, pos_y: y } }));
  };

  const handlePointerUp = () => setDragId(null);

  const handleSave = async () => {
    setSaving(true);
    try {
      const positions = nodes.map((n) => ({
        id: n.id,
        pos_x: draft[n.id]?.pos_x ?? null,
        pos_y: draft[n.id]?.pos_y ?? null,
        size_w: draft[n.id]?.pos_x !== null ? draft[n.id]?.size_w : null,
        size_d: draft[n.id]?.pos_x !== null ? draft[n.id]?.size_d : null,
      }));
      await fetch(`/api/cycom/rest/inventory/warehouses/${warehouseId}/layout/positions/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ positions }),
      });
      onSaved();
      setEditMode(false);
    } finally {
      setSaving(false);
    }
  };

  const bounds = placed.reduce(
    (acc, n) => {
      const d = draft[n.id];
      return {
        w: Math.max(acc.w, ((d.pos_x ?? 0) + d.size_w + 2) * PX_PER_UNIT),
        h: Math.max(acc.h, ((d.pos_y ?? 0) + d.size_d + 2) * PX_PER_UNIT),
      };
    },
    { w: 800, h: 500 },
  );

  return (
    <div className="glass-card p-5 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
          <Move className="w-4 h-4 text-amber-400" /> {t('warehouseMap.floorPlan2d')}
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setEditMode((v) => !v)}
            className={`px-3 py-1.5 rounded-lg text-[11px] font-bold border transition ${
              editMode ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' : 'bg-white/5 border-white/10 text-slate-400'
            }`}
          >
            {editMode ? t('warehouseMap.editingOn') : t('warehouseMap.editLayout')}
          </button>
          {editMode && (
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-600/90 hover:bg-amber-500 disabled:opacity-50 text-white text-[11px] font-bold transition"
            >
              <Save className="w-3.5 h-3.5" /> {t('warehouseMap.saveLayout')}
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-4">
        <div
          ref={canvasRef}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          className="relative flex-1 overflow-auto rounded-xl border border-slate-850 bg-slate-950/60"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)',
            backgroundSize: `${PX_PER_UNIT}px ${PX_PER_UNIT}px`,
            minHeight: 400, maxHeight: 520,
          }}
        >
          <div style={{ width: bounds.w, height: bounds.h, position: 'relative' }}>
            {placed.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center text-slate-600 text-xs">
                {t('warehouseMap.noPlacements')}
              </div>
            )}
            {placed.map((n) => {
              const d = draft[n.id];
              const color = occupancyHexColor(n.occupancy_percent);
              return (
                <div
                  key={n.id}
                  onPointerDown={(e) => handlePointerDown(e, n.id)}
                  className={`absolute rounded-lg border flex flex-col items-center justify-center text-center select-none transition-shadow ${
                    editMode ? 'cursor-move' : 'cursor-pointer'
                  } ${selectedId === n.id ? 'ring-2 ring-white/60' : ''}`}
                  style={{
                    left: (d.pos_x ?? 0) * PX_PER_UNIT,
                    top: (d.pos_y ?? 0) * PX_PER_UNIT,
                    width: d.size_w * PX_PER_UNIT,
                    height: d.size_d * PX_PER_UNIT,
                    backgroundColor: `${color}33`,
                    borderColor: color,
                  }}
                  title={n.parent_path}
                >
                  <span className="text-[10px] font-bold text-white truncate px-1">{n.code}</span>
                  {n.occupancy_percent !== null && (
                    <span className="text-[9px] font-mono" style={{ color }}>{n.occupancy_percent}%</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="w-56 flex-shrink-0 space-y-3">
          {selected && (
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-850 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{selected.code}</span>
                <button onClick={() => setSelectedId(null)} className="text-slate-500 hover:text-white">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
              <p className="text-[10px] text-slate-500">{selected.parent_path || selected.location_type}</p>
              {selected.occupancy_percent !== null && (
                <p className="text-[10px] text-slate-400">{t('warehouseMap.occupancyLabel')}: <span className="font-mono">{selected.occupancy_percent}%</span></p>
              )}
              {editMode && (
                <div className="flex items-center gap-2 pt-1">
                  <label className="text-[9px] text-slate-500 flex-1">
                    W
                    <input
                      type="number" min={0.5} step={0.5}
                      value={draft[selected.id]?.size_w ?? 1}
                      onChange={(e) => setDraft((d) => ({ ...d, [selected.id]: { ...d[selected.id], size_w: parseFloat(e.target.value) || 1 } }))}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-1.5 py-1 text-[10px] text-slate-200 outline-none mt-0.5"
                    />
                  </label>
                  <label className="text-[9px] text-slate-500 flex-1">
                    D
                    <input
                      type="number" min={0.5} step={0.5}
                      value={draft[selected.id]?.size_d ?? 1}
                      onChange={(e) => setDraft((d) => ({ ...d, [selected.id]: { ...d[selected.id], size_d: parseFloat(e.target.value) || 1 } }))}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-1.5 py-1 text-[10px] text-slate-200 outline-none mt-0.5"
                    />
                  </label>
                </div>
              )}
              {editMode && (
                <button
                  onClick={() => handleRemove(selected.id)}
                  className="w-full text-[10px] font-bold text-rose-400 hover:bg-rose-500/10 rounded-lg py-1.5 transition"
                >
                  {t('warehouseMap.removeFromMap')}
                </button>
              )}
            </div>
          )}

          {editMode && unplaced.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-[10px] font-bold text-slate-500 uppercase">{t('warehouseMap.unplaced')}</p>
              <div className="max-h-64 overflow-y-auto space-y-1">
                {unplaced.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => handlePlace(n.id)}
                    className="w-full flex items-center justify-between gap-2 px-2 py-1.5 rounded-lg bg-white/3 hover:bg-white/8 border border-white/5 text-[10px] text-slate-300 transition"
                  >
                    <span className="truncate">{n.code}</span>
                    <Plus className="w-3 h-3 text-slate-500 flex-shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
