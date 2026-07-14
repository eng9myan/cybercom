"use client";

import { useState, useEffect } from "react";
import { Plus, Search, FileText, CheckCircle, AlertTriangle, Eye, SlidersHorizontal, RefreshCw, X, Trash2 } from "lucide-react";

export default function QuotationsPage() {
  const [quotations, setQuotations] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Search & Filter state
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedQuotation, setSelectedQuotation] = useState(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Form state
  const [newQuote, setNewQuote] = useState({
    quotation_number: "",
    company: "",
    branch: "",
    customer_name: "",
    customer_type: "RETAIL",
    discount_type: "PERCENTAGE",
    discount_value: "0.00",
    tax_rate: "0.1600",
    expiration_date: "",
    terms_conditions: "",
    lines: [{ item_name: "", qty: "1", unit_price: "0.00" }],
  });

  const fetchQuotationData = async () => {
    setLoading(true);
    setError("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      // 1. Fetch Quotations
      const qRes = await fetch("/api/v1/sales/quotations/", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
      });
      if (!qRes.ok) throw new Error("Failed to load quotations");
      const qData = await qRes.json();
      setQuotations(qData);

      // 2. Fetch Companies
      const compRes = await fetch("/api/v1/tenants/companies/", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
      });
      if (compRes.ok) {
        const compData = await compRes.json();
        setCompanies(compData);
        if (compData.length > 0 && !newQuote.company) {
          setNewQuote(prev => ({ ...prev, company: compData[0].id }));
        }
      }

      // 3. Fetch Branches
      const brRes = await fetch("/api/v1/tenants/branches/", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
      });
      if (brRes.ok) {
        const brData = await brRes.json();
        setBranches(brData);
        if (brData.length > 0 && !newQuote.branch) {
          setNewQuote(prev => ({ ...prev, branch: brData[0].id }));
        }
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateQuotation = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    // Basic Validation
    if (newQuote.lines.some(l => !l.item_name || parseFloat(l.qty) <= 0 || parseFloat(l.unit_price) < 0)) {
      setError("Please ensure all quotation lines contain valid item names, quantities (>0), and prices (>=0).");
      return;
    }

    try {
      const payload = {
        ...newQuote,
        discount_value: parseFloat(newQuote.discount_value),
        tax_rate: parseFloat(newQuote.tax_rate),
        lines: newQuote.lines.map(l => ({
          item_name: l.item_name,
          qty: parseFloat(l.qty),
          unit_price: parseFloat(l.unit_price)
        }))
      };

      const response = await fetch("/api/v1/sales/quotations/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        setSuccess("Quotation successfully created!");
        setIsCreateOpen(false);
        setNewQuote({
          quotation_number: "",
          company: companies[0]?.id || "",
          branch: branches[0]?.id || "",
          customer_name: "",
          customer_type: "RETAIL",
          discount_type: "PERCENTAGE",
          discount_value: "0.00",
          tax_rate: "0.1600",
          expiration_date: "",
          terms_conditions: "",
          lines: [{ item_name: "", qty: "1", unit_price: "0.00" }],
        });
        fetchQuotationData();
      } else {
        const data = await response.json();
        throw new Error(data.detail || JSON.stringify(data) || "Error creating quotation.");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleApproveQuotation = async (qId) => {
    setError("");
    setSuccess("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const response = await fetch(`/api/v1/sales/quotations/${qId}/approve/`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(data.message || "Quotation approved!");
        setIsDetailOpen(false);
        fetchQuotationData();
      } else {
        const data = await response.json();
        throw new Error(data.detail || "Failed to approve quotation.");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const addLine = () => {
    setNewQuote({
      ...newQuote,
      lines: [...newQuote.lines, { item_name: "", qty: "1", unit_price: "0.00" }],
    });
  };

  const removeLine = (index) => {
    if (newQuote.lines.length === 1) return;
    const nextLines = [...newQuote.lines];
    nextLines.splice(index, 1);
    setNewQuote({ ...newQuote, lines: nextLines });
  };

  const updateLine = (index, field, value) => {
    const nextLines = [...newQuote.lines];
    nextLines[index][field] = value;
    setNewQuote({ ...newQuote, lines: nextLines });
  };

  useEffect(() => {
    fetchQuotationData();
  }, []);

  const filteredQuotes = quotations.filter((q) => {
    const matchesSearch =
      q.quotation_number.toLowerCase().includes(search.toLowerCase()) ||
      q.customer_name.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === "ALL" || q.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 text-[var(--color-ink)] animate-fade">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">Quotations</h1>
          <p className="text-xs text-[var(--color-ink-muted)]">Generate, calculate, and route customer pricing bids with approval guardrails.</p>
        </div>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center gap-2 bg-[#ED6C00] hover:bg-[#ED6C00] transition text-white px-4 py-2.5 rounded-xl text-xs font-bold shadow-lg shadow-orange-950/20"
        >
          <Plus className="w-4 h-4" />
          New Quotation
        </button>
      </div>

      {error && (
        <div className="bg-red-950/40 border border-red-800 text-red-400 p-4 rounded-xl text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="bg-emerald-950/40 border border-emerald-800 text-emerald-400 p-4 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* Filters and search */}
      <div className="bg-white border border-[var(--color-line)] p-4 rounded-2xl flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-[var(--color-ink-muted)] absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by quote # or customer..."
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
            <option value="SUBMITTED">Submitted (Pending Review)</option>
            <option value="APPROVED">Approved</option>
            <option value="SENT">Sent</option>
            <option value="ACCEPTED">Accepted</option>
            <option value="REJECTED">Rejected</option>
            <option value="EXPIRED">Expired</option>
            <option value="CANCELLED">Cancelled</option>
          </select>

          <button
            onClick={fetchQuotationData}
            className="w-9 h-9 bg-white border border-[var(--color-line)] rounded-xl flex items-center justify-center text-[var(--color-ink-muted)] hover:text-white transition hover:bg-white"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Quotations Table */}
      {loading ? (
        <div className="flex justify-center items-center h-60">
          <div className="w-8 h-8 border-4 border-[var(--color-line)] border-t-orange-500 rounded-full animate-spin"></div>
        </div>
      ) : filteredQuotes.length === 0 ? (
        <div className="bg-white border border-[var(--color-line)] p-12 rounded-2xl text-center">
          <p className="text-xs text-[var(--color-ink-muted)] font-medium">No quotations match search filters.</p>
        </div>
      ) : (
        <div className="bg-white border border-[var(--color-line)] rounded-2xl overflow-hidden shadow">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[var(--color-line)] text-[10px] uppercase tracking-wider text-[var(--color-ink-muted)] bg-white">
                <th className="px-6 py-4 font-bold">Quote Number</th>
                <th className="px-6 py-4 font-bold">Customer Name</th>
                <th className="px-6 py-4 font-bold">Customer Type</th>
                <th className="px-6 py-4 font-bold">Total Amount</th>
                <th className="px-6 py-4 font-bold">Status</th>
                <th className="px-6 py-4 font-bold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-850 text-xs">
              {filteredQuotes.map((q) => {
                const statusColors = {
                  DRAFT: "bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] border-[var(--color-ink)]",
                  SUBMITTED: "bg-[rgba(237,108,0,0.08)] text-[#ED6C00] border-[rgba(237,108,0,0.25)]",
                  APPROVED: "bg-emerald-950/40 text-emerald-450 border-emerald-900/30",
                  SENT: "bg-sky-950/40 text-sky-400 border-sky-900/30",
                  ACCEPTED: "bg-teal-950/40 text-teal-400 border-teal-900/30",
                  REJECTED: "bg-red-950/40 text-red-400 border-red-900/30",
                };

                return (
                  <tr key={q.id} className="hover:bg-white transition">
                    <td className="px-6 py-4 font-bold font-mono text-[var(--color-ink)]">{q.quotation_number}</td>
                    <td className="px-6 py-4 text-[var(--color-ink-soft)] font-medium">{q.customer_name}</td>
                    <td className="px-6 py-4 text-[var(--color-ink-muted)] font-bold text-[10px]">{q.customer_type}</td>
                    <td className="px-6 py-4 font-extrabold font-mono text-[#ED6C00]">{parseFloat(q.total_amount).toFixed(2)} JOD</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${statusColors[q.status] || "bg-white text-[var(--color-ink-muted)] border-[var(--color-line)]"}`}>
                        {q.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => {
                          setSelectedQuotation(q);
                          setIsDetailOpen(true);
                        }}
                        className="p-2 hover:bg-[var(--color-surface-2)] rounded-xl text-[var(--color-ink-muted)] hover:text-white transition inline-flex items-center gap-1.5"
                      >
                        <Eye className="w-4 h-4" />
                        <span className="text-[10px] font-bold">Details</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* DETAIL DRAWER / MODAL */}
      {isDetailOpen && selectedQuotation && (
        <div className="fixed inset-0 bg-white/60 backdrop-blur-sm z-50 flex items-center justify-end">
          <div className="bg-white border-l border-[var(--color-line)] w-full max-w-2xl h-full flex flex-col justify-between shadow-2xl animate-slideOver">
            <div className="px-8 py-6 border-b border-[var(--color-line)] flex justify-between items-center bg-white">
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--color-ink-soft)]">Quotation Detail</h2>
                <p className="text-[10px] text-[var(--color-ink-muted)] font-mono mt-0.5">{selectedQuotation.id}</p>
              </div>
              <button
                onClick={() => setIsDetailOpen(false)}
                className="text-[var(--color-ink-muted)] hover:text-white text-xs font-bold p-1 bg-white rounded-lg border border-[var(--color-line)]"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-8 space-y-6">
              <div className="grid grid-cols-2 gap-6 border-b border-[var(--color-line)] pb-6">
                <div>
                  <span className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block mb-1">Quote Number</span>
                  <span className="text-sm font-bold font-mono text-[var(--color-ink)]">{selectedQuotation.quotation_number}</span>
                </div>
                <div>
                  <span className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block mb-1">Customer Name</span>
                  <span className="text-sm font-bold text-[var(--color-ink)]">{selectedQuotation.customer_name} ({selectedQuotation.customer_type})</span>
                </div>
                <div>
                  <span className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block mb-1">Status</span>
                  <span className="text-xs font-bold text-[#ED6C00]">{selectedQuotation.status}</span>
                </div>
                <div>
                  <span className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block mb-1">Expiration Date</span>
                  <span className="text-xs font-medium text-[var(--color-ink-soft)] font-mono">{selectedQuotation.expiration_date || "N/A"}</span>
                </div>
              </div>

              {/* Line Items */}
              <div className="space-y-3">
                <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block">Quotation Line Items</span>
                <div className="bg-white border border-[var(--color-line)] rounded-xl overflow-hidden">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-[var(--color-line)] text-[9px] uppercase tracking-wider text-[var(--color-ink-muted)] bg-white">
                        <th className="px-4 py-2">Item Name</th>
                        <th className="px-4 py-2 text-right">Qty</th>
                        <th className="px-4 py-2 text-right">Unit Price</th>
                        <th className="px-4 py-2 text-right">Discount</th>
                        <th className="px-4 py-2 text-right">Line Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-850 text-[11px] font-mono">
                      {selectedQuotation.lines?.map((line, idx) => (
                        <tr key={idx} className="hover:bg-white">
                          <td className="px-4 py-3 font-sans text-[var(--color-ink-soft)] font-medium">{line.item_name}</td>
                          <td className="px-4 py-3 text-right text-[var(--color-ink-muted)]">{parseFloat(line.qty).toFixed(1)}</td>
                          <td className="px-4 py-3 text-right text-[var(--color-ink-muted)]">{parseFloat(line.unit_price).toFixed(2)}</td>
                          <td className="px-4 py-3 text-right text-[var(--color-ink-muted)]">-{parseFloat(line.discount).toFixed(2)}</td>
                          <td className="px-4 py-3 text-right font-bold text-[var(--color-ink)]">{parseFloat(line.line_total).toFixed(2)} JOD</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6 pt-4">
                <div className="bg-white border border-[var(--color-line)] p-4 rounded-xl space-y-2">
                  <span className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block">Discounts & Taxes</span>
                  <div className="text-xs space-y-1.5">
                    <div className="flex justify-between text-[var(--color-ink-muted)]">
                      <span>Discount Type:</span>
                      <span className="font-bold">{selectedQuotation.discount_type}</span>
                    </div>
                    <div className="flex justify-between text-[var(--color-ink-muted)]">
                      <span>Discount Value:</span>
                      <span className="font-mono">{parseFloat(selectedQuotation.discount_value).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-[var(--color-ink-muted)]">
                      <span>Tax Rate:</span>
                      <span className="font-mono">{(parseFloat(selectedQuotation.tax_rate) * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white border border-[var(--color-line)] p-4 rounded-xl flex flex-col justify-center items-end">
                  <span className="text-[9px] text-[#ED6C00] uppercase tracking-widest font-bold mb-1">Final Invoice Net</span>
                  <div className="text-xl font-black font-mono text-[#ED6C00]">
                    {parseFloat(selectedQuotation.total_amount).toFixed(2)} JOD
                  </div>
                </div>
              </div>

              {selectedQuotation.terms_conditions && (
                <div className="space-y-1 bg-white border border-[var(--color-line)] p-4 rounded-xl text-xs">
                  <span className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold block">Terms & Conditions</span>
                  <p className="text-[var(--color-ink-muted)] leading-relaxed font-sans">{selectedQuotation.terms_conditions}</p>
                </div>
              )}
            </div>

            <div className="px-8 py-6 border-t border-[var(--color-line)] flex justify-end gap-3 bg-white">
              <button
                onClick={() => setIsDetailOpen(false)}
                className="bg-white hover:bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] hover:text-white border border-[var(--color-line)] px-5 py-2.5 rounded-xl text-xs font-bold transition"
              >
                Close
              </button>

              {selectedQuotation.status === "SUBMITTED" && (
                <button
                  onClick={() => handleApproveQuotation(selectedQuotation.id)}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-lg shadow-emerald-950/20"
                >
                  <CheckCircle className="w-4 h-4" />
                  Approve Quotation
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* CREATE QUOTATION MODAL */}
      {isCreateOpen && (
        <div className="fixed inset-0 bg-white/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[var(--color-line)] w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden animate-zoomIn flex flex-col max-h-[90vh]">
            <div className="px-6 py-4 border-b border-[var(--color-line)] flex justify-between items-center bg-white">
              <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--color-ink-soft)]">Draft New Quotation</h2>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="text-[var(--color-ink-muted)] hover:text-white text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateQuotation} className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Quote Number *</label>
                  <input
                    type="text"
                    required
                    value={newQuote.quotation_number}
                    onChange={(e) => setNewQuote({ ...newQuote, quotation_number: e.target.value })}
                    placeholder="e.g. QT-2026-0001"
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none focus:border-[var(--color-ink)] font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Customer Name *</label>
                  <input
                    type="text"
                    required
                    value={newQuote.customer_name}
                    onChange={(e) => setNewQuote({ ...newQuote, customer_name: e.target.value })}
                    placeholder="e.g., Al-Muna Retailers"
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none focus:border-[var(--color-ink)]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Company *</label>
                  <select
                    required
                    value={newQuote.company}
                    onChange={(e) => setNewQuote({ ...newQuote, company: e.target.value })}
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
                    value={newQuote.branch}
                    onChange={(e) => setNewQuote({ ...newQuote, branch: e.target.value })}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                  >
                    <option value="">Select Branch</option>
                    {branches.map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Customer Type</label>
                  <select
                    value={newQuote.customer_type}
                    onChange={(e) => setNewQuote({ ...newQuote, customer_type: e.target.value })}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                  >
                    <option value="RETAIL">Retail</option>
                    <option value="WHOLESALE">Wholesale (Auto 15% Disc)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Discount Type</label>
                  <select
                    value={newQuote.discount_type}
                    onChange={(e) => setNewQuote({ ...newQuote, discount_type: e.target.value })}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                  >
                    <option value="PERCENTAGE">Percentage (%)</option>
                    <option value="FIXED">Fixed (JOD)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Discount Value</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newQuote.discount_value}
                    onChange={(e) => setNewQuote({ ...newQuote, discount_value: e.target.value })}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none font-mono"
                  />
                </div>
              </div>

              {/* Line Items Form */}
              <div className="space-y-3 pt-2">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Quotation Line Items *</span>
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
                  {newQuote.lines.map((line, index) => (
                    <div key={index} className="flex gap-3 items-end bg-white border border-[var(--color-line)] p-4 rounded-xl">
                      <div className="flex-1 space-y-1">
                        <label className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Item Name</label>
                        <input
                          type="text"
                          required
                          value={line.item_name}
                          onChange={(e) => updateLine(index, "item_name", e.target.value)}
                          placeholder="e.g. Baklawa Pistachio 1kg"
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
                        disabled={newQuote.lines.length === 1}
                        className="bg-white border border-[var(--color-line)] hover:bg-white transition p-2.5 rounded-xl text-[var(--color-ink-muted)] hover:text-red-400 disabled:opacity-30 disabled:pointer-events-none"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Expiration Date</label>
                  <input
                    type="date"
                    value={newQuote.expiration_date}
                    onChange={(e) => setNewQuote({ ...newQuote, expiration_date: e.target.value })}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Tax Rate</label>
                  <select
                    value={newQuote.tax_rate}
                    onChange={(e) => setNewQuote({ ...newQuote, tax_rate: e.target.value })}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                  >
                    <option value="0.1600">Jordan Sales Tax (16%)</option>
                    <option value="0.0000">Exempt (0%)</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Terms & Conditions</label>
                <textarea
                  value={newQuote.terms_conditions}
                  onChange={(e) => setNewQuote({ ...newQuote, terms_conditions: e.target.value })}
                  placeholder="Terms of delivery, payment windows, etc."
                  rows="3"
                  className="w-full bg-white border border-[var(--color-line)] rounded-xl p-3 text-xs text-[var(--color-ink)] focus:outline-none focus:border-[var(--color-ink)]"
                ></textarea>
              </div>

              <div className="pt-4 border-t border-[var(--color-line)] flex justify-end gap-3">
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
                  Submit Quote
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
