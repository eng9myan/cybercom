'use client';

import React, { useState } from 'react';
import { GripVertical, Trash2 } from 'lucide-react';
import type { BlockNode, BlockType } from '@/lib/cmsBlocks';
import { BLOCK_TYPE_LABELS, CONTAINER_BLOCK_TYPES } from '@/lib/cmsBlocks';

type DragPayload = { kind: 'new'; block_type: BlockType } | { kind: 'move'; id: string };

function readPayload(e: React.DragEvent): DragPayload | null {
  try {
    const raw = e.dataTransfer.getData('application/json');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

interface DropSlotProps {
  slotKey: string;
  activeKey: string | null;
  setActiveKey: (k: string | null) => void;
  onDrop: (payload: DragPayload) => void;
}

function DropSlot({ slotKey, activeKey, setActiveKey, onDrop }: DropSlotProps) {
  const isActive = activeKey === slotKey;
  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setActiveKey(slotKey);
      }}
      onDragLeave={() => setActiveKey(null)}
      onDrop={(e) => {
        e.preventDefault();
        const payload = readPayload(e);
        setActiveKey(null);
        if (payload) onDrop(payload);
      }}
      className={`transition-all rounded-full ${isActive ? 'h-8 bg-cyan-500/20 border border-dashed border-cyan-400' : 'h-2'}`}
    />
  );
}

interface SlottedBlockListProps {
  blocks: BlockNode[];
  parentId: string | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onMove: (blockId: string, parentId: string | null, order: number) => void;
  onInsert: (blockType: BlockType, parentId: string | null, order: number) => void;
  emptyHint?: string;
}

export default function SlottedBlockList({
  blocks,
  parentId,
  selectedId,
  onSelect,
  onDelete,
  onMove,
  onInsert,
  emptyHint,
}: SlottedBlockListProps) {
  const [activeKey, setActiveKey] = useState<string | null>(null);

  const handleDropAt = (index: number) => (payload: DragPayload) => {
    if (payload.kind === 'new') onInsert(payload.block_type, parentId, index);
    else onMove(payload.id, parentId, index);
  };

  return (
    <div className="space-y-1">
      <DropSlot slotKey={`${parentId}:0`} activeKey={activeKey} setActiveKey={setActiveKey} onDrop={handleDropAt(0)} />
      {blocks.length === 0 && emptyHint && (
        <p className="text-[11px] text-slate-600 italic text-center py-2">{emptyHint}</p>
      )}
      {blocks.map((block, i) => (
        <React.Fragment key={block.id}>
          <EditableBlock
            block={block}
            selectedId={selectedId}
            onSelect={onSelect}
            onDelete={onDelete}
            onMove={onMove}
            onInsert={onInsert}
          />
          <DropSlot
            slotKey={`${parentId}:${i + 1}`}
            activeKey={activeKey}
            setActiveKey={setActiveKey}
            onDrop={handleDropAt(i + 1)}
          />
        </React.Fragment>
      ))}
    </div>
  );
}

function DropSlotGridCell({
  parentId,
  index,
  onMove,
  onInsert,
}: {
  parentId: string;
  index: number;
  onMove: (blockId: string, parentId: string | null, order: number) => void;
  onInsert: (blockType: BlockType, parentId: string | null, order: number) => void;
}) {
  const [active, setActive] = useState(false);
  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setActive(true);
      }}
      onDragLeave={() => setActive(false)}
      onDrop={(e) => {
        e.preventDefault();
        setActive(false);
        const payload = readPayload(e);
        if (!payload) return;
        if (payload.kind === 'new') onInsert(payload.block_type, parentId, index);
        else onMove(payload.id, parentId, index);
      }}
      className={`min-h-[48px] rounded-lg border border-dashed flex items-center justify-center text-[10px] transition-colors ${
        active ? 'border-cyan-400 bg-cyan-500/10 text-cyan-300' : 'border-white/10 text-slate-600'
      }`}
    >
      + Add
    </div>
  );
}

