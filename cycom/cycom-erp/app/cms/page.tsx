'use client';

// Website Builder (CMS) -- drag-drop page canvas. Talks to the backend via
// the generic authenticated REST proxy (/api/cycom/rest/cms/... ->
// cycomBackendProxy), same as /custom-reports and /kds, since it needs
// custom actions (tree, publish, reorder) beyond plain CRUD.

import React, { useEffect, useState } from 'react';
import { Eye, EyeOff, Globe, Layout, Plus, Save } from 'lucide-react';
import SlottedBlockList from '@/components/cms/BuilderCanvas';
import type { BlockNode, BlockType } from '@/lib/cmsBlocks';
import { BLOCK_TYPE_LABELS, INSPECTOR_FIELDS, defaultConfigFor } from '@/lib/cmsBlocks';
import { useT } from '@/lib/i18n';

interface PageMeta {
  id: string;
  title: string;
  slug: string;
  is_published: boolean;
  is_homepage: boolean;
}

interface PageTree extends PageMeta {
  meta_description: string;
  blocks: BlockNode[];
}

const BLOCK_PALETTE: BlockType[] = ['section', 'columns', 'heading', 'text', 'image', 'button', 'spacer', 'video', 'html'];

function findBlock(blocks: BlockNode[], id: string): BlockNode | null {
  for (const b of blocks) {
    if (b.id === id) return b;
    const found = findBlock(b.children, id);
    if (found) return found;
  }
  return null;
}

async function api(path: string, options?: RequestInit) {
  const res = await fetch(`/api/cycom/rest/cms/${path}`, {
    credentials: 'include',
    headers: options?.body ? { 'Content-Type': 'application/json' } : undefined,
    ...options,
  });
  if (!res.ok) throw new Error(`Backend ${res.status}`);
  return res.status === 204 ? null : res.json();
}

