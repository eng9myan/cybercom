"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Plus, Search, Package, Pencil, Trash2, X, ChevronDown,
  BarChart2, Tag, RefreshCw, AlertTriangle, CheckCircle2, Boxes,
} from "lucide-react";
import { api } from "@/lib/api";

const PRODUCT_TYPES = [
  { value: "STORABLE", label: "Storable" },
  { value: "CONSUMABLE", label: "Consumable" },
  { value: "SERVICE", label: "Service" },
  { value: "KIT", label: "Kit / Bundle" },
];

const EMPTY_FORM = {
  name: "", internal_ref: "", barcode: "", description: "",
  product_type: "STORABLE", sell_price: "0.0000", cost_price: "0.0000",
  track_stock: true, pos_available: true, min_stock_qty: "0.0000",
  category: "", unit: "", company: "", image_url: "",
};

function Toast({ msg, ok, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3500); return () => clearTimeout(t); }, [onDone]);
  return (
    <div className={`fixed bottom-6 right-6 z-[200] flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl text-white text-sm font-medium ${ok ? "bg-[#16A34A]" : "bg-[#DC2626]"}`}>
      {ok ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
      {msg}
    </div>
  );
}

function ProductModal({ product, companies, categories, units, onSave, onClose }) {
  const [form, setForm] = useState(product ? { ...product } : { ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);
  const isEdit = Boolean(product);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (isEdit) {
        await api.patch(`/api/v1/catalog/products/${product.id}/`, form);
      } else {
        await api.post("/api/v1/catalog/products/", form);
      }
      onSave(isEdit ? "Product updated." : "Product created.");
    } catch (err) {
      onSave(null, err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-[var(--color-line)] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-line)]">
          <h2 className="font-heading font-bold text-lg">{isEdit ? "Edit Product" : "New Product"}</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="cy-label">Name *</label>
              <input required className="cy-input" value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="e.g. Espresso" />
            </div>
            <div>
              <label className="cy-label">SKU / Internal Ref</label>
              <input className="cy-input" value={form.internal_ref} onChange={(e) => set("internal_ref", e.target.value)} placeholder="ESP-001" />
            </div>
            <div>
              <label className="cy-label">Barcode</label>
              <input className="cy-input" value={form.barcode} onChange={(e) => set("barcode", e.target.value)} placeholder="6291041500213" />
            </div>
            <div>
              <label className="cy-label">Type</label>
              <select className="cy-input" value={form.product_type} onChange={(e) => set("product_type", e.target.value)}>
                {PRODUCT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">Company *</label>
              <select required className="cy-input" value={form.company} onChange={(e) => set("company", e.target.value)}>
                <option value="">— select —</option>
                {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">Category</label>
              <select className="cy-input" value={form.category} onChange={(e) => set("category", e.target.value)}>
                <option value="">— none —</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">Unit of Measure</label>
              <select className="cy-input" value={form.unit} onChange={(e) => set("unit", e.target.value)}>
                <option value="">— none —</option>
                {units.map((u) => <option key={u.id} value={u.id}>{u.name} ({u.abbreviation})</option>)}
              </select>
            </div>
            <div>
              <label className="cy-label">Sell Price</label>
              <input type="number" step="0.0001" min="0" className="cy-input" value={form.sell_price} onChange={(e) => set("sell_price", e.target.value)} />
            </div>
            <div>
              <label className="cy-label">Cost Price</label>
              <input type="number" step="0.0001" min="0" className="cy-input" value={form.cost_price} onChange={(e) => set("cost_price", e.target.value)} />
            </div>
            <div>
              <label className="cy-label">Min Stock (reorder point)</label>
              <input type="number" step="0.0001" min="0" className="cy-input" value={form.min_stock_qty} onChange={(e) => set("min_stock_qty", e.target.value)} />
            </div>
            <div>
              <label className="cy-label">Image URL</label>
              <input className="cy-input" value={form.image_url || ""} onChange={(e) => set("image_url", e.target.value)} placeholder="https://…" />
            </div>
            <div className="col-span-2">
              <label className="cy-label">Description</label>
              <textarea rows={2} className="cy-input" value={form.description} onChange={(e) => set("description", e.target.value)} />
            </div>
            <div className="flex items-center gap-3">
              <input type="checkbox" id="track_stock" checked={form.track_stock} onChange={(e) => set("track_stock", e.target.checked)} className="w-4 h-4 accent-[#ED6C00]" />
              <label htmlFor="track_stock" className="text-sm font-medium">Track stock</label>
            </div>
            <div className="flex items-center gap-3">
              <input type="checkbox" id="pos_available" checked={form.pos_available} onChange={(e) => set("pos_available", e.target.checked)} className="w-4 h-4 accent-[#ED6C00]" />
              <label htmlFor="pos_available" className="text-sm font-medium">Show on POS</label>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="cy-btn cy-btn-ghost">Cancel</button>
            <button type="submit" disabled={saving} className="cy-btn cy-btn-primary">
              {saving ? "Saving…" : isEdit ? "Save Changes" : "Create Product"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function BomModal({ product, allProducts, onClose, onToast }) {
  const [components, setComponents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [componentProduct, setComponentProduct] = useState("");
  const [qty, setQty] = useState("1");
  const [saving, setSaving] = useState(false);

  const candidates = allProducts.filter((p) => p.id !== product.id);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get(`/api/v1/catalog/products/${product.id}/bom/`);
      setComponents(Array.isArray(data) ? data : []);
    } catch (err) {
      onToast(null, err.message);
    } finally {
      setLoading(false);
    }
  }, [product.id]);

  useEffect(() => { load(); }, [load]);

  const addComponent = async (e) => {
    e.preventDefault();
    if (!componentProduct) return;
    setSaving(true);
    try {
      await api.post(`/api/v1/catalog/products/${product.id}/bom/`, {
        component_product: componentProduct, quantity_per_unit: qty,
      });
      setComponentProduct(""); setQty("1");
      load();
    } catch (err) {
      onToast(null, err.message);
    } finally { setSaving(false); }
  };

  const removeComponent = async (id) => {
    try {
      await api.del(`/api/v1/catalog/kit-components/${id}/`);
      setComponents((c) => c.filter((x) => x.id !== id));
    } catch (err) {
      onToast(null, err.message);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-[var(--color-line)] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-line)]">
          <h2 className="font-heading font-bold text-lg flex items-center gap-2">
            <Boxes className="w-5 h-5 text-[#ED6C00]" /> Bill of Materials — {product.name}
          </h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
          <p className="text-sm text-[var(--color-ink-muted)]">
            Selling one unit of <strong>{product.name}</strong> auto-deducts these component quantities from stock on payment.
          </p>

          <div className="space-y-2">
            {loading ? (
              <div className="text-center py-6 text-sm text-[var(--color-ink-muted)]">Loading…</div>
            ) : components.length === 0 ? (
              <div className="text-center py-6 text-sm text-[var(--color-ink-muted)] border border-dashed border-[var(--color-line)] rounded-lg">
                No components yet — add raw materials below.
              </div>
            ) : components.map((c) => (
              <div key={c.id} className="flex items-center justify-between bg-[var(--color-surface)] border border-[var(--color-line)] rounded-lg px-3 py-2.5">
                <div>
                  <div className="text-sm font-semibold">{c.component_product_name}</div>
                  <div className="text-xs text-[var(--color-ink-muted)] font-mono">{c.component_product_ref}</div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold tabular-nums">{parseFloat(c.quantity_per_unit)} / unit</span>
                  <button onClick={() => removeComponent(c.id)} className="text-[var(--color-ink-muted)] hover:text-[#DC2626]">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={addComponent} className="flex gap-2 items-end border-t border-[var(--color-line)] pt-4">
            <div className="flex-1">
              <label className="cy-label">Component Product</label>
              <select required className="cy-input" value={componentProduct} onChange={(e) => setComponentProduct(e.target.value)}>
                <option value="">— select —</option>
                {candidates.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div className="w-28">
              <label className="cy-label">Qty / unit</label>
              <input type="number" step="0.0001" min="0.0001" required className="cy-input" value={qty} onChange={(e) => setQty(e.target.value)} />
            </div>
            <button type="submit" disabled={saving} className="cy-btn cy-btn-primary !py-2.5">
              <Plus className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function CatalogPage() {
  const [products, setProducts] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [modal, setModal] = useState(null); // null | 'create' | product object
  const [bomModal, setBomModal] = useState(null); // null | product object
  const [toast, setToast] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [prods, comps, cats, uts] = await Promise.all([
        api.get("/api/v1/catalog/products/"),
        api.get("/api/v1/tenants/companies/"),
        api.get("/api/v1/catalog/categories/"),
        api.get("/api/v1/catalog/units/"),
      ]);
      setProducts(Array.isArray(prods) ? prods : prods.results || []);
      setCompanies(Array.isArray(comps) ? comps : comps.results || []);
      setCategories(Array.isArray(cats) ? cats : cats.results || []);
      setUnits(Array.isArray(uts) ? uts : uts.results || []);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSave = (successMsg, errMsg) => {
    if (successMsg) {
      setModal(null);
      setToast({ msg: successMsg, ok: true });
      load();
    } else {
      setToast({ msg: errMsg, ok: false });
    }
  };

  const handleDelete = async (product) => {
    if (!window.confirm(`Delete "${product.name}"? This cannot be undone.`)) return;
    setDeleting(product.id);
    try {
      await api.patch(`/api/v1/catalog/products/${product.id}/`, { is_deleted: true });
      setToast({ msg: "Product deleted.", ok: true });
      load();
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    } finally {
      setDeleting(null);
    }
  };

  const filtered = products.filter((p) => {
    const matchSearch =
      !search ||
      p.name?.toLowerCase().includes(search.toLowerCase()) ||
      p.internal_ref?.toLowerCase().includes(search.toLowerCase()) ||
      p.barcode?.includes(search);
    const matchType = typeFilter === "ALL" || p.product_type === typeFilter;
    return matchSearch && matchType;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-heading font-bold text-2xl">Product Catalog</h2>
          <p className="text-sm text-[var(--color-ink-muted)] mt-0.5">
            {products.length} product{products.length !== 1 ? "s" : ""} · persisted in database
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={load} className="cy-btn cy-btn-ghost !py-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setModal("create")} className="cy-btn cy-btn-primary">
            <Plus className="w-4 h-4" /> New Product
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-ink-muted)]" />
          <input
            className="cy-input pl-9"
            placeholder="Search by name, SKU or barcode…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select className="cy-input w-auto" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="ALL">All Types</option>
          {PRODUCT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="cy-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-line)] bg-[var(--color-surface)]">
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Product</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide hidden md:table-cell">SKU</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide hidden lg:table-cell">Category</th>
                <th className="text-left px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Type</th>
                <th className="text-right px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide">Sell Price</th>
                <th className="text-right px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide hidden md:table-cell">Cost</th>
                <th className="text-center px-4 py-3 font-semibold text-[var(--color-ink-muted)] text-xs uppercase tracking-wide hidden sm:table-cell">POS</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-line)]">
              {loading ? (
                <tr><td colSpan={8} className="text-center py-16 text-[var(--color-ink-muted)]">Loading…</td></tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-16">
                    <Package className="w-10 h-10 mx-auto mb-3 text-[var(--color-ink-muted)] opacity-40" />
                    <p className="text-[var(--color-ink-muted)]">No products found.</p>
                    <button onClick={() => setModal("create")} className="mt-3 cy-btn cy-btn-primary !py-2 !text-xs">
                      <Plus className="w-3.5 h-3.5" /> Add first product
                    </button>
                  </td>
                </tr>
              ) : filtered.map((p) => (
                <tr key={p.id} className="hover:bg-[var(--color-surface)] transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      {p.image_url ? (
                        <img src={p.image_url} alt="" className="w-9 h-9 rounded-lg object-cover bg-[var(--color-surface-2)]" />
                      ) : (
                        <div className="w-9 h-9 rounded-lg bg-[rgba(237,108,0,.10)] flex items-center justify-center">
                          <Package className="w-4 h-4 text-[#ED6C00]" />
                        </div>
                      )}
                      <span className="font-semibold">{p.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-[var(--color-ink-muted)] hidden md:table-cell font-mono text-xs">{p.internal_ref || "—"}</td>
                  <td className="px-4 py-3 hidden lg:table-cell">
                    {p.category_name ? (
                      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-[var(--color-surface-2)]">
                        <Tag className="w-3 h-3" /> {p.category_name}
                      </span>
                    ) : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--color-surface-2)] font-medium">{p.product_type}</span>
                  </td>
                  <td className="px-4 py-3 text-right font-semibold tabular-nums">{parseFloat(p.sell_price).toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-[var(--color-ink-muted)] tabular-nums hidden md:table-cell">{parseFloat(p.cost_price).toFixed(2)}</td>
                  <td className="px-4 py-3 text-center hidden sm:table-cell">
                    <span className={`inline-block w-2 h-2 rounded-full ${p.pos_available ? "bg-[#16A34A]" : "bg-[var(--color-line)]"}`} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      {p.product_type === "KIT" && (
                        <button
                          onClick={() => setBomModal(p)}
                          title="Bill of Materials"
                          className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center text-[var(--color-ink-muted)] hover:text-[#ED6C00] transition"
                        >
                          <Boxes className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => setModal(p)}
                        className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center text-[var(--color-ink-muted)] hover:text-[var(--color-ink)] transition"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(p)}
                        disabled={deleting === p.id}
                        className="w-8 h-8 rounded-lg hover:bg-[rgba(220,38,38,.08)] flex items-center justify-center text-[var(--color-ink-muted)] hover:text-[#DC2626] transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stats row */}
      {products.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Total Products", value: products.length, icon: Package },
            { label: "POS-visible", value: products.filter((p) => p.pos_available).length, icon: BarChart2 },
            { label: "Tracked Stock", value: products.filter((p) => p.track_stock).length, icon: Tag },
            { label: "Categories", value: categories.length, icon: ChevronDown },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="cy-card p-4 flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[rgba(237,108,0,.10)] flex items-center justify-center text-[#ED6C00]">
                <Icon className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs text-[var(--color-ink-muted)]">{label}</div>
                <div className="text-xl font-heading font-bold tabular-nums">{value}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modals */}
      {modal && (
        <ProductModal
          product={modal === "create" ? null : modal}
          companies={companies}
          categories={categories}
          units={units}
          onSave={handleSave}
          onClose={() => setModal(null)}
        />
      )}
      {bomModal && (
        <BomModal
          product={bomModal}
          allProducts={products}
          onClose={() => setBomModal(null)}
          onToast={(ok, err) => setToast(ok ? { msg: ok, ok: true } : { msg: err, ok: false })}
        />
      )}
      {toast && <Toast msg={toast.msg} ok={toast.ok} onDone={() => setToast(null)} />}
    </div>
  );
}
