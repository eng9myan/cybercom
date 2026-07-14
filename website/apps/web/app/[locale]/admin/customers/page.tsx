"use client";

import { useState } from "react";
import {
  Search, Filter, ArrowUpRight, Building2, Stethoscope,
  ShoppingCart, BarChart3, Pill, FlaskConical, Scan,
  CheckCircle2, Clock, AlertCircle,
} from "lucide-react";
import Link from "next/link";

const PRODUCT_ICONS: Record<string, React.ElementType> = {
  "CyMed Hospital": Building2,
  "CyMed Clinic": Stethoscope,
  "CyMed Pharmacy": Pill,
  "CyMed Laboratory": FlaskConical,
  "CyMed Imaging": Scan,
  CyShop: ShoppingCart,
  "CyCom ERP": BarChart3,
};

const CUSTOMERS = [
  {
    id: "C-001", name: "King Abdullah University Hospital", country: "JO", tier: "Enterprise",
    status: "active", products: ["CyMed Hospital", "CyMed Pharmacy", "CyCom ERP"],
    mrr: 7898, since: "2025-01-15", contact: "Dr. Rania Khalil",
  },
  {
    id: "C-002", name: "Saudi German Hospital Group", country: "SA", tier: "Enterprise",
    status: "active", products: ["CyMed Hospital", "CyCom ERP"],
    mrr: 7199, since: "2025-03-01", contact: "Mr. Faisal Al-Harbi",
  },
  {
    id: "C-003", name: "AlAmeen Pharmacy Network", country: "AE", tier: "Professional",
    status: "active", products: ["CyMed Pharmacy"],
    mrr: 399, since: "2025-06-10", contact: "Ms. Huda Al-Rashid",
  },
  {
    id: "C-004", name: "Jordan Medical Laboratory", country: "JO", tier: "Core",
    status: "active", products: ["CyMed Laboratory"],
    mrr: 549, since: "2025-09-22", contact: "Dr. Tariq Mansour",
  },
  {
    id: "C-005", name: "City Mall Retail Group", country: "JO", tier: "Business",
    status: "active", products: ["CyShop"],
    mrr: 299, since: "2026-01-08", contact: "Mr. Khalid Nawas",
  },
  {
    id: "C-006", name: "Gulf Diagnostic Imaging Center", country: "KW", tier: "Advanced",
    status: "active", products: ["CyMed Imaging"],
    mrr: 799, since: "2026-02-14", contact: "Dr. Samira Nasser",
  },
  {
    id: "C-007", name: "Al Noor Specialist Clinics", country: "AE", tier: "Professional",
    status: "active", products: ["CyMed Clinic", "CyCom ERP"],
    mrr: 3498, since: "2026-03-20", contact: "Dr. Mohamed Kamal",
  },
  {
    id: "C-008", name: "Riyadh Digital Health Initiative", country: "SA", tier: "Enterprise",
    status: "trial", products: ["CyMed Hospital"],
    mrr: 0, since: "2026-07-01", contact: "Ms. Noor Al-Qahtani",
  },
];

const STATUS_CONFIG: Record<string, { label: string; icon: React.ElementType; className: string }> = {
  active: { label: "Active", icon: CheckCircle2, className: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
  trial: { label: "Trial", icon: Clock, className: "text-cy-orange bg-cy-orange/10 border-cy-orange/20" },
  suspended: { label: "Suspended", icon: AlertCircle, className: "text-red-400 bg-red-500/10 border-red-500/20" },
};

export default function AdminCustomersPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = CUSTOMERS.filter((c) => {
    const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.country.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalMRR = CUSTOMERS.filter((c) => c.status === "active").reduce((s, c) => s + c.mrr, 0);

  return (
    <div>
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-heading font-semibold text-white mb-1">Customers</h1>
          <p className="text-sm text-cy-gray-400">{CUSTOMERS.length} total · ${totalMRR.toLocaleString()}/mo active MRR</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cy-gray-500" />
          <input
            className="w-full glass-card rounded-lg pl-9 pr-3 py-2.5 text-sm text-white placeholder:text-cy-gray-500 outline-none focus:border-cy-orange border border-cy-glass-border transition-colors"
            placeholder="Search customers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1 p-1 rounded-lg bg-cy-dark/60 border border-cy-glass-border">
          <Filter className="w-4 h-4 text-cy-gray-500 ml-2" />
          {["all", "active", "trial", "suspended"].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all capitalize ${statusFilter === s ? "bg-cy-glass-border text-white" : "text-cy-gray-400 hover:text-white"}`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="glass-card rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-cy-glass-border">
                {["Customer", "Country", "Products", "MRR", "Status", "Since", ""].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium text-cy-gray-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => {
                const status = STATUS_CONFIG[c.status]!;
                const StatusIcon = status.icon;
                return (
                  <tr key={c.id} className="border-b border-cy-glass-border/50 hover:bg-cy-glass-border/20 transition-colors">
                    <td className="px-4 py-4">
                      <div className="font-medium text-white">{c.name}</div>
                      <div className="text-xs text-cy-gray-400">{c.contact} · {c.id}</div>
                    </td>
                    <td className="px-4 py-4 text-cy-gray-300">{c.country}</td>
                    <td className="px-4 py-4">
                      <div className="flex gap-1 flex-wrap">
                        {c.products.map((p) => {
                          const Icon = PRODUCT_ICONS[p] ?? Building2;
                          return (
                            <span key={p} title={p} className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-cy-glass-border text-cy-gray-300">
                              <Icon className="w-3.5 h-3.5" />
                            </span>
                          );
                        })}
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      {c.mrr > 0
                        ? <span className="font-semibold text-white">${c.mrr.toLocaleString()}</span>
                        : <span className="text-cy-gray-400 text-xs">Trial</span>}
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${status.className}`}>
                        <StatusIcon className="w-3 h-3" />
                        {status.label}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-xs text-cy-gray-400">
                      {new Date(c.since).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                    </td>
                    <td className="px-4 py-4">
                      <button className="p-1.5 rounded-lg hover:bg-cy-glass-border/50 text-cy-gray-400 hover:text-white transition-colors">
                        <ArrowUpRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-cy-gray-400 text-sm">No customers match your filter.</div>
        )}
      </div>
    </div>
  );
}
