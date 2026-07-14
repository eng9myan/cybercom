"use client";

import { useState, useEffect } from "react";
import { Plus, Search, Eye, SlidersHorizontal, RefreshCw, Truck, FileCheck, CheckCircle2, ChevronRight, AlertCircle, ShoppingBag, Trash2 } from "lucide-react";

export default function SalesOrdersPage() {
  const [orders, setOrders] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [branches, setBranches] = useState([]);
  const [quotations, setQuotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Search & Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Modals / Drawer
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Form state
  const [newOrder, setNewOrder] = useState({
    order_number: "",
    quotation: "",
    company: "",
    branch: "",
    customer_name: "",
    status: "CONFIRMED",
    fulfillment_status: "UNFULFILLED",
    invoice_status: "UNINVOICED",
    delivery_status: "PENDING",
    lines: [{ item_name: "", qty: "1", unit_price: "0.00" }]
  });

  const fetchOrderData = async () => {
    setLoading(true);
    setError("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const oRes = await fetch("/api/v1/sales/orders/", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
      });
      if (!oRes.ok) throw new Error("Failed to load orders");
      const oData = await oRes.json();
      setOrders(oData);

      const compRes = await fetch("/api/v1/tenants/companies/", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
      });
      if (compRes.ok) {
        const compData = await compRes.json();
        setCompanies(compData);
        if (compData.length > 0 && !newOrder.company) {
          setNewOrder(prev => ({ ...prev, company: compData[0].id }));
        }
      }

      const brRes = await fetch("/api/v1/tenants/branches/", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
      });
      if (brRes.ok) {
        const brData = await brRes.json();
        setBranches(brData);
        if (brData.length > 0 && !newOrder.branch) {
          setNewOrder(prev => ({ ...prev, branch: brData[0].id }));
        }
      }

      const qRes = await fetch("/api/v1/sales/quotations/", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
      });
      if (qRes.ok) {
        setQuotations(await qRes.json());
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrder = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    if (newOrder.lines.some(l => !l.item_name || parseFloat(l.qty) <= 0 || parseFloat(l.unit_price) < 0)) {
      setError("Please ensure all lines contain valid item names, quantities (>0), and prices (>=0).");
      return;
    }

    try {
      const payload = {
        ...newOrder,
        quotation: newOrder.quotation || null,
        lines: newOrder.lines.map(l => ({
          item_name: l.item_name,
          qty: parseFloat(l.qty),
          unit_price: parseFloat(l.unit_price)
        }))
      };

      const response = await fetch("/api/v1/sales/orders/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        setSuccess("Sales Order created and logged successfully!");
        setIsCreateOpen(false);
        setNewOrder({
          order_number: "",
          quotation: "",
          company: companies[0]?.id || "",
          branch: branches[0]?.id || "",
          customer_name: "",
          status: "CONFIRMED",
          fulfillment_status: "UNFULFILLED",
          invoice_status: "UNINVOICED",
          delivery_status: "PENDING",
          lines: [{ item_name: "", qty: "1", unit_price: "0.00" }]
        });
        fetchOrderData();
      } else {
        const data = await response.json();
        throw new Error(data.detail || JSON.stringify(data) || "Error creating order.");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleUpdateOrderStatus = async (orderId, updates) => {
    setError("");
    setSuccess("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    const order = orders.find(o => o.id === orderId);

    try {
      const response = await fetch(`/api/v1/sales/orders/${orderId}/`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
        body: JSON.stringify({
          ...order,
          ...updates
        }),
      });

      if (response.ok) {
        const updated = await response.json();
        setSuccess(`Order updated successfully.`);
        setSelectedOrder(updated);
        // Refresh orders list
        const refreshedRes = await fetch("/api/v1/sales/orders/", {
          headers: {
            "Authorization": `Bearer ${token}`,
            "X-Tenant-ID": tenantId,
          },
        });
        if (refreshedRes.ok) {
          setOrders(await refreshedRes.json());
        }
      } else {
        throw new Error("Failed to update order details.");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleApplyQuoteReference = (qId) => {
    const q = quotations.find(item => item.id === qId);
    if (!q) return;

    setNewOrder(prev => ({
      ...prev,
      quotation: qId,
      customer_name: q.customer_name,
      company: q.company,
      branch: q.branch,
      lines: q.lines.map(line => ({
        item_name: line.item_name,
        qty: line.qty,
        unit_price: line.unit_price
      }))
    }));
  };

  const addLine = () => {
    setNewOrder({
      ...newOrder,
      lines: [...newOrder.lines, { item_name: "", qty: "1", unit_price: "0.00" }],
    });
  };

  const removeLine = (index) => {
    if (newOrder.lines.length === 1) return;
    const nextLines = [...newOrder.lines];
    nextLines.splice(index, 1);
    setNewOrder({ ...newOrder, lines: nextLines });
  };

  const updateLine = (index, field, value) => {
    const nextLines = [...newOrder.lines];
    nextLines[index][field] = value;
    setNewOrder({ ...newOrder, lines: nextLines });
  };

  useEffect(() => {
    fetchOrderData();
  }, []);

  const filteredOrders = orders.filter((o) => {
    const matchesSearch =
      o.order_number.toLowerCase().includes(search.toLowerCase()) ||
      o.customer_name.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === "ALL" || o.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 text-[var(--color-ink)] animate-fade">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">Sales Orders</h1>
          <p className="text-xs text-[var(--color-ink-muted)]">Fulfill orders, track deliveries, monitor invoice pipelines, and trigger status updates.</p>
        </div>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center gap-2 bg-[#ED6C00] hover:bg-[#ED6C00] transition text-white px-4 py-2.5 rounded-xl text-xs font-bold shadow-lg shadow-orange-950/20"
        >
          <Plus className="w-4 h-4" />
          New Sales Order
        </button>
      </div>

      {error && (
        <div className="bg-red-950/40 border border-red-800 text-red-400 p-4 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="bg-emerald-950/40 border border-emerald-800 text-emerald-400 p-4 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* Filters and search */}
      <div className="bg-white border border-[var(--color-line)] p-4 rounded-2xl flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-[var(--color-ink-muted)] absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by order # or customer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-white border border-[var(--color-line)] rounded-xl py-2 pl-10 pr-4 text-xs text-[var(--color-ink)] placeholder-[var(--color-ink-muted)] focus:outline-none focus:border-[var(--color-ink)] font-medium"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-3.5 h-3.5 text-[var(--color-ink-muted)]" />
            <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-wider font-bold">Status:</span>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none focus:border-[var(--color-ink)] font-bold"
          >
            <option value="ALL">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="PROCESSING">Processing</option>
            <option value="DELIVERED">Delivered</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>

          <button
            onClick={fetchOrderData}
            className="w-9 h-9 bg-white border border-[var(--color-line)] rounded-xl flex items-center justify-center text-[var(--color-ink-muted)] hover:text-white transition hover:bg-white"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Orders list */}
      {loading ? (
        <div className="flex justify-center items-center h-60">
          <div className="w-8 h-8 border-4 border-[var(--color-line)] border-t-orange-500 rounded-full animate-spin"></div>
        </div>
      ) : filteredOrders.length === 0 ? (
        <div className="bg-white border border-[var(--color-line)] p-12 rounded-2xl text-center">
          <p className="text-xs text-[var(--color-ink-muted)] font-medium">No sales orders found.</p>
        </div>
      ) : (
        <div className="bg-white border border-[var(--color-line)] rounded-2xl overflow-hidden shadow">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[var(--color-line)] text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)] bg-white">
                <th className="px-6 py-4 font-bold">Order Number</th>
                <th className="px-6 py-4 font-bold">Customer Name</th>
                <th className="px-6 py-4 font-bold">Fulfillment</th>
                <th className="px-6 py-4 font-bold">Delivery</th>
                <th className="px-6 py-4 font-bold">Invoice</th>
                <th className="px-6 py-4 font-bold">Total Amount</th>
                <th className="px-6 py-4 font-bold">Status</th>
                <th className="px-6 py-4 font-bold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-850 text-xs">
              {filteredOrders.map((o) => {
                const statusColors = {
                  DRAFT: "bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] border-[var(--color-ink)]",
                  CONFIRMED: "bg-blue-950/40 text-blue-400 border-blue-900/30",
                  PROCESSING: "bg-amber-950/40 text-amber-400 border-amber-900/30",
                  DELIVERED: "bg-emerald-950/40 text-emerald-450 border-emerald-900/30",
                  COMPLETED: "bg-teal-950/40 text-teal-400 border-teal-900/30",
                  CANCELLED: "bg-red-950/40 text-red-400 border-red-900/30",
                };

                return (
                  <tr key={o.id} className="hover:bg-white transition">
                    <td className="px-6 py-4 font-bold font-mono text-[var(--color-ink-soft)]">{o.order_number}</td>
                    <td className="px-6 py-4 text-[var(--color-ink-soft)] font-medium">{o.customer_name}</td>
                    <td className="px-6 py-4 text-[10px] font-bold text-[var(--color-ink-muted)]">{o.fulfillment_status}</td>
                    <td className="px-6 py-4 text-[10px] font-bold text-[var(--color-ink-soft)]">{o.delivery_status}</td>
                    <td className="px-6 py-4 text-[10px] font-bold text-[var(--color-ink-muted)]">{o.invoice_status}</td>
                    <td className="px-6 py-4 font-extrabold font-mono text-[#ED6C00]">{parseFloat(o.total_amount).toFixed(2)} JOD</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${statusColors[o.status] || ""}`}>
                        {o.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => {
                          setSelectedOrder(o);
                          setIsDetailOpen(true);
                        }}
                        className="p-2 hover:bg-[var(--color-surface-2)] rounded-xl text-[var(--color-ink-muted)] hover:text-white transition inline-flex items-center gap-1.5"
                      >
                        <Eye className="w-4 h-4" />
                        <span className="text-[10px] font-bold">Manage</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* DETAIL DRAWER */}
      {isDetailOpen && selectedOrder && (
        <div className="fixed inset-0 bg-white/60 backdrop-blur-sm z-50 flex items-center justify-end">
          <div className="bg-white border-l border-[var(--color-line)] w-full max-w-2xl h-full flex flex-col justify-between shadow-2xl animate-slideOver">
            <div className="px-8 py-6 border-b border-[var(--color-line)] flex justify-between items-center bg-white">
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--color-ink-soft)]">Fulfillment & Delivery Tracker</h2>
                <p className="text-[10px] text-[var(--color-ink-muted)] font-mono mt-0.5">{selectedOrder.order_number}</p>
              </div>
              <button
                onClick={() => setIsDetailOpen(false)}
                className="text-[var(--color-ink-muted)] hover:text-white text-xs font-bold p-1 bg-white rounded-lg border border-[var(--color-line)]"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-8 space-y-6">
              
              {/* Tracker visual stages */}
              <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl space-y-4">
                <div className="flex justify-between items-center text-xs border-b border-[var(--color-line)] pb-3">
                  <span className="font-bold text-[var(--color-ink-muted)]">Order Delivery Roadmap</span>
                  <span className="font-mono text-[#ED6C00] font-extrabold">{parseFloat(selectedOrder.total_amount).toFixed(2)} JOD</span>
                </div>

                <div className="grid grid-cols-3 gap-2 relative">
                  {/* Step 1: Confirmed */}
                  <div className="flex flex-col items-center text-center space-y-2">
                    <div className={`w-8 h-8 rounded-full border flex items-center justify-center font-bold text-xs ${
                      ["CONFIRMED", "PROCESSING", "DELIVERED", "COMPLETED"].includes(selectedOrder.status)
                        ? "bg-[#ED6C00]/20 border-orange-500 text-[#ED6C00]"
                        : "bg-white border-[var(--color-line)] text-[var(--color-ink-muted)]"
                    }`}>
                      <FileCheck className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-bold text-[var(--color-ink-soft)]">1. Confirmed</span>
                  </div>

                  {/* Step 2: Shipped */}
                  <div className="flex flex-col items-center text-center space-y-2">
                    <div className={`w-8 h-8 rounded-full border flex items-center justify-center font-bold text-xs ${
                      ["SHIPPED", "DELIVERED"].includes(selectedOrder.delivery_status) || selectedOrder.status === "COMPLETED"
                        ? "bg-blue-950/40 border-blue-500 text-blue-400"
                        : "bg-white border-[var(--color-line)] text-[var(--color-ink-muted)]"
                    }`}>
                      <Truck className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-bold text-[var(--color-ink-soft)]">2. Dispatched</span>
                  </div>

                  {/* Step 3: Delivered */}
                  <div className="flex flex-col items-center text-center space-y-2">
                    <div className={`w-8 h-8 rounded-full border flex items-center justify-center font-bold text-xs ${
                      selectedOrder.delivery_status === "DELIVERED" || selectedOrder.status === "COMPLETED"
                        ? "bg-emerald-950/40 border-emerald-500 text-emerald-400"
                        : "bg-white border-[var(--color-line)] text-[var(--color-ink-muted)]"
                    }`}>
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-bold text-[var(--color-ink-soft)]">3. Delivered</span>
                  </div>
                </div>
              </div>

              {/* Status Update Quick Triggers */}
              <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl space-y-4">
                <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block">Operator Control Desk</span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  
                  {/* Fulfillment trigger dropdown */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Fulfillment Status</label>
                    <select
                      value={selectedOrder.fulfillment_status}
                      onChange={(e) => handleUpdateOrderStatus(selectedOrder.id, { fulfillment_status: e.target.value })}
                      className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                    >
                      <option value="UNFULFILLED">Unfulfilled</option>
                      <option value="PARTIALLY_FULFILLED">Partially Fulfilled</option>
                      <option value="FULFILLED">Fulfilled</option>
                    </select>
                  </div>

                  {/* Delivery status dropdown */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Delivery Tracker Status</label>
                    <select
                      value={selectedOrder.delivery_status}
                      onChange={(e) => handleUpdateOrderStatus(selectedOrder.id, { delivery_status: e.target.value })}
                      className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                    >
                      <option value="PENDING">Pending (Holding)</option>
                      <option value="SHIPPED">Shipped (Dispatched)</option>
                      <option value="DELIVERED">Delivered (Completed)</option>
                    </select>
                  </div>

                  {/* Order main status dropdown */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Global Status</label>
                    <select
                      value={selectedOrder.status}
                      onChange={(e) => handleUpdateOrderStatus(selectedOrder.id, { status: e.target.value })}
                      className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                    >
                      <option value="DRAFT">Draft</option>
                      <option value="CONFIRMED">Confirmed</option>
                      <option value="PROCESSING">Processing</option>
                      <option value="DELIVERED">Delivered</option>
                      <option value="COMPLETED">Completed</option>
                      <option value="CANCELLED">Cancelled</option>
                    </select>
                  </div>

                  {/* Invoice status dropdown */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Invoicing Pipeline</label>
                    <select
                      value={selectedOrder.invoice_status}
                      onChange={(e) => handleUpdateOrderStatus(selectedOrder.id, { invoice_status: e.target.value })}
                      className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                    >
                      <option value="UNINVOICED">Uninvoiced</option>
                      <option value="PARTIALLY_INVOICED">Partially Invoiced</option>
                      <option value="INVOICED">Invoiced</option>
                    </select>
                  </div>

                </div>
              </div>

              {/* Order Lines table */}
              <div className="space-y-3">
                <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block">Items ordered</span>
                <div className="bg-white border border-[var(--color-line)] rounded-xl overflow-hidden">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-[var(--color-line)] text-[9px] uppercase tracking-wider text-[var(--color-ink-muted)] bg-white">
                        <th className="px-4 py-2">Item Name</th>
                        <th className="px-4 py-2 text-right">Qty</th>
                        <th className="px-4 py-2 text-right">Unit Price</th>
                        <th className="px-4 py-2 text-right">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-850 text-xs font-mono">
                      {selectedOrder.lines?.map((line, idx) => (
                        <tr key={idx} className="hover:bg-white">
                          <td className="px-4 py-3 font-sans text-[var(--color-ink-soft)] font-medium">{line.item_name}</td>
                          <td className="px-4 py-3 text-right text-[var(--color-ink-muted)]">{parseFloat(line.qty).toFixed(1)}</td>
                          <td className="px-4 py-3 text-right text-[var(--color-ink-muted)]">{parseFloat(line.unit_price).toFixed(2)}</td>
                          <td className="px-4 py-3 text-right font-bold text-[var(--color-ink)]">{parseFloat(line.line_total).toFixed(2)} JOD</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>

            <div className="px-8 py-6 border-t border-[var(--color-line)] flex justify-end bg-white">
              <button
                onClick={() => setIsDetailOpen(false)}
                className="bg-white hover:bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] hover:text-white border border-[var(--color-line)] px-5 py-2.5 rounded-xl text-xs font-bold transition"
              >
                Close Panel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CREATE ORDER MODAL */}
      {isCreateOpen && (
        <div className="fixed inset-0 bg-white/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[var(--color-line)] w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden animate-zoomIn flex flex-col max-h-[90vh]">
            <div className="px-6 py-4 border-b border-[var(--color-line)] flex justify-between items-center bg-white">
              <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--color-ink-soft)]">Create New Sales Order</h2>
              <button onClick={() => setIsCreateOpen(false)} className="text-[var(--color-ink-muted)] hover:text-white text-xs font-bold">✕</button>
            </div>

            <form onSubmit={handleCreateOrder} className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-white border border-[var(--color-line)] p-4 rounded-xl">
                <div className="space-y-1 col-span-2">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block mb-1">Link Quote Reference (Optional)</label>
                  <select
                    value={newOrder.quotation}
                    onChange={(e) => handleApplyQuoteReference(e.target.value)}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                  >
                    <option value="">No reference (Custom Order)</option>
                    {quotations.map((q) => (
                      <option key={q.id} value={q.id}>{q.quotation_number} - {q.customer_name} ({parseFloat(q.total_amount).toFixed(2)} JOD)</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Order Number *</label>
                  <input
                    type="text"
                    required
                    value={newOrder.order_number}
                    onChange={(e) => setNewOrder({ ...newOrder, order_number: e.target.value })}
                    placeholder="e.g. SO-2026-0001"
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none focus:border-[var(--color-ink)] font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Customer Name *</label>
                  <input
                    type="text"
                    required
                    value={newOrder.customer_name}
                    onChange={(e) => setNewOrder({ ...newOrder, customer_name: e.target.value })}
                    placeholder="e.g. Anabtawi Bakery Branch"
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none focus:border-[var(--color-ink)]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Company *</label>
                  <select
                    required
                    value={newOrder.company}
                    onChange={(e) => setNewOrder({ ...newOrder, company: e.target.value })}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                  >
                    <option value="">Select Company</option>
                    {companies.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Branch *</label>
                  <select
                    required
                    value={newOrder.branch}
                    onChange={(e) => setNewOrder({ ...newOrder, branch: e.target.value })}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                  >
                    <option value="">Select Branch</option>
                    {branches.map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Line items */}
              <div className="space-y-3 pt-2">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Sales Order Items *</span>
                  <button
                    type="button"
                    onClick={addLine}
                    className="text-[#ED6C00] hover:text-[#ED6C00] text-xs font-bold flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Add Item
                  </button>
                </div>

                <div className="space-y-3">
                  {newOrder.lines.map((line, index) => (
                    <div key={index} className="flex gap-3 items-end bg-white border border-[var(--color-line)] p-4 rounded-xl">
                      <div className="flex-1 space-y-1">
                        <label className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Item Name</label>
                        <input
                          type="text"
                          required
                          value={line.item_name}
                          onChange={(e) => updateLine(index, "item_name", e.target.value)}
                          placeholder="e.g. Standard Baklawa Box"
                          className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none"
                        />
                      </div>

                      <div className="w-24 space-y-1">
                        <label className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Qty</label>
                        <input
                          type="number"
                          required
                          value={line.qty}
                          onChange={(e) => updateLine(index, "qty", e.target.value)}
                          className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none font-mono"
                        />
                      </div>

                      <div className="w-28 space-y-1">
                        <label className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Unit Price</label>
                        <input
                          type="number"
                          step="0.01"
                          required
                          value={line.unit_price}
                          onChange={(e) => updateLine(index, "unit_price", e.target.value)}
                          className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none font-mono"
                        />
                      </div>

                      <button
                        type="button"
                        onClick={() => removeLine(index)}
                        disabled={newOrder.lines.length === 1}
                        className="bg-white border border-[var(--color-line)] hover:bg-white transition p-2.5 rounded-xl text-[var(--color-ink-muted)] hover:text-red-400 disabled:opacity-30 disabled:pointer-events-none"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-[var(--color-line)] flex justify-end gap-3 font-sans">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="bg-white hover:bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] hover:text-white border border-[var(--color-line)] px-4 py-2 rounded-xl text-xs font-bold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-[#ED6C00] hover:bg-[#ED6C00] text-white px-4 py-2 rounded-xl text-xs font-bold transition shadow-lg shadow-orange-950/20"
                >
                  Confirm Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
