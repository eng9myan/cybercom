"use client";

import { useState } from "react";
import {
  AlertCircle, CheckCircle2, Clock, Plus, X,
  ChevronDown, ChevronUp, MessageSquare, ArrowRight,
} from "lucide-react";

const TICKETS = [
  {
    id: "TKT-1042",
    title: "Lab integration HL7 mapping question",
    product: "CyMed Hospital",
    priority: "medium",
    status: "open",
    created: "2026-07-02",
    updated: "2h ago",
    messages: [
      { from: "you", text: "We're trying to map our HL7 v2 OBR segment to the CyMed lab order fields. The LOINC codes aren't resolving for microbiology orders specifically.", ts: "2026-07-02 09:14" },
      { from: "support", text: "Hi — microbiology orders use a secondary LOINC mapping table. I'm pulling the configuration guide for your version. Will send in ~30 mins.", ts: "2026-07-02 09:41" },
    ],
  },
  {
    id: "TKT-1038",
    title: "Pharmacy auto-verification threshold adjustment",
    product: "CyMed Pharmacy",
    priority: "low",
    status: "resolved",
    created: "2026-06-28",
    updated: "3d ago",
    messages: [
      { from: "you", text: "Need to lower the auto-verify threshold for controlled substances from 95% confidence to 98%.", ts: "2026-06-28 14:22" },
      { from: "support", text: "Updated in your instance config. The new threshold is live — please test on your next dispense cycle.", ts: "2026-06-28 16:05" },
    ],
  },
  {
    id: "TKT-1031",
    title: "ERP payroll GOSI deduction formula",
    product: "CyCom ERP",
    priority: "high",
    status: "resolved",
    created: "2026-06-15",
    updated: "15d ago",
    messages: [
      { from: "you", text: "The GOSI employer contribution is calculating at 10% instead of 11.5% for Saudi nationals.", ts: "2026-06-15 10:00" },
      { from: "support", text: "This was a localization config gap for the SA payroll table. Hotfix deployed to your instance. Verified correct: 11.5%.", ts: "2026-06-15 14:33" },
    ],
  },
];

const PRIORITY_COLORS: Record<string, string> = {
  high: "text-red-400 bg-red-500/10 border-red-500/20",
  medium: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  low: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
};