export default function CmsBuilderPage() {
  const t = useT();
  const [pages, setPages] = useState<PageMeta[]>([]);
  const [newTitle, setNewTitle] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const [activeId, setActiveId] = useState<string | null>(null);
  const [tree, setTree] = useState<PageTree | null>(null);
  const [loadingTree, setLoadingTree] = useState(false);
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);
  const [draftConfig, setDraftConfig] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);

  const loadPages = async () => {
    const data = await api('pages/');
    setPages(Array.isArray(data) ? data : data.results || []);
  };

  useEffect(() => {
    loadPages();
  }, []);

  const loadTree = async (id: string) => {
    setLoadingTree(true);
    try {
      const data = await api(`pages/${id}/tree/`);
      setTree(data);
    } finally {
      setLoadingTree(false);
    }
  };

  const selectPage = async (id: string) => {
    setActiveId(id);
    setSelectedBlockId(null);
    await loadTree(id);
  };

  const createPage = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const page = await api('pages/', { method: 'POST', body: JSON.stringify({ title: newTitle }) });
      setNewTitle('');
      await loadPages();
      await selectPage(page.id);
    } catch (e2) {
      setCreateError(e2 instanceof Error ? e2.message : 'Failed');
    } finally {
      setCreating(false);
    }
  };

  const togglePublish = async () => {
    if (!tree) return;
    await api(`pages/${tree.id}/${tree.is_published ? 'unpublish' : 'publish'}/`, { method: 'POST' });
    await loadPages();
    await loadTree(tree.id);
  };

  const setHomepage = async () => {
    if (!tree) return;
    await api(`pages/${tree.id}/`, { method: 'PATCH', body: JSON.stringify({ is_homepage: true }) });
    await loadPages();
    await loadTree(tree.id);
  };

  const onInsert = async (blockType: BlockType, parentId: string | null, order: number) => {
    if (!tree) return;
    const created = await api('blocks/', {
      method: 'POST',
      body: JSON.stringify({ page: tree.id, parent: parentId, block_type: blockType, order, config: defaultConfigFor(blockType) }),
    });
    await loadTree(tree.id);
    setSelectedBlockId(created.id);
  };

  const onMove = async (blockId: string, parentId: string | null, order: number) => {
    if (!tree) return;
    await api('blocks/reorder/', {
      method: 'POST',
      body: JSON.stringify({ page: tree.id, moves: [{ id: blockId, parent: parentId, order }] }),
    });
    await loadTree(tree.id);
  };

  const onDelete = async (blockId: string) => {
    if (!tree) return;
    await api(`blocks/${blockId}/`, { method: 'DELETE' });
    if (selectedBlockId === blockId) setSelectedBlockId(null);
    await loadTree(tree.id);
  };

  const selectedBlock = tree && selectedBlockId ? findBlock(tree.blocks, selectedBlockId) : null;

  useEffect(() => {
    setDraftConfig(selectedBlock?.config || {});
  }, [selectedBlockId]); // eslint-disable-line react-hooks/exhaustive-deps

  const saveBlockConfig = async () => {
    if (!tree || !selectedBlockId) return;
    setSaving(true);
    try {
      await api(`blocks/${selectedBlockId}/`, { method: 'PATCH', body: JSON.stringify({ config: draftConfig }) });
      await loadTree(tree.id);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid grid-cols-[220px_1fr_280px] gap-4 h-[calc(100vh-7rem)]">
      {/* Left: pages + palette */}
      <div className="space-y-4 overflow-y-auto">
        <div className="glass-card p-3 space-y-2">
          <h2 className="text-xs font-black text-slate-400 uppercase tracking-wide">{t('cmsBuilder.pages')}</h2>
          {pages.length === 0 && <p className="text-[11px] text-slate-600 italic">{t('cmsBuilder.empty')}</p>}
          {pages.map((p) => (
            <button
              key={p.id}
              onClick={() => selectPage(p.id)}
              className={`w-full text-start px-2 py-1.5 rounded-lg text-xs flex items-center justify-between gap-1 ${
                activeId === p.id ? 'bg-cyan-500/15 text-cyan-300' : 'text-slate-300 hover:bg-white/5'
              }`}
            >
              <span className="truncate">{p.title}</span>
              {p.is_homepage && <Globe className="w-3 h-3 shrink-0" />}
            </button>
          ))}
          <form onSubmit={createPage} className="pt-2 border-t border-white/5 space-y-1.5">
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder={t('cmsBuilder.pageTitlePlaceholder')}
              required
              className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-xs outline-none focus:border-white/30"
            />
            {createError && <p className="text-red-400 text-[10px]">{createError}</p>}
            <button type="submit" disabled={creating} className="w-full btn-primary py-1.5 text-[11px] flex items-center justify-center gap-1 disabled:opacity-50">
              <Plus className="w-3 h-3" /> {creating ? t('cmsBuilder.creating') : t('cmsBuilder.create')}
            </button>
          </form>
        </div>

        <div className="glass-card p-3 space-y-1.5">
          <h2 className="text-xs font-black text-slate-400 uppercase tracking-wide">{t('cmsBuilder.palette')}</h2>
          {BLOCK_PALETTE.map((type) => (
            <div
              key={type}
              draggable
              onDragStart={(e) => e.dataTransfer.setData('application/json', JSON.stringify({ kind: 'new', block_type: type }))}
              className="px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300 cursor-grab active:cursor-grabbing hover:border-white/25"
            >
              {BLOCK_TYPE_LABELS[type]}
            </div>
          ))}
          <p className="text-[10px] text-slate-600 pt-1">{t('cmsBuilder.dragHint')}</p>
        </div>
      </div>

      {/* Center: canvas */}
      <div className="glass-card p-4 overflow-y-auto">
        {!tree && <p className="text-slate-500 text-sm italic">{t('cmsBuilder.selectPagePrompt')}</p>}
        {tree && (
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3 pb-3 border-b border-white/5">
              <div className="min-w-0">
                <h1 className="text-sm font-black text-white truncate">{tree.title}</h1>
                <p className="text-[11px] text-slate-500">/{tree.slug}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {!tree.is_homepage && (
                  <button onClick={setHomepage} className="px-2 py-1 rounded-lg bg-white/5 border border-white/10 text-[11px] text-slate-300 hover:border-white/25">
                    {t('cmsBuilder.setHomepage')}
                  </button>
                )}
                <button
                  onClick={togglePublish}
                  className={`px-2 py-1 rounded-lg border text-[11px] flex items-center gap-1 ${
                    tree.is_published ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-white/5 border-white/10 text-slate-300'
                  }`}
                >
                  {tree.is_published ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                  {tree.is_published ? t('cmsBuilder.published') : t('cmsBuilder.unpublished')}
                </button>
              </div>
            </div>

            {loadingTree ? (
              <p className="text-slate-500 text-sm">{t('cmsBuilder.loading')}</p>
            ) : (
              <SlottedBlockList
                blocks={tree.blocks}
                parentId={null}
                selectedId={selectedBlockId}
                onSelect={setSelectedBlockId}
                onDelete={onDelete}
                onMove={onMove}
                onInsert={onInsert}
                emptyHint={t('cmsBuilder.canvasEmpty')}
              />
            )}
          </div>
        )}
      </div>

      {/* Right: inspector */}
      <div className="glass-card p-4 overflow-y-auto">
        <h2 className="text-xs font-black text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <Layout className="w-3.5 h-3.5" /> {BLOCK_TYPE_LABELS[selectedBlock?.block_type as BlockType] || ''}
        </h2>
        {!selectedBlock && <p className="text-slate-500 text-xs italic">{t('cmsBuilder.selectBlockPrompt')}</p>}
        {selectedBlock && (
          <div className="space-y-3">
            {INSPECTOR_FIELDS[selectedBlock.block_type].map((field) => (
              <div key={field.key} className="space-y-1">
                <label className="text-[11px] font-bold text-slate-400">{field.label}</label>
                {field.type === 'textarea' ? (
                  <textarea
                    value={draftConfig[field.key] ?? ''}
                    onChange={(e) => setDraftConfig((c) => ({ ...c, [field.key]: e.target.value }))}
                    rows={4}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-xs outline-none focus:border-white/30 resize-none"
                  />
                ) : field.type === 'select' ? (
                  <select
                    value={String(draftConfig[field.key] ?? '')}
                    onChange={(e) => setDraftConfig((c) => ({ ...c, [field.key]: e.target.value }))}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-xs outline-none focus:border-white/30"
                  >
                    {field.options?.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                ) : field.type === 'color' ? (
                  <input
                    type="color"
                    value={draftConfig[field.key] || '#000000'}
                    onChange={(e) => setDraftConfig((c) => ({ ...c, [field.key]: e.target.value }))}
                    className="w-full h-8 bg-white/5 border border-white/10 rounded-lg"
                  />
                ) : (
                  <input
                    type={field.type === 'number' ? 'number' : 'text'}
                    value={draftConfig[field.key] ?? ''}
                    onChange={(e) =>
                      setDraftConfig((c) => ({
                        ...c,
                        [field.key]: field.type === 'number' ? Number(e.target.value) : e.target.value,
                      }))
                    }
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-xs outline-none focus:border-white/30"
                  />
                )}
              </div>
            ))}
            <button onClick={saveBlockConfig} disabled={saving} className="btn-primary w-full py-1.5 text-xs flex items-center justify-center gap-1.5 disabled:opacity-50">
              <Save className="w-3.5 h-3.5" /> {saving ? t('cmsBuilder.saving') : t('cmsBuilder.save')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
