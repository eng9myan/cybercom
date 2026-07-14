"use client";

import { useState, useEffect } from "react";
import { CheckCircle2, XCircle, Clock, Truck, ShieldAlert, Sparkles, MessageSquare, Plus, RefreshCw, Send } from "lucide-react";

export default function CustomerPortalPage() {
  const [quotations, setQuotations] = useState([]);
  const [orders, setOrders] = useState([]);
  const [communications, setCommunications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Communication Form
  const [newComm, setNewComm] = useState({
    customer_name: "",
    subject: "",
    content: "",
    channel: "EMAIL"
  });

  const fetchData = async () => {
    setLoading(true);
    setError("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");
    const username = localStorage.getItem("username") || "Valued Customer";

    try {
      // 1. Fetch Quotations
      const qRes = await fetch("/api/v1/sales/quotations/", {
        headers: { "Authorization": `Bearer ${token}`, "X-Tenant-ID": tenantId }
      });
      if (qRes.ok) setQuotations(await qRes.json());

      // 2. Fetch Orders
      const oRes = await fetch("/api/v1/sales/orders/", {
        headers: { "Authorization": `Bearer ${token}`, "X-Tenant-ID": tenantId }
      });
      if (oRes.ok) setOrders(await oRes.json());

      // 3. Fetch Communications
      const cRes = await fetch("/api/v1/sales/communications/", {
        headers: { "Authorization": `Bearer ${token}`, "X-Tenant-ID": tenantId }
      });
      if (cRes.ok) setCommunications(await cRes.json());

      setNewComm(prev => ({ ...prev, customer_name: username }));

    } catch (err) {
      setError("Failed to fetch customer data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuoteStatus = async (quoteId, newStatus) => {
    setError("");
    setSuccess("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");
    const quote = quotations.find(q => q.id === quoteId);

    try {
      const response = await fetch(`/api/v1/sales/quotations/${quoteId}/`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId
        },
        body: JSON.stringify({
          ...quote,
          status: newStatus
        })
      });

      if (response.ok) {
        setSuccess(`Quotation has been successfully ${newStatus === "ACCEPTED" ? "accepted" : "declined"}.`);
        fetchData();
      } else {
        throw new Error("Failed to process quotation request.");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSubmitTicket = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    if (!newComm.subject || !newComm.content) {
      setError("Please specify the ticket subject and description content.");
      return;
    }

    try {
      const response = await fetch("/api/v1/sales/communications/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId
        },
        body: JSON.stringify(newComm)
      });

      if (response.ok) {
        setSuccess("Support ticket / query submitted successfully to sales reps!");
        setNewComm(prev => ({ ...prev, subject: "", content: "" }));
        fetchData();
      } else {
        throw new Error("Failed to post message.");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="w-8 h-8 border-4 border-[var(--color-line)] border-t-orange-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 text-[var(--color-ink)] animate-fade font-sans">
      
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">Customer Hub Portal</h1>
          <p className="text-xs text-[var(--color-ink-muted)]">Review pending business bids, verify order logistics, and submit customer service queries.</p>
        </div>
        <button
          onClick={fetchData}
          className="w-10 h-10 bg-white border border-[var(--color-line)] rounded-xl flex items-center justify-center text-[var(--color-ink-muted)] hover:text-white transition hover:bg-[var(--color-surface-2)]"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {error && (
        <div className="bg-red-950/40 border border-red-800 text-red-400 p-4 rounded-xl text-xs flex items-center gap-2">
          <ShieldAlert className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="bg-emerald-950/40 border border-emerald-800 text-emerald-400 p-4 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{success}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Side: Quotes & Orders */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Active Quotes */}
          <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl space-y-4">
            <span className="text-[10px] text-[var(--color-ink-soft)] uppercase tracking-widest font-bold block mb-2">Pending Bids / Quotations</span>
            
            {quotations.filter(q => ["SUBMITTED", "APPROVED", "SENT"].includes(q.status)).length === 0 ? (
              <p className="text-xs text-[var(--color-ink-muted)]">No pending quotes await your review.</p>
            ) : (
              <div className="space-y-4">
                {quotations.filter(q => ["SUBMITTED", "APPROVED", "SENT"].includes(q.status)).map(q => (
                  <div key={q.id} className="bg-white border border-[var(--color-line)] p-5 rounded-xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-[var(--color-ink)] font-mono">{q.quotation_number}</span>
                        <span className="text-[10px] bg-white text-[var(--color-ink-muted)] border border-[var(--color-line)] px-2 py-0.5 rounded-full">{q.status}</span>
                      </div>
                      <p className="text-[11px] text-[var(--color-ink-soft)] mt-1">Total amount due: <strong className="text-[#ED6C00] font-mono">{parseFloat(q.total_amount).toFixed(2)} JOD</strong></p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleUpdateQuoteStatus(q.id, "REJECTED")}
                        className="bg-white border border-[var(--color-line)] hover:bg-[var(--color-surface-2)] text-red-400 px-3 py-1.5 rounded-lg text-[10px] font-bold transition flex items-center gap-1"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        Decline
                      </button>
                      <button
                        onClick={() => handleUpdateQuoteStatus(q.id, "ACCEPTED")}
                        className="bg-[#ED6C00] hover:bg-[#ED6C00] text-white px-3 py-1.5 rounded-lg text-[10px] font-bold transition flex items-center gap-1"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Accept Quote
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Delivery Tracks */}
          <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl space-y-4">
            <span className="text-[10px] text-[var(--color-ink-soft)] uppercase tracking-widest font-bold block mb-2">Active Order Dispatches</span>
            
            {orders.length === 0 ? (
              <p className="text-xs text-[var(--color-ink-muted)]">No active orders or logistics records found.</p>
            ) : (
              <div className="space-y-4">
                {orders.map(o => (
                  <div key={o.id} className="bg-white border border-[var(--color-line)] p-5 rounded-xl space-y-4">
                    <div className="flex justify-between items-center text-xs">
                      <div>
                        <span className="font-bold text-[var(--color-ink)] font-mono">{o.order_number}</span>
                        <span className="text-[9px] text-[var(--color-ink-muted)] block">Total: {parseFloat(o.total_amount).toFixed(2)} JOD</span>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span className="px-2 py-0.5 rounded-full text-[9px] font-bold border bg-white text-[var(--color-ink-muted)] border-[var(--color-line)]">
                          {o.status}
                        </span>
                      </div>
                    </div>

                    {/* Progress tracking line */}
                    <div className="grid grid-cols-3 gap-2 border-t border-[var(--color-line)] pt-3 relative">
                      <div className="flex items-center gap-2">
                        <Clock className={`w-4 h-4 ${o.fulfillment_status !== "UNFULFILLED" ? "text-[#ED6C00]" : "text-[var(--color-ink-muted)]"}`} />
                        <div className="text-[10px] font-bold text-[var(--color-ink-muted)]">
                          <span>Fulfill: {o.fulfillment_status}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Truck className={`w-4 h-4 ${o.delivery_status !== "PENDING" ? "text-blue-400" : "text-[var(--color-ink-muted)]"}`} />
                        <div className="text-[10px] font-bold text-[var(--color-ink-muted)]">
                          <span>Delivery: {o.delivery_status}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <CheckCircle2 className={`w-4 h-4 ${o.status === "COMPLETED" ? "text-emerald-400" : "text-[var(--color-ink-muted)]"}`} />
                        <div className="text-[10px] font-bold text-[var(--color-ink-muted)]">
                          <span>Invoice: {o.invoice_status}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Right Side: Communication Support */}
        <div className="space-y-8">
          
          {/* Submit Support Message */}
          <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl space-y-4">
            <span className="text-[10px] text-[var(--color-ink-soft)] uppercase tracking-widest font-bold block">Submit Support Request</span>
            
            <form onSubmit={handleSubmitTicket} className="space-y-3">
              <div className="space-y-1">
                <label className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Category Subject</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Quotation delivery query"
                  value={newComm.subject}
                  onChange={(e) => setNewComm({ ...newComm, subject: e.target.value })}
                  className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Channel</label>
                <select
                  value={newComm.channel}
                  onChange={(e) => setNewComm({ ...newComm, channel: e.target.value })}
                  className="w-full bg-white border border-[var(--color-line)] rounded-xl px-3 py-2 text-xs text-[var(--color-ink-soft)] focus:outline-none"
                >
                  <option value="EMAIL">Email Representative</option>
                  <option value="SMS">SMS Notification</option>
                  <option value="WHATSAPP">WhatsApp Message</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Detailed query</label>
                <textarea
                  required
                  rows="4"
                  placeholder="Please write details about your query..."
                  value={newComm.content}
                  onChange={(e) => setNewComm({ ...newComm, content: e.target.value })}
                  className="w-full bg-white border border-[var(--color-line)] rounded-xl p-3 text-xs text-[var(--color-ink)] focus:outline-none"
                ></textarea>
              </div>

              <button
                type="submit"
                className="w-full bg-[#ED6C00] hover:bg-[#ED6C00] text-white font-bold py-2 px-4 rounded-xl text-xs flex items-center justify-center gap-1.5 transition shadow"
              >
                <Send className="w-3.5 h-3.5" />
                Send Query
              </button>
            </form>
          </div>

          {/* Communication Logs */}
          <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl space-y-4">
            <span className="text-[10px] text-[var(--color-ink-soft)] uppercase tracking-widest font-bold block">Support History logs</span>
            
            {communications.length === 0 ? (
              <p className="text-xs text-[var(--color-ink-muted)]">No previous messages logged.</p>
            ) : (
              <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                {communications.map(c => (
                  <div key={c.id} className="bg-white border border-[var(--color-line)] p-3 rounded-lg text-xs space-y-1">
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="font-bold text-[var(--color-ink-soft)] truncate w-32">{c.subject || "Message"}</span>
                      <span className="text-[#ED6C00] font-mono font-bold uppercase text-[8px]">{c.channel}</span>
                    </div>
                    <p className="text-[var(--color-ink-soft)] leading-normal text-[11px]">{c.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

      </div>

    </div>
  );
}