function EditableBlock({
  block,
  selectedId,
  onSelect,
  onDelete,
  onMove,
  onInsert,
}: {
  block: BlockNode;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onMove: (blockId: string, parentId: string | null, order: number) => void;
  onInsert: (blockType: BlockType, parentId: string | null, order: number) => void;
}) {
  const c = block.config || {};
  const isSelected = selectedId === block.id;
  const isContainer = CONTAINER_BLOCK_TYPES.includes(block.block_type);

  return (
    <div
      draggable
      onDragStart={(e) => {
        e.stopPropagation();
        e.dataTransfer.setData('application/json', JSON.stringify({ kind: 'move', id: block.id }));
      }}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(block.id);
      }}
      className={`relative rounded-xl border p-3 cursor-pointer transition-colors ${
        isSelected ? 'border-cyan-400 bg-cyan-500/5' : 'border-white/10 hover:border-white/25'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-wide">
          <GripVertical className="w-3 h-3" /> {BLOCK_TYPE_LABELS[block.block_type]}
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(block.id);
          }}
          className="text-slate-600 hover:text-red-400 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {block.block_type === 'section' && (
        <div style={{ background: c.background || 'transparent', padding: 8 }} className="rounded-lg">
          <SlottedBlockList
            blocks={block.children}
            parentId={block.id}
            selectedId={selectedId}
            onSelect={onSelect}
            onDelete={onDelete}
            onMove={onMove}
            onInsert={onInsert}
            emptyHint="Drop blocks into this section"
          />
        </div>
      )}
      {block.block_type === 'columns' && (
        // Children aren't assigned to a specific column -- same as the
        // public renderer, they flow left-to-right/top-to-bottom into the
        // CSS grid in their existing order, so a drag reorder here and the
        // live page always agree on layout without extra column-index
        // bookkeeping in each child's config.
        <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${Number(c.column_count) || 2}, minmax(0, 1fr))` }}>
          {block.children.map((child) => (
            <div key={child.id} className="border border-dashed border-white/10 rounded-lg p-1">
              <EditableBlock
                block={child}
                selectedId={selectedId}
                onSelect={onSelect}
                onDelete={onDelete}
                onMove={onMove}
                onInsert={onInsert}
              />
            </div>
          ))}
          <DropSlotGridCell parentId={block.id} index={block.children.length} onMove={onMove} onInsert={onInsert} />
        </div>
      )}
      {block.block_type === 'heading' && (
        <p className="font-black text-white text-lg truncate">{c.text || '(empty heading)'}</p>
      )}
      {block.block_type === 'text' && <p className="text-slate-300 text-sm line-clamp-3">{c.text || '(empty text)'}</p>}
      {block.block_type === 'image' &&
        (c.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={c.image_url} alt={c.alt || ''} className="w-full h-24 object-cover rounded-lg" />
        ) : (
          <div className="w-full h-16 rounded-lg bg-white/5 flex items-center justify-center text-slate-600 text-xs">
            No image set
          </div>
        ))}
      {block.block_type === 'button' && (
        <span className="btn-primary inline-block py-1.5 px-4 text-xs">{c.label || 'Button'}</span>
      )}
      {block.block_type === 'spacer' && (
        <div className="w-full bg-white/5 rounded" style={{ height: Math.min(Number(c.height) || 40, 60) }} />
      )}
      {block.block_type === 'video' && (
        <div className="w-full h-16 rounded-lg bg-white/5 flex items-center justify-center text-slate-600 text-xs">
          {c.video_url || 'No video URL set'}
        </div>
      )}
      {block.block_type === 'html' && (
        <div className="w-full rounded-lg bg-white/5 p-2 text-[11px] text-slate-500 font-mono truncate">
          {c.html || '<!-- empty -->'}
        </div>
      )}
    </div>
  );
}
