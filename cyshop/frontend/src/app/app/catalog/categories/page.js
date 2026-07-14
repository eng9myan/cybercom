"use client";

import { useState, useEffect, useCallback } from "react";
import { Plus, Folder, Pencil, Trash2, X, RefreshCw, CheckCircle2, AlertTriangle, Tag } from "lucide-react";
import { api } from "@/lib/api";

const EMPTY_FORM = { name: "", company: "", parent: "", sort_order: 0, image_url: "" };

function Toast({ msg, ok, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3500); return () => clearTimeout(t); }, [onDone]);
  return (
    <div className={`fixed bottom-6 right-6 z-[200] flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl text-white text-sm font-medium ${ok ? "bg-[#16A34A]" : "bg-[#DC2626]"}`}>
      {ok ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
      {msg}
    </div>
  );
}

function CategoryModal({ category, companies, allCategories, onSave, onClose }) {
  const [form, setForm] = useState(category ? { ...category, parent: category.parent || "" } : { ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);
  const isEdit = Boolean(category);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const parents = allCategories.filter((c) => !category || c.id !== category.id);

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    const payload = { ...form, parent: form.parent || null };
    try {
      if (isEdit) {
        await api.patch(`/api/v1/catalog/categories/${category.id}/`, payload);
      } else {
        await api.post("/api/v1/catalog/categories/", payload);
      }
      onSave(isEdit ? "Category updated." : "Category created.");
    } catch (err) {
      onSave(null, err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-[var(--color-line)]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-line)]">
          <h2 className="font-heading font-bold text-lg">{isEdit ? "Edit Category" : "New Category"}</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4">
          <div>
            <label className="cy-label">Name *</label>
            <input required className="cy-input" value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="e.g. Beverages" />
          </div>
          <div>
            <label className="cy-label">Company *</label>
            <select required className="cy-input" value={form.company} onChange={(e) => set("company", e.target.value)}>
              <option value="">— select company —</option>
              {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="cy-label">Parent Category</label>
            <select className="cy-input" value={form.parent} onChange={(e) => set("parent", e.target.value)}>
              <option value="">— top-level —</option>
              {parents.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="cy-label">Sort Order</label>
            <input type="number" min="0" className="cy-input" value={form.sort_order} onChange={(e) => set("sort_order", parseInt(e.target.value, 10) || 0)} />
          </div>
          <div>
            <label className="cy-label">Image URL</label>
            <input className="cy-input" value={form.image_url || ""} onChange={(e) => set("image_url", e.target.value)} placeholder="https://…" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="cy-btn cy-btn-ghost">Cancel</button>
            <button type="submit" disabled={saving} className="cy-btn cy-btn-primary">
              {saving ? "Saving…" : isEdit ? "Save" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null);
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [cats, comps] = await Promise.all([
        api.get("/api/v1/catalog/categories/"),
        api.get("/api/v1/tenants/companies/"),
      ]);
      setCategories(Array.isArray(cats) ? cats : cats.results || []);
      setCompanies(Array.isArray(comps) ? comps : comps.results || []);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSave = (ok, err) => {
    if (ok) { setModal(null); setToast({ msg: ok, ok: true }); load(); }
    else setToast({ msg: err, ok: false });
  };

  const handleDelete = async (cat) => {
    if (!window.confirm(`Delete category "${cat.name}"?`)) return;
    try {
      await api.patch(`/api/v1/catalog/categories/${cat.id}/`, { is_deleted: true });
      setToast({ msg: "Category deleted.", ok: true });
      load();
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    }
  };

  const topLevel = categories.filter((c) => !c.parent);
  const children = (parentId) => categories.filter((c) => c.parent === parentId);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading font-bold text-2xl">Product Categories</h2>
          <p className="text-sm text-[var(--color-ink-muted)] mt-0.5">{categories.length} categories</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={load} className="cy-btn cy-btn-ghost !py-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setModal("create")} className="cy-btn cy-btn-primary">
            <Plus className="w-4 h-4" /> New Category
          </button>
        </div>
      </div>

      <div className="cy-card divide-y divide-[var(--color-line)]">
        {loading ? (
          <div className="py-16 text-center text-[var(--color-ink-muted)]">Loading…</div>
        ) : topLevel.length === 0 ? (
          <div className="py-16 text-center">
            <Tag className="w-10 h-10 mx-auto mb-3 text-[var(--color-ink-muted)] opacity-40" />
            <p className="text-[var(--color-ink-muted)]">No categories yet.</p>
            <button onClick={() => setModal("create")} className="mt-3 cy-btn cy-btn-primary !py-2 !text-xs">
              <Plus className="w-3.5 h-3.5" /> Add first category
            </button>
          </div>
        ) : topLevel.map((cat) => (
          <div key={cat.id}>
            <div className="flex items-center gap-3 px-4 py-3 hover:bg-[var(--color-surface)] transition-colors">
              <div className="w-8 h-8 rounded-lg bg-[rgba(237,108,0,.10)] flex items-center justify-center text-[#ED6C00]">
                <Folder className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <span className="font-semibold">{cat.name}</span>
                <span className="ml-2 text-xs text-[var(--color-ink-muted)]">/{cat.slug}</span>
                {cat.children_count > 0 && (
                  <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-[var(--color-surface-2)]">
                    {cat.children_count} sub-categories
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => setModal(cat)} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center text-[var(--color-ink-muted)] transition">
                  <Pencil className="w-3.5 h-3.5" />
                </button>
                <button onClick={() => handleDelete(cat)} className="w-8 h-8 rounded-lg hover:bg-[rgba(220,38,38,.08)] flex items-center justify-center text-[var(--color-ink-muted)] hover:text-[#DC2626] transition">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
            {children(cat.id).map((child) => (
              <div key={child.id} className="flex items-center gap-3 pl-12 pr-4 py-2.5 border-t border-[var(--color-line)] hover:bg-[var(--color-surface)] transition-colors">
                <div className="w-6 h-6 rounded bg-[var(--color-surface-2)] flex items-center justify-center">
                  <Folder className="w-3 h-3 text-[var(--color-ink-muted)]" />
                </div>
                <span className="flex-1 text-sm">{child.name}</span>
                <div className="flex items-center gap-1">
                  <button onClick={() => setModal(child)} className="w-7 h-7 rounded hover:bg-[var(--color-surface-2)] flex items-center justify-center text-[var(--color-ink-muted)]">
                    <Pencil className="w-3 h-3" />
                  </button>
                  <button onClick={() => handleDelete(child)} className="w-7 h-7 rounded hover:bg-[rgba(220,38,38,.08)] flex items-center justify-center text-[var(--color-ink-muted)] hover:text-[#DC2626]">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

      {modal && (
        <CategoryModal
          category={modal === "create" ? null : modal}
          companies={companies}
          allCategories={categories}
          onSave={handleSave}
          onClose={() => setModal(null)}
        />
      )}
      {toast && <Toast msg={toast.msg} ok={toast.ok} onDone={() => setToast(null)} />}
    </div>
  );
}
