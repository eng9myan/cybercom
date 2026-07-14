"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Building2, BarChart3, Pill, ArrowRight, Check,
  ChevronUp, ChevronDown, Calendar, AlertCircle, Plus,
  RefreshCw,
} from "lucide-react";

const SUBSCRIPTIONS = [
  {
    id: "cymed-hospital",
    name: "CyMed Hospital",
    edition: "Hospital Advanced",
    icon: Building2,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    status: "active",
    billing: "annual",
    monthlyEquiv: 4500,
    startDate: "2026-07-01",
    renewalDate: "2027-07-01",
    seats: 120,
    usedSeats: 87,
    modules: ["ADT", "EMR", "Nursing", "OR Management", "ICU", "PACS", "Billing"],
    availableEditions: [
      { name: "Hospital Core", price: 2500 },
      { name: "Hospital Advanced", price: 4500 },
      { name: "Hospital Enterprise", price: null },
    ],
  },
  {
    id: "cymed-pharmacy",
    name: "CyMed Pharmacy",
    edition: "Pharmacy Clinical",
    icon: Pill,
    color: "text-violet-400",
    bg: "bg-violet-500/10",
    border: "border-violet-500/20",
    status: "active",
    billing: "annual",
    monthlyEquiv: 399,
    startDate: "2026-07-01",
    renewalDate: "2027-07-01",
    seats: 20,
    usedSeats: 14,
    modules: ["Dispensing", "Inventory", "Clinical Review", "IV Admixture", "Narcotic Tracking"],
    availableEditions: [
      { name: "Pharmacy Core", price: 199 },
      { name: "Pharmacy Clinical", price: 399 },
    ],
  },
  {
    id: "cycom-erp",
    name: "CyCom ERP",
    edition: "Enterprise",
    icon: BarChart3,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    status: "active",
    billing: "annual",
    monthlyEquiv: 2499,
    startDate: "2026-07-01",
    renewalDate: "2027-07-01",
    seats: 50,
    usedSeats: 32,
    modules: ["Finance", "HR", "Inventory", "CRM", "Manufacturing", "BI", "Advanced Analytics"],
    availableEditions: [
      { name: "Business", price: 999 },
      { name: "Enterprise", price: 2499 },
      { name: "Healthcare ERP", price: null },
    ],
  },
];