export default function SupportPage() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [form, setForm] = useState({ subject: "", product: "", priority: "medium", message: "" });
  const [replyText, setReplyText] = useState("");

  return (
    <div>
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-heading font-semibold text-white mb-1">Support</h1>
          <p className="text-sm text-cy-gray-400">Track and manage your support tickets</p>
        </div>
        <button
          onClick={() => setShowNew(!showNew)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-cy-orange hover:bg-cy-orange-light text-white transition-colors"
        >
          <Plus className="w-4 h-4" /> New Ticket
        </button>
      </div>

      {/* New ticket form */}
      {showNew && (
        <div className="glass-card p-5 rounded-xl mb-6 border border-cy-orange/20">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-heading font-semibold text-white">New Support Ticket</h2>
            <button onClick={() => setShowNew(false)} className="p-1.5 rounded-lg hover:bg-cy-glass-border/50 text-cy-gray-400 hover:text-white transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-3">
            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-cy-gray-400 mb-1.5">Product</label>
                <select
                  className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white outline-none focus:border-cy-orange border border-cy-glass-border transition-colors bg-cy-dark"
                  value={form.product}
                  onChange={(e) => setForm((f) => ({ ...f, product: e.target.value }))}
                >
                  <option value="">Select product</option>
                  {["CyMed Hospital", "CyMed Pharmacy", "CyCom ERP"].map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-cy-gray-400 mb-1.5">Priority</label>
                <select
                  className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white outline-none focus:border-cy-orange border border-cy-glass-border transition-colors bg-cy-dark"
                  value={form.priority}
                  onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High / Urgent</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs text-cy-gray-400 mb-1.5">Subject *</label>
              <input
                className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-cy-gray-500 outline-none focus:border-cy-orange border border-cy-glass-border transition-colors"
                placeholder="Brief description of your issue"
                value={form.subject}
                onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs text-cy-gray-400 mb-1.5">Description *</label>
              <textarea
                rows={4}
                className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-cy-gray-500 outline-none focus:border-cy-orange border border-cy-glass-border transition-colors resize-none"
                placeholder="Describe the issue in detail — steps to reproduce, expected vs actual behavior, any error messages..."
                value={form.message}
                onChange={(e) => setForm((f) => ({ ...f, message: e.target.value }))}
              />
            </div>
            <div className="flex gap-3">
              <button
                disabled={!form.subject || !form.product || !form.message}
                className="px-5 py-2.5 rounded-xl text-sm font-medium bg-cy-orange hover:bg-cy-orange-light text-white transition-all disabled:opacity-40"
              >
                Submit Ticket
              </button>
              <button onClick={() => setShowNew(false)} className="px-5 py-2.5 rounded-xl text-sm text-cy-gray-400 border border-cy-glass-border hover:text-white transition-colors">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SLA info */}
      <div className="grid sm:grid-cols-3 gap-3 mb-6">
        {[
          { label: "High priority", sla: "< 2 hours", icon: AlertCircle, color: "text-red-400" },
          { label: "Medium priority", sla: "< 8 hours", icon: Clock, color: "text-amber-400" },
          { label: "Low priority", sla: "< 24 hours", icon: MessageSquare, color: "text-emerald-400" },
        ].map(({ label, sla, icon: Icon, color }) => (
          <div key={label} className="glass-card px-4 py-3 rounded-xl flex items-center gap-3">
            <Icon className={`w-4 h-4 ${color} flex-shrink-0`} />
            <div>
              <div className="text-xs font-medium text-white">{label}</div>
              <div className="text-xs text-cy-gray-400">First response {sla}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Ticket list */}
      <div className="space-y-3">
        {TICKETS.map((t) => {
          const expanded = expandedId === t.id;
          return (
            <div key={t.id} className="glass-card rounded-xl overflow-hidden">
              <button
                onClick={() => setExpandedId(expanded ? null : t.id)}
                className="w-full text-left p-4 flex items-center gap-3"
              >
                {t.status === "open"
                  ? <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                  : <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white mb-0.5">{t.title}</div>
                  <div className="flex items-center gap-3 text-xs text-cy-gray-400">
                    <span>{t.id}</span>
                    <span>{t.product}</span>
                    <span>{t.updated}</span>
                  </div>
                </div>
                <span className={`hidden sm:inline-flex text-xs px-2 py-0.5 rounded-full border ${PRIORITY_COLORS[t.priority]} capitalize flex-shrink-0`}>
                  {t.priority}
                </span>
                {expanded ? <ChevronUp className="w-4 h-4 text-cy-gray-400 flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-cy-gray-400 flex-shrink-0" />}
              </button>

              {expanded && (
                <div className="border-t border-cy-glass-border p-4 space-y-3">
                  {t.messages.map((msg, i) => (
                    <div key={i} className={`flex gap-3 ${msg.from === "you" ? "flex-row-reverse" : ""}`}>
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${msg.from === "you" ? "bg-cy-orange/20 text-cy-orange" : "bg-blue-500/20 text-blue-400"}`}>
                        {msg.from === "you" ? "Y" : "S"}
                      </div>
                      <div className={`flex-1 max-w-lg ${msg.from === "you" ? "text-right" : ""}`}>
                        <div className={`inline-block text-sm px-4 py-2.5 rounded-xl ${msg.from === "you" ? "bg-cy-orange/15 text-white" : "bg-cy-glass-border text-cy-gray-200"}`}>
                          {msg.text}
                        </div>
                        <div className="text-xs text-cy-gray-500 mt-1">{msg.ts}</div>
                      </div>
                    </div>
                  ))}

                  {t.status === "open" && (
                    <div className="flex gap-2 pt-2">
                      <input
                        className="flex-1 glass-card rounded-lg px-3 py-2 text-sm text-white placeholder:text-cy-gray-500 outline-none border border-cy-glass-border focus:border-cy-orange transition-colors"
                        placeholder="Type a reply..."
                        value={replyText}
                        onChange={(e) => setReplyText(e.target.value)}
                      />
                      <button className="px-4 py-2 rounded-lg bg-cy-orange hover:bg-cy-orange-light text-white text-sm font-medium transition-colors">
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
