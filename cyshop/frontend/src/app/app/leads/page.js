"use client";

import { useState, useEffect } from "react";
import { Plus, Search, Building, User, Mail, Phone, ArrowRight, Tag, AlertCircle, CheckCircle, SlidersHorizontal, RefreshCw } from "lucide-react";

export default function LeadsPage() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Search & Filter state
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [priorityFilter, setPriorityFilter] = useState("ALL");

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isConvertOpen, setIsConvertOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);

  // Form state
  const [newLead, setNewLead] = useState({
    name: "",
    company: "",
    contact_person: "",
    email: "",
    phone: "",
    source: "MANUAL",
    status: "NEW",
    priority: "MEDIUM",
    expected_revenue: "0.00",
  });

  const sources = [
    { value: "WEBSITE", label: "Website" },
    { value: "REFERRAL", label: "Referral" },
    { value: "FACEBOOK", label: "Facebook" },
    { value: "INSTAGRAM", label: "Instagram" },
    { value: "LINKEDIN", label: "LinkedIn" },
    { value: "GOOGLE_ADS", label: "Google Ads" },
    { value: "TRADE_SHOW", label: "Trade Show" },
    { value: "MANUAL", label: "Manual Entry" },
    { value: "IMPORT", label: "Import" },
    { value: "API", label: "API" },
  ];

  const statuses = [
    { value: "NEW", label: "New" },
    { value: "CONTACTED", label: "Contacted" },
    { value: "QUALIFIED", label: "Qualified" },
    { value: "LOST", label: "Lost" },
  ];

  const priorities = [
    { value: "LOW", label: "Low" },
    { value: "MEDIUM", label: "Medium" },
    { value: "HIGH", label: "High" },
    { value: "CRITICAL", label: "Critical" },
  ];

  const fetchLeads = async () => {
    setLoading(true);
    setError("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const response = await fetch("/api/v1/sales/leads/", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setLeads(data);
      } else {
        throw new Error("Failed to fetch leads data.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLead = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const response = await fetch("/api/v1/sales/leads/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
        body: JSON.stringify(newLead),
      });

      if (response.ok) {
        setSuccess("Lead successfully created!");
        setIsCreateOpen(false);
        setNewLead({
          name: "",
          company: "",
          contact_person: "",
          email: "",
          phone: "",
          source: "MANUAL",
          status: "NEW",
          priority: "MEDIUM",
          expected_revenue: "0.00",
        });
        fetchLeads();
      } else {
        const data = await response.json();
        throw new Error(data.detail || JSON.stringify(data) || "Error creating lead.");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleConvertLead = async (leadId) => {
    setError("");
    setSuccess("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const response = await fetch(`/api/v1/sales/leads/${leadId}/convert/`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(data.message || "Lead converted to Opportunity!");
        setIsConvertOpen(false);
        fetchLeads();
      } else {
        const data = await response.json();
        throw new Error(data.error || "Failed to convert lead.");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, []);

  const filteredLeads = leads.filter((lead) => {
    const matchesSearch =
      lead.name.toLowerCase().includes(search.toLowerCase()) ||
      (lead.company && lead.company.toLowerCase().includes(search.toLowerCase())) ||
      (lead.email && lead.email.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = statusFilter === "ALL" || lead.status === statusFilter;
    const matchesPriority = priorityFilter === "ALL" || lead.priority === priorityFilter;

    return matchesSearch && matchesStatus && matchesPriority;
  });

  return (
    <div className="space-y-6 text-[var(--color-ink)] animate-fade">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">Leads Directory</h1>
          <p className="text-xs text-[var(--color-ink-muted)]">Capture, filter, and convert customer prospects into deal pipelines.</p>
        </div>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center gap-2 bg-[#ED6C00] hover:bg-[#ED6C00] transition text-white px-4 py-2.5 rounded-xl text-xs font-bold shadow-lg shadow-orange-950/20"
        >
          <Plus className="w-4 h-4" />
          Create Lead
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
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* Filter panel */}
      <div className="bg-white border border-[var(--color-line)] p-4 rounded-2xl flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-[var(--color-ink-muted)] absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search leads by name, company..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-white border border-[var(--color-line)] rounded-xl py-2 pl-10 pr-4 text-xs text-[var(--color-ink)] placeholder-[var(--color-ink-muted)] focus:outline-none focus:border-[var(--color-ink)] font-medium"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-3.5 h-3.5 text-[var(--color-ink-muted)]" />
            <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-wider font-bold">Filters:</span>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none focus:border-[var(--color-ink)] font-bold"
          >
            <option value="ALL">All Statuses</option>
            {statuses.map((st) => (
              <option key={st.value} value={st.value}>{st.label}</option>
            ))}
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none focus:border-[var(--color-ink)] font-bold"
          >
            <option value="ALL">All Priorities</option>
            {priorities.map((pr) => (
              <option key={pr.value} value={pr.value}>{pr.label}</option>
            ))}
          </select>

          <button
            onClick={fetchLeads}
            className="w-9 h-9 bg-white border border-[var(--color-line)] rounded-xl flex items-center justify-center text-[var(--color-ink-muted)] hover:text-white transition hover:bg-white"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main grid / list */}
      {loading ? (
        <div className="flex justify-center items-center h-60">
          <div className="w-8 h-8 border-4 border-[var(--color-line)] border-t-orange-500 rounded-full animate-spin"></div>
        </div>
      ) : filteredLeads.length === 0 ? (
        <div className="bg-white border border-[var(--color-line)] p-12 rounded-2xl text-center">
          <p className="text-xs text-[var(--color-ink-muted)] font-medium">No leads match the active filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredLeads.map((lead) => {
            const priorityColors = {
              LOW: "bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] border-[var(--color-ink)]",
              MEDIUM: "bg-blue-950/40 text-blue-400 border-blue-900/30",
              HIGH: "bg-[rgba(237,108,0,0.08)] text-[#ED6C00] border-[rgba(237,108,0,0.25)]",
              CRITICAL: "bg-red-950/40 text-red-400 border-red-900/30",
            };

            const statusColors = {
              NEW: "bg-white text-[var(--color-ink-muted)] border-[var(--color-line)]",
              CONTACTED: "bg-sky-950/40 text-sky-400 border-sky-900/30",
              QUALIFIED: "bg-emerald-950/40 text-emerald-400 border-emerald-900/30",
              LOST: "bg-red-950/20 text-red-500/80 border-red-950/40",
            };

            return (
              <div
                key={lead.id}
                className="bg-white border border-[var(--color-line)] rounded-2xl p-6 flex flex-col justify-between hover:border-[var(--color-ink)] transition duration-200 shadow-sm"
              >
                <div className="space-y-4">
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <h3 className="font-bold text-sm text-[var(--color-ink)]">{lead.name}</h3>
                      {lead.company && (
                        <div className="flex items-center gap-1.5 text-xs text-[var(--color-ink-muted)] mt-1">
                          <Building className="w-3.5 h-3.5 text-[var(--color-ink-muted)]" />
                          <span>{lead.company}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1.5">
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${priorityColors[lead.priority] || ""}`}>
                        {lead.priority}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${statusColors[lead.status] || ""}`}>
                        {lead.status}
                      </span>
                    </div>
                  </div>

                  <div className="border-t border-[var(--color-line)] pt-4 space-y-2 text-xs">
                    {lead.contact_person && (
                      <div className="flex items-center gap-2 text-[var(--color-ink-muted)]">
                        <User className="w-3.5 h-3.5 text-[var(--color-ink-muted)]" />
                        <span>{lead.contact_person}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-[var(--color-ink-muted)]">
                      <Mail className="w-3.5 h-3.5 text-[var(--color-ink-muted)]" />
                      <span className="truncate">{lead.email}</span>
                    </div>
                    {lead.phone && (
                      <div className="flex items-center gap-2 text-[var(--color-ink-muted)]">
                        <Phone className="w-3.5 h-3.5 text-[var(--color-ink-muted)]" />
                        <span>{lead.phone}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="border-t border-[var(--color-line)] mt-6 pt-4 flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="text-[9px] text-[var(--color-ink-muted)] font-bold uppercase tracking-wider">Est. Revenue</span>
                    <div className="text-sm font-extrabold font-mono text-[#ED6C00]">
                      {parseFloat(lead.expected_revenue).toFixed(2)} JOD
                    </div>
                  </div>

                  {lead.status !== "QUALIFIED" && (
                    <button
                      onClick={() => {
                        setSelectedLead(lead);
                        setIsConvertOpen(true);
                      }}
                      className="flex items-center gap-1.5 bg-white border border-[var(--color-line)] hover:bg-white transition text-[var(--color-ink-soft)] hover:text-white px-3 py-1.5 rounded-xl text-[10px] font-bold"
                    >
                      Convert
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* CREATE LEAD MODAL */}
      {isCreateOpen && (
        <div className="fixed inset-0 bg-white/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[var(--color-line)] w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden animate-zoomIn flex flex-col max-h-[90vh]">
            <div className="px-6 py-4 border-b border-[var(--color-line)] flex justify-between items-center">
              <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--color-ink-soft)]">Add New Prospect Lead</h2>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="text-[var(--color-ink-muted)] hover:text-white text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateLead} className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Prospect Name *</label>
                  <input
                    type="text"
                    required
                    value={newLead.name}
                    onChange={(e) => setNewLead({ ...newLead, name: e.target.value })}
                    placeholder="e.g., Al-Nabulsi Bakery"
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none focus:border-[var(--color-ink)]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Company Name</label>
                  <input
                    type="text"
                    value={newLead.company}
                    onChange={(e) => setNewLead({ ...newLead, company: e.target.value })}
                    placeholder="e.g., Nabulsi & Sons"
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none focus:border-[var(--color-ink)]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Contact Person</label>
                  <input
                    type="text"
                    value={newLead.contact_person}
                    onChange={(e) => setNewLead({ ...newLead, contact_person: e.target.value })}
                    placeholder="e.g., Tareq Nabulsi"
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none focus:border-[var(--color-ink)]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Email Address *</label>
                  <input
                    type="email"
                    required
                    value={newLead.email}
                    onChange={(e) => setNewLead({ ...newLead, email: e.target.value })}
                    placeholder="e.g., tareq@nabulsi.com"
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none focus:border-[var(--color-ink)]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Phone Number</label>
                  <input
                    type="text"
                    value={newLead.phone}
                    onChange={(e) => setNewLead({ ...newLead, phone: e.target.value })}
                    placeholder="e.g., +962791234567"
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none focus:border-[var(--color-ink)]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Estimated Deal Value (JOD)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newLead.expected_revenue}
                    onChange={(e) => setNewLead({ ...newLead, expected_revenue: e.target.value })}
                    placeholder="5000.00"
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink)] focus:outline-none focus:border-[var(--color-ink)] font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Source</label>
                  <select
                    value={newLead.source}
                    onChange={(e) => setNewLead({ ...newLead, source: e.target.value })}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none focus:border-[var(--color-ink)]"
                  >
                    {sources.map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Priority</label>
                  <select
                    value={newLead.priority}
                    onChange={(e) => setNewLead({ ...newLead, priority: e.target.value })}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none focus:border-[var(--color-ink)]"
                  >
                    {priorities.map((p) => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Status</label>
                  <select
                    value={newLead.status}
                    onChange={(e) => setNewLead({ ...newLead, status: e.target.value })}
                    className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none focus:border-[var(--color-ink)]"
                  >
                    {statuses.map((st) => (
                      <option key={st.value} value={st.value}>{st.label}</option>
                    ))}
                  </select>
                </div>
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
                  className="bg-[#ED6C00] hover:bg-[#ED6C00] text-white px-4 py-2 rounded-xl text-xs font-bold transition"
                >
                  Submit Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CONVERT LEAD CONFIRMATION MODAL */}
      {isConvertOpen && selectedLead && (
        <div className="fixed inset-0 bg-white/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[var(--color-line)] w-full max-w-md rounded-2xl shadow-2xl overflow-hidden animate-zoomIn">
            <div className="px-6 py-4 border-b border-[var(--color-line)]">
              <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--color-ink-soft)]">Convert Lead to Opportunity</h2>
            </div>

            <div className="p-6 space-y-4">
              <p className="text-xs text-[var(--color-ink-muted)] leading-relaxed">
                You are about to qualify <strong className="text-[var(--color-ink)]">{selectedLead.name}</strong> and convert it into a pipeline Deal Opportunity. 
                This will automatically:
              </p>
              <ul className="text-xs text-[var(--color-ink-muted)] list-disc pl-4 space-y-1">
                <li>Change Lead status to <strong className="text-emerald-400">QUALIFIED</strong>.</li>
                <li>Create an Opportunity card in the CRM Kanban Board with stage <strong className="text-[#ED6C00]">QUALIFIED</strong>.</li>
                <li>Log a converted audit action under activities history.</li>
              </ul>

              <div className="pt-4 border-t border-[var(--color-line)] flex justify-end gap-3">
                <button
                  onClick={() => setIsConvertOpen(false)}
                  className="bg-white hover:bg-[var(--color-surface-2)] text-[var(--color-ink-muted)] hover:text-white border border-[var(--color-line)] px-4 py-2 rounded-xl text-xs font-bold transition"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleConvertLead(selectedLead.id)}
                  className="bg-[#ED6C00] hover:bg-[#ED6C00] text-white px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5"
                >
                  Confirm Conversion
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