export default function SubscriptionsPage() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div>
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-heading font-semibold text-white mb-1">Subscriptions</h1>
          <p className="text-sm text-cy-gray-400">Manage your active products and editions</p>
        </div>
        <Link
          href="/en/subscribe"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-cy-orange hover:bg-cy-orange-light text-white transition-colors"
        >
          <Plus className="w-4 h-4" /> Add Product
        </Link>
      </div>

      <div className="space-y-4">
        {SUBSCRIPTIONS.map((sub) => {
          const Icon = sub.icon;
          const expanded = expandedId === sub.id;
          const usagePct = Math.round((sub.usedSeats / sub.seats) * 100);
          const annualTotal = Math.round(sub.monthlyEquiv * 0.8 * 12);
          return (
            <div key={sub.id} className="glass-card rounded-xl overflow-hidden">
              {/* Header row */}
              <button
                onClick={() => setExpandedId(expanded ? null : sub.id)}
                className="w-full text-left p-5 flex items-center gap-4"
              >
                <div className={`w-10 h-10 rounded-lg ${sub.bg} border ${sub.border} flex items-center justify-center flex-shrink-0`}>
                  <Icon className={`w-5 h-5 ${sub.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-heading font-semibold text-white">{sub.name}</span>
                    <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      Active
                    </span>
                  </div>
                  <div className="text-xs text-cy-gray-400">{sub.edition} · Annual · ${sub.monthlyEquiv.toLocaleString()}/mo equiv.</div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="hidden sm:flex items-center gap-1.5 text-xs text-cy-gray-400">
                    <Calendar className="w-3.5 h-3.5" />
                    Renews {new Date(sub.renewalDate).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                  </div>
                  {expanded ? <ChevronUp className="w-4 h-4 text-cy-gray-400" /> : <ChevronDown className="w-4 h-4 text-cy-gray-400" />}
                </div>
              </button>

              {/* Expanded detail */}
              {expanded && (
                <div className="border-t border-cy-glass-border p-5 space-y-6">
                  {/* Usage */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-cy-gray-400">Seat Usage</span>
                      <span className="text-xs text-cy-gray-400">{sub.usedSeats} / {sub.seats} seats used</span>
                    </div>
                    <div className="h-2 bg-cy-glass-border rounded-full overflow-hidden mb-1">
                      <div
                        className={`h-full rounded-full ${usagePct > 85 ? "bg-amber-400" : "bg-emerald-500"}`}
                        style={{ width: `${usagePct}%` }}
                      />
                    </div>
                    {usagePct > 85 && (
                      <div className="flex items-center gap-1.5 text-xs text-amber-400 mt-2">
                        <AlertCircle className="w-3.5 h-3.5" />
                        Approaching seat limit — consider upgrading
                      </div>
                    )}
                  </div>

                  {/* Active modules */}
                  <div>
                    <div className="text-xs font-medium text-cy-gray-400 mb-3">Active Modules</div>
                    <div className="flex flex-wrap gap-2">
                      {sub.modules.map((m) => (
                        <span key={m} className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-cy-glass-border text-cy-gray-300">
                          <Check className="w-3 h-3 text-emerald-400" />
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Edition change */}
                  <div>
                    <div className="text-xs font-medium text-cy-gray-400 mb-3">Change Edition</div>
                    <div className="grid sm:grid-cols-3 gap-2">
                      {sub.availableEditions.map((ed) => (
                        <div
                          key={ed.name}
                          className={`p-3 rounded-xl border text-left transition-all ${ed.name === sub.edition ? `${sub.border} ${sub.bg}` : "border-cy-glass-border hover:border-cy-glass-bg-hover cursor-pointer"}`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-semibold text-white">{ed.name}</span>
                            {ed.name === sub.edition && <Check className={`w-3.5 h-3.5 ${sub.color}`} />}
                          </div>
                          <div className={`text-sm font-bold ${sub.color}`}>
                            {ed.price !== null ? `$${ed.price.toLocaleString()}/mo` : "Custom"}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Billing summary */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-cy-dark/40 border border-cy-glass-border">
                    <div className="text-sm">
                      <div className="text-white font-medium">Annual subscription</div>
                      <div className="text-xs text-cy-gray-400 mt-0.5">
                        {new Date(sub.startDate).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                        {" → "}
                        {new Date(sub.renewalDate).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-white font-bold">${annualTotal.toLocaleString()}/yr</div>
                      <div className="text-xs text-emerald-400">20% discount applied</div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap gap-3 pt-2">
                    <button className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-cy-orange hover:bg-cy-orange-light text-white transition-colors">
                      <RefreshCw className="w-3.5 h-3.5" />
                      Upgrade / Change Edition
                    </button>
                    <button className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-cy-gray-300 border border-cy-glass-border hover:border-cy-glass-bg-hover transition-colors">
                      Add Seats
                    </button>
                    <button className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-cy-gray-400 hover:text-red-400 transition-colors ml-auto">
                      Cancel Subscription
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Add more */}
      <div className="mt-8 p-6 rounded-xl border border-dashed border-cy-glass-border text-center">
        <p className="text-sm text-cy-gray-400 mb-4">Interested in more CyberCom products?</p>
        <div className="flex flex-wrap justify-center gap-3 mb-5 text-xs text-cy-gray-500">
          {["CyMed Clinic", "CyMed Laboratory", "CyMed Imaging", "CyShop"].map((p) => (
            <span key={p} className="px-3 py-1.5 rounded-lg border border-cy-glass-border">{p}</span>
          ))}
        </div>
        <Link
          href="/en/subscribe"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium bg-cy-orange hover:bg-cy-orange-light text-white transition-colors"
        >
          Browse all products <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
}
