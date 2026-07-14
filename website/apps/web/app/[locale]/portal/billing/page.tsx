"use client";

import { useState } from "react";
import {
  Download, CreditCard, Calendar, CheckCircle2,
  FileText, ArrowRight, AlertCircle,
} from "lucide-react";

const INVOICES = [
  { id: "INV-2026-006", date: "2026-07-01", amount: 94776, status: "paid", period: "Jul 2026 – Jun 2027" },
  { id: "INV-2026-005", date: "2026-01-01", amount: 94776, status: "paid", period: "Jan 2026 – Dec 2026" },
  { id: "INV-2025-012", date: "2025-07-01", amount: 82000, status: "paid", period: "Jul 2025 – Jun 2026" },
  { id: "INV-2025-006", date: "2025-01-01", amount: 82000, status: "paid", period: "Jan 2025 – Dec 2025" },
];

const PAYMENT_METHODS = [
  { id: "pm1", type: "bank_transfer", label: "Bank Transfer", detail: "Jordan Arab Bank — Account ending 4821", default: true },
  { id: "pm2", type: "card", label: "Corporate Card", detail: "Visa ending 7734 · Exp 09/2028", default: false },
];

export default function BillingPage() {
  const [activeTab, setActiveTab] = useState<"invoices" | "payment" | "summary">("invoices");

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-semibold text-white mb-1">Billing</h1>
        <p className="text-sm text-cy-gray-400">Invoices, payment methods, and billing history</p>
      </div>

      {/* Next charge notice */}
      <div className="flex items-center gap-4 p-4 mb-6 rounded-xl bg-cy-orange/10 border border-cy-orange/20">
        <Calendar className="w-5 h-5 text-cy-orange flex-shrink-0" />
        <div className="flex-1">
          <div className="text-sm font-medium text-white">Next renewal: July 1, 2027</div>
          <div className="text-xs text-cy-gray-400">Annual subscription — $94,776 will be charged automatically</div>
        </div>
        <button className="text-xs text-cy-orange hover:text-cy-orange-light whitespace-nowrap">Manage →</button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-xl bg-cy-dark/60 border border-cy-glass-border mb-6 max-w-sm">
        {(["invoices", "payment", "summary"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all capitalize ${activeTab === tab ? "bg-cy-glass-border text-white" : "text-cy-gray-400 hover:text-white"}`}
          >
            {tab === "payment" ? "Payment" : tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Invoices */}
      {activeTab === "invoices" && (
        <div className="space-y-3">
          {INVOICES.map((inv) => (
            <div key={inv.id} className="glass-card p-4 rounded-xl flex items-center gap-4">
              <div className="w-9 h-9 rounded-lg bg-cy-glass-border flex items-center justify-center flex-shrink-0">
                <FileText className="w-4 h-4 text-cy-gray-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-sm font-medium text-white">{inv.id}</span>
                  <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                    <CheckCircle2 className="w-3 h-3" /> Paid
                  </span>
                </div>
                <div className="text-xs text-cy-gray-400">{inv.period}</div>
              </div>
              <div className="text-right flex-shrink-0">
                <div className="font-semibold text-white">${inv.amount.toLocaleString()}</div>
                <div className="text-xs text-cy-gray-400">
                  {new Date(inv.date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                </div>
              </div>
              <button className="p-2 rounded-lg hover:bg-cy-glass-border/60 text-cy-gray-400 hover:text-white transition-colors flex-shrink-0">
                <Download className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Payment methods */}
      {activeTab === "payment" && (
        <div className="space-y-4">
          {PAYMENT_METHODS.map((pm) => (
            <div key={pm.id} className={`glass-card p-4 rounded-xl flex items-center gap-4 ${pm.default ? "border-cy-orange/30" : ""}`}>
              <div className="w-9 h-9 rounded-lg bg-cy-glass-border flex items-center justify-center flex-shrink-0">
                <CreditCard className="w-4 h-4 text-cy-gray-400" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-sm font-medium text-white">{pm.label}</span>
                  {pm.default && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-cy-orange/15 text-cy-orange border border-cy-orange/20">Default</span>
                  )}
                </div>
                <div className="text-xs text-cy-gray-400">{pm.detail}</div>
              </div>
              {!pm.default && (
                <button className="text-xs text-cy-gray-400 hover:text-white transition-colors">Set default</button>
              )}
            </div>
          ))}
          <div className="p-4 rounded-xl border border-dashed border-cy-glass-border flex items-center justify-between">
            <span className="text-sm text-cy-gray-400">Add another payment method</span>
            <button className="text-sm text-cy-orange hover:text-cy-orange-light flex items-center gap-1.5">
              Add <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="flex items-start gap-2 p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
            <AlertCircle className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-cy-gray-300">
              For enterprise invoices or custom payment terms, contact your account manager at{" "}
              <a href="mailto:billing@cy-com.com" className="text-blue-400 hover:text-blue-300">billing@cy-com.com</a>
            </p>
          </div>
        </div>
      )}

      {/* Billing summary */}
      {activeTab === "summary" && (
        <div className="space-y-4">
          <div className="glass-card p-5 rounded-xl">
            <h2 className="font-heading font-semibold text-white mb-4">Current Subscription Costs</h2>
            <div className="space-y-3 mb-4">
              {[
                { name: "CyMed Hospital — Advanced", monthly: 3600, annual: 43200 },
                { name: "CyMed Pharmacy — Clinical", monthly: 319, annual: 3828 },
                { name: "CyCom ERP — Enterprise", monthly: 1999, annual: 23988 },
              ].map((line) => (
                <div key={line.name} className="flex items-center justify-between py-2 border-b border-cy-glass-border last:border-0">
                  <span className="text-sm text-cy-gray-300">{line.name}</span>
                  <div className="text-right">
                    <div className="text-sm font-medium text-white">${line.monthly.toLocaleString()}/mo</div>
                    <div className="text-xs text-cy-gray-400">${line.annual.toLocaleString()}/yr</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between pt-3 border-t border-cy-glass-border">
              <div>
                <div className="font-semibold text-white">Total (annual)</div>
                <div className="text-xs text-emerald-400">20% annual discount applied — saving ~$23,754/yr</div>
              </div>
              <div className="text-right">
                <div className="text-xl font-heading font-bold text-white">$71,016/yr</div>
                <div className="text-xs text-cy-gray-400">$5,918/mo equiv.</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
