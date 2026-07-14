"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import {
  Plus, Minus, Trash2, ShoppingCart, RefreshCw,
  CheckCircle2, AlertTriangle, X, CreditCard, Banknote,
  Smartphone, Search, Tag,
} from "lucide-react";
import { api } from "@/lib/api";

// ─── Toast ─────────────────────────────────────────────────────────────────
function Toast({ msg, ok, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 4000); return () => clearTimeout(t); }, [onDone]);
  return (
    <div className={`fixed bottom-6 right-6 z-[200] flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl text-white text-sm font-medium ${ok ? "bg-[#16A34A]" : "bg-[#DC2626]"}`}>
      {ok ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
      {msg}
    </div>
  );
}

// ─── Payment modal ──────────────────────────────────────────────────────────
const PAY_METHODS = [
  { value: "CASH", label: "Cash", icon: Banknote },
  { value: "CARD", label: "Card", icon: CreditCard },
  { value: "MOBILE", label: "Mobile", icon: Smartphone },
];

function PaymentModal({ total, session, onPaid, onClose }) {
  const [method, setMethod] = useState("CASH");
  const [tendered, setTendered] = useState(String(Math.ceil(total * 100) / 100));
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  const change = Math.max(0, parseFloat(tendered || 0) - total);

  const submit = async () => {
    if (parseFloat(tendered || 0) < total) return;
    setSaving(true);
    try {
      await onPaid({ method, amount: tendered, change_given: change.toFixed(4), notes: note });
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-2xl border border-[var(--color-line)] overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--color-line)]">
          <h2 className="font-heading font-bold text-lg">Collect Payment</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--color-surface-2)] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 space-y-4">
          {/* Total due */}
          <div className="text-center py-2">
            <div className="text-xs uppercase tracking-widest text-[var(--color-ink-muted)] mb-1">Total Due</div>
            <div className="font-heading font-black text-4xl text-[#ED6C00]">{total.toFixed(2)}</div>
          </div>

          {/* Method selector */}
          <div className="grid grid-cols-3 gap-2">
            {PAY_METHODS.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                onClick={() => setMethod(value)}
                className={`flex flex-col items-center gap-1.5 py-3 rounded-xl border font-semibold text-xs transition-colors ${
                  method === value
                    ? "bg-[rgba(237,108,0,.10)] border-[#ED6C00] text-[#ED6C00]"
                    : "bg-white border-[var(--color-line)] text-[var(--color-ink-soft)] hover:border-[var(--color-ink)]"
                }`}
              >
                <Icon className="w-5 h-5" />
                {label}
              </button>
            ))}
          </div>

          {/* Amount tendered (cash only) */}
          {method === "CASH" && (
            <div>
              <label className="cy-label">Amount Tendered</label>
              <input
                type="number"
                step="0.01"
                min={total}
                className="cy-input text-xl font-bold"
                value={tendered}
                onChange={e => setTendered(e.target.value)}
                autoFocus
              />
              {change > 0 && (
                <div className="mt-2 text-center text-sm font-semibold text-[#16A34A]">
                  Change: {change.toFixed(2)}
                </div>
              )}
            </div>
          )}

          {method !== "CASH" && (
            <div>
              <label className="cy-label">Reference / Auth Code</label>
              <input className="cy-input" value={note} onChange={e => setNote(e.target.value)} placeholder="e.g. TXN-1234" />
            </div>
          )}

          <button
            onClick={submit}
            disabled={saving || parseFloat(tendered || 0) < total}
            className="cy-btn cy-btn-primary w-full justify-center text-base"
          >
            {saving ? "Processing…" : `Charge ${total.toFixed(2)}`}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Receipt panel ──────────────────────────────────────────────────────────
