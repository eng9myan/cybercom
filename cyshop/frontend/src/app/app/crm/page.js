"use client";

import { useState, useEffect } from "react";
import { Shield, Sparkles, TrendingUp, DollarSign } from "lucide-react";

export default function CrmKanbanPage() {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const stages = ["NEW", "QUALIFIED", "PROPOSAL", "NEGOTIATION", "WON", "LOST"];

  const fetchOpps = async () => {
    setLoading(true);
    setError("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const response = await fetch("/api/v1/sales/opportunities/", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId
        }
      });
      if (response.ok) {
        const data = await response.json();
        setOpportunities(data);
      } else {
        throw new Error("Failed to load pipeline");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateOppStage = async (oppId, newStage) => {
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");
    const opp = opportunities.find((o) => o.id === oppId);

    try {
      const response = await fetch(`/api/v1/sales/opportunities/${oppId}/`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId
        },
        body: JSON.stringify({
          ...opp,
          stage: newStage
        })
      });

      if (response.ok) {
        fetchOpps();
      }
    } catch (err) {
      setError("Failed to shift opportunity stage");
    }
  };

  useEffect(() => {
    fetchOpps();
  }, []);

  const getPipelineValue = () => {
    return opportunities
      .filter((o) => o.stage !== "WON" && o.stage !== "LOST")
      .reduce((sum, o) => sum + parseFloat(o.expected_revenue || 0), 0)
      .toFixed(2);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="w-8 h-8 border-4 border-[var(--color-line)] border-t-orange-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade text-[var(--color-ink)]">
      
      {error && (
        <div className="bg-red-950/40 border border-red-800 text-red-400 p-4 rounded-xl text-xs">
          {error}
        </div>
      )}

      {/* Pipeline KPI metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Pipeline Active Value</span>
            <div className="text-2xl font-extrabold font-mono text-[#ED6C00]">{getPipelineValue()} JOD</div>
          </div>
          <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center border border-[var(--color-line)]">
            <DollarSign className="w-5 h-5 text-[#ED6C00]" />
          </div>
        </div>

        <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Total Deals Tracked</span>
            <div className="text-2xl font-extrabold font-mono">{opportunities.length}</div>
          </div>
          <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center border border-[var(--color-line)]">
            <TrendingUp className="w-5 h-5 text-sky-400" />
          </div>
        </div>

        <div className="bg-white border border-[var(--color-line)] p-6 rounded-2xl flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-[var(--color-ink-muted)] uppercase tracking-widest font-bold">Closed Won Value</span>
            <div className="text-2xl font-extrabold font-mono text-emerald-400">
              {opportunities
                .filter((o) => o.stage === "WON")
                .reduce((sum, o) => sum + parseFloat(o.expected_revenue || 0), 0)
                .toFixed(2)}{" "}
              JOD
            </div>
          </div>
          <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center border border-[var(--color-line)]">
            <Sparkles className="w-5 h-5 text-emerald-400" />
          </div>
        </div>
      </div>

      {/* Kanban Board Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 overflow-x-auto pb-4">
        {stages.map((stage) => {
          const stageOpps = opportunities.filter((o) => o.stage === stage);
          return (
            <div key={stage} className="bg-white border border-[var(--color-line)] rounded-2xl p-4 min-w-[200px] flex flex-col gap-4">
              <div className="flex justify-between items-center border-b border-[var(--color-line)] pb-2">
                <span className="text-[10px] font-bold uppercase tracking-wide text-[var(--color-ink-muted)]">{stage}</span>
                <span className="bg-white border border-[var(--color-line)] px-2 py-0.5 rounded-full text-[9px] text-[var(--color-ink-muted)] font-bold font-mono">
                  {stageOpps.length}
                </span>
              </div>

              <div className="flex-1 space-y-3">
                {stageOpps.map((opp) => (
                  <div key={opp.id} className="bg-white border border-[var(--color-line)] p-4 rounded-xl shadow space-y-3 hover:border-[var(--color-ink)] transition">
                    <div>
                      <h4 className="font-bold text-xs text-[var(--color-ink)] line-clamp-1">{opp.name}</h4>
                      <span className="text-[9px] text-[var(--color-ink-muted)] font-mono">Prob: {opp.probability}%</span>
                    </div>

                    <div className="flex justify-between items-center text-[10px] font-mono font-bold text-[#ED6C00]">
                      <span>{parseFloat(opp.expected_revenue).toFixed(2)} JOD</span>
                    </div>

                    {/* Shifts stage controls */}
                    <div className="flex justify-between border-t border-[var(--color-line)] pt-2 gap-1.5">
                      <select
                        value={opp.stage}
                        onChange={(e) => updateOppStage(opp.id, e.target.value)}
                        className="w-full bg-white border border-[var(--color-line)] rounded py-1 px-1.5 text-[9px] focus:outline-none text-[var(--color-ink-muted)] font-bold"
                      >
                        {stages.map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