function ReceiptPanel({ order, receipt, onNewOrder }) {
  return (
    <div className="flex flex-col items-center justify-center h-full space-y-4 py-8 px-4 text-center">
      <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center">
        <CheckCircle2 className="w-8 h-8 text-[#16A34A]" />
      </div>
      <div>
        <div className="font-heading font-bold text-xl">Payment Complete</div>
        <div className="text-sm text-[var(--color-ink-muted)] mt-1">{order.order_number}</div>
      </div>
      {receipt && (
        <div className="w-full max-w-xs bg-[var(--color-surface)] rounded-xl p-4 text-left text-sm">
          <div className="flex justify-between"><span className="text-[var(--color-ink-muted)]">Receipt #</span><span className="font-mono font-semibold">{receipt.receipt_number}</span></div>
          <div className="flex justify-between mt-1"><span className="text-[var(--color-ink-muted)]">Subtotal</span><span>{parseFloat(order.subtotal).toFixed(2)}</span></div>
          <div className="flex justify-between mt-1"><span className="text-[var(--color-ink-muted)]">Tax</span><span>{parseFloat(order.tax_amount).toFixed(2)}</span></div>
          <div className="flex justify-between mt-2 font-bold text-base border-t border-[var(--color-line)] pt-2"><span>Total</span><span className="text-[#ED6C00]">{parseFloat(order.total).toFixed(2)}</span></div>
        </div>
      )}
      <button onClick={onNewOrder} className="cy-btn cy-btn-primary">
        <Plus className="w-4 h-4" /> New Order
      </button>
    </div>
  );
}

// ─── Main POS page ──────────────────────────────────────────────────────────
export default function PosPage() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [catFilter, setCatFilter] = useState("ALL");
  const [cart, setCart] = useState([]); // [{product, qty}]
  const [discount, setDiscount] = useState("0");
  const [customer, setCustomer] = useState({ name: "", phone: "" });
  const [payModal, setPayModal] = useState(false);
  const [completedOrder, setCompletedOrder] = useState(null);
  const [toast, setToast] = useState(null);

  const activeSession = sessions.find(s => s.status === "OPEN") || null;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [prods, cats, sess] = await Promise.all([
        api.get("/api/v1/catalog/products/?pos_available=true"),
        api.get("/api/v1/catalog/categories/"),
        api.get("/api/v1/pos/sessions/?status=OPEN"),
      ]);
      setProducts(Array.isArray(prods) ? prods : prods.results || []);
      setCategories(Array.isArray(cats) ? cats : cats.results || []);
      setSessions(Array.isArray(sess) ? sess : sess.results || []);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Cart logic
  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(i => i.product.id === product.id);
      if (existing) return prev.map(i => i.product.id === product.id ? { ...i, qty: i.qty + 1 } : i);
      return [...prev, { product, qty: 1 }];
    });
  };

  const changeQty = (pid, delta) => {
    setCart(prev => prev
      .map(i => i.product.id === pid ? { ...i, qty: Math.max(0, i.qty + delta) } : i)
      .filter(i => i.qty > 0)
    );
  };

  const removeFromCart = (pid) => setCart(prev => prev.filter(i => i.product.id !== pid));

  // Totals
  const totals = useMemo(() => {
    const subtotal = cart.reduce((s, i) => s + i.qty * parseFloat(i.product.sell_price), 0);
    const tax = cart.reduce((s, i) => {
      const rate = parseFloat(i.product.tax_class_rate || 0);
      return s + i.qty * parseFloat(i.product.sell_price) * rate;
    }, 0);
    const disc = parseFloat(discount) || 0;
    return { subtotal, tax, discount: disc, total: subtotal + tax - disc };
  }, [cart, discount]);

  // Filtered products
  const filtered = useMemo(() => products.filter(p => {
    const matchCat = catFilter === "ALL" || String(p.category) === catFilter;
    const matchSearch = !search || p.name.toLowerCase().includes(search.toLowerCase()) ||
      (p.internal_ref || "").toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  }), [products, catFilter, search]);

  // Checkout
  const handlePay = async ({ method, amount, change_given, notes }) => {
    try {
      // Build lines_input
      const lines_input = cart.map(i => ({
        product: i.product.id,
        quantity: String(i.qty),
      }));

      // Get company from active session
      const companyId = activeSession?.company;

      // Create order + lines in one POST
      const orderRes = await api.post("/api/v1/pos/orders/", {
        company: companyId,
        session: activeSession?.id || null,
        customer_name: customer.name,
        customer_phone: customer.phone,
        discount_amount: discount || "0",
        lines_input,
      });

      // Pay
      const paidRes = await api.post(`/api/v1/pos/orders/${orderRes.id}/pay/`, {
        method,
        amount,
        change_given,
        reference: notes || "",
      });

      setPayModal(false);
      setCompletedOrder(paidRes);
    } catch (err) {
      setToast({ msg: err.message, ok: false });
    }
  };

  const newOrder = () => {
    setCart([]);
    setDiscount("0");
    setCustomer({ name: "", phone: "" });
    setCompletedOrder(null);
  };

  if (completedOrder) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="cy-card p-8 w-full max-w-md">
          <ReceiptPanel
            order={completedOrder}
            receipt={completedOrder.receipt}
            onNewOrder={newOrder}
          />
        </div>
        {toast && <Toast msg={toast.msg} ok={toast.ok} onDone={() => setToast(null)} />}
      </div>
    );
  }

  return (
    <div className="flex gap-4 h-[calc(100vh-8rem)] min-h-0">
      {/* ── Left: Product grid ── */}
      <div className="flex-1 flex flex-col min-w-0 space-y-3">
        {/* Search + refresh */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-ink-muted)]" />
            <input
              placeholder="Search products…"
              className="cy-input pl-9"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <button onClick={load} className="cy-btn cy-btn-ghost !py-2 !px-3">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {/* No session warning */}
        {!loading && !activeSession && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-sm">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            No open session. <a href="/app/pos/sessions" className="font-semibold underline">Open a session</a> to start selling.
          </div>
        )}

        {/* Category pills */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setCatFilter("ALL")}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
              catFilter === "ALL"
                ? "bg-[#333] text-white border-transparent"
                : "bg-white border-[var(--color-line)] text-[var(--color-ink-soft)] hover:border-[var(--color-ink)]"
            }`}
          >
            All
          </button>
          {categories.map(c => (
            <button
              key={c.id}
              onClick={() => setCatFilter(String(c.id))}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
                catFilter === String(c.id)
                  ? "bg-[#333] text-white border-transparent"
                  : "bg-white border-[var(--color-line)] text-[var(--color-ink-soft)] hover:border-[var(--color-ink)]"
              }`}
            >
              {c.name}
            </button>
          ))}
        </div>

        {/* Product grid */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center h-40 text-[var(--color-ink-muted)]">Loading products…</div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-[var(--color-ink-muted)]">
              <Tag className="w-8 h-8 mb-2 opacity-30" />
              <p className="text-sm">No products match.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 pb-4">
              {filtered.map(p => {
                const inCart = cart.find(i => i.product.id === p.id);
                return (
                  <button
                    key={p.id}
                    onClick={() => addToCart(p)}
                    className={`relative group p-3 rounded-2xl border text-left transition-all hover:shadow-md hover:-translate-y-0.5 ${
                      inCart
                        ? "border-[#ED6C00] bg-[rgba(237,108,0,.06)]"
                        : "border-[var(--color-line)] bg-white"
                    }`}
                  >
                    {inCart && (
                      <span className="absolute top-2 right-2 w-5 h-5 rounded-full bg-[#ED6C00] text-white text-[10px] font-bold flex items-center justify-center">
                        {inCart.qty}
                      </span>
                    )}
                    {p.image_url && (
                      <img src={p.image_url} alt={p.name} className="w-full h-20 object-cover rounded-lg mb-2" />
                    )}
                    {!p.image_url && (
                      <div className="w-full h-12 rounded-lg mb-2 bg-[var(--color-surface-2)] flex items-center justify-center">
                        <Tag className="w-5 h-5 text-[var(--color-ink-muted)]" />
                      </div>
                    )}
                    <div className="text-xs font-semibold leading-tight truncate">{p.name}</div>
                    {p.internal_ref && (
                      <div className="text-[10px] text-[var(--color-ink-muted)] mt-0.5 font-mono">{p.internal_ref}</div>
                    )}
                    <div className="mt-1 text-sm font-bold text-[#ED6C00]">
                      {parseFloat(p.sell_price).toFixed(2)}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* ── Right: Cart ── */}
      <div className="w-80 xl:w-96 flex flex-col bg-white border border-[var(--color-line)] rounded-2xl shadow-sm overflow-hidden">
        {/* Cart header */}
        <div className="px-4 py-3 border-b border-[var(--color-line)] flex items-center justify-between">
          <div className="flex items-center gap-2 font-heading font-bold">
            <ShoppingCart className="w-4 h-4 text-[#ED6C00]" />
            Order
          </div>
          {cart.length > 0 && (
            <button onClick={() => setCart([])} className="text-xs text-[var(--color-ink-muted)] hover:text-[#DC2626] transition-colors">
              Clear
            </button>
          )}
        </div>

        {/* Customer (optional) */}
        <div className="px-4 pt-3 pb-2 border-b border-[var(--color-line)] grid grid-cols-2 gap-2">
          <input
            placeholder="Customer name"
            className="cy-input !text-xs !py-1.5"
            value={customer.name}
            onChange={e => setCustomer(c => ({ ...c, name: e.target.value }))}
          />
          <input
            placeholder="Phone"
            className="cy-input !text-xs !py-1.5"
            value={customer.phone}
            onChange={e => setCustomer(c => ({ ...c, phone: e.target.value }))}
          />
        </div>

        {/* Cart lines */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
          {cart.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-[var(--color-ink-muted)]">
              <ShoppingCart className="w-8 h-8 mb-2 opacity-20" />
              <p className="text-sm">Cart is empty.</p>
            </div>
          ) : cart.map(({ product: p, qty }) => (
            <div key={p.id} className="flex items-center gap-2 p-2 rounded-xl bg-[var(--color-surface)] border border-[var(--color-line)]">
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold truncate">{p.name}</div>
                <div className="text-xs text-[var(--color-ink-muted)]">
                  {parseFloat(p.sell_price).toFixed(2)} ea
                </div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button onClick={() => changeQty(p.id, -1)} className="w-6 h-6 rounded-md bg-white border border-[var(--color-line)] flex items-center justify-center hover:border-[#ED6C00] transition-colors">
                  <Minus className="w-3 h-3" />
                </button>
                <span className="w-6 text-center text-xs font-bold">{qty}</span>
                <button onClick={() => changeQty(p.id, 1)} className="w-6 h-6 rounded-md bg-white border border-[var(--color-line)] flex items-center justify-center hover:border-[#ED6C00] transition-colors">
                  <Plus className="w-3 h-3" />
                </button>
                <button onClick={() => removeFromCart(p.id)} className="w-6 h-6 rounded-md hover:bg-red-50 hover:text-[#DC2626] text-[var(--color-ink-muted)] flex items-center justify-center transition-colors ml-1">
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
              <div className="w-16 text-right text-xs font-bold shrink-0">
                {(qty * parseFloat(p.sell_price)).toFixed(2)}
              </div>
            </div>
          ))}
        </div>

        {/* Totals + discount */}
        <div className="border-t border-[var(--color-line)] px-4 py-3 space-y-2">
          <div className="flex items-center gap-2">
            <label className="text-xs text-[var(--color-ink-muted)] shrink-0">Discount</label>
            <input
              type="number" step="0.01" min="0"
              className="cy-input !py-1 !text-xs flex-1"
              value={discount}
              onChange={e => setDiscount(e.target.value)}
            />
          </div>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between text-[var(--color-ink-muted)]">
              <span>Subtotal</span><span>{totals.subtotal.toFixed(2)}</span>
            </div>
            {totals.tax > 0 && (
              <div className="flex justify-between text-[var(--color-ink-muted)]">
                <span>Tax</span><span>{totals.tax.toFixed(2)}</span>
              </div>
            )}
            {totals.discount > 0 && (
              <div className="flex justify-between text-[#16A34A]">
                <span>Discount</span><span>-{totals.discount.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between font-heading font-bold text-base pt-1 border-t border-[var(--color-line)]">
              <span>Total</span>
              <span className="text-[#ED6C00]">{Math.max(0, totals.total).toFixed(2)}</span>
            </div>
          </div>

          <button
            onClick={() => setPayModal(true)}
            disabled={cart.length === 0 || !activeSession}
            className="cy-btn cy-btn-primary w-full justify-center text-base mt-1 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <CreditCard className="w-4 h-4" /> Charge {Math.max(0, totals.total).toFixed(2)}
          </button>
          {!activeSession && cart.length > 0 && (
            <p className="text-xs text-center text-amber-700">Open a session to charge.</p>
          )}
        </div>
      </div>

      {/* Modals */}
      {payModal && (
        <PaymentModal
          total={Math.max(0, totals.total)}
          session={activeSession}
          onPaid={handlePay}
          onClose={() => setPayModal(false)}
        />
      )}
      {toast && <Toast msg={toast.msg} ok={toast.ok} onDone={() => setToast(null)} />}
    </div>
  );
}
