"use client";
import { useState } from "react";

export interface WorkflowStep {
  action: string;
  detail: string;
}

export interface RoleWorkflow {
  role: string;
  description: string;
  steps: WorkflowStep[];
}

export function RoleWorkflowExplorer({ roleWorkflows }: { roleWorkflows: RoleWorkflow[] }) {
  const [activeIdx, setActiveIdx] = useState(0);
  const current = roleWorkflows[activeIdx];
  if (!current) return null;

  return (
    <div>
      {/* Role selector */}
      <div className="flex flex-wrap gap-2 mb-6" role="tablist">
        {roleWorkflows.map((rw, i) => (
          <button
            key={rw.role}
            role="tab"
            aria-selected={activeIdx === i}
            onClick={() => setActiveIdx(i)}
            className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all duration-150 ${
              activeIdx === i
                ? "bg-cy-orange/15 border-cy-orange/40 text-cy-orange"
                : "bg-cy-glass-bg border-cy-glass-border text-cy-gray-400 hover:text-white hover:border-cy-glass-bg-hover"
            }`}
          >
            {rw.role}
          </button>
        ))}
      </div>

      {/* Role description */}
      <p className="text-sm text-cy-gray-400 mb-8 leading-relaxed">{current.description}</p>

      {/* Steps */}
      <div className="relative">
        <div
          className="hidden lg:block absolute top-[2.2rem] left-0 right-0 h-px"
          style={{ background: "linear-gradient(to right, transparent, rgba(255,255,255,0.08), transparent)" }}
          aria-hidden="true"
        />
        <div className={`grid gap-4 ${
          current.steps.length <= 3
            ? "sm:grid-cols-2 lg:grid-cols-3"
            : current.steps.length === 4
            ? "sm:grid-cols-2 lg:grid-cols-4"
            : "sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5"
        }`}>
          {current.steps.map((step, i) => (
            <div key={step.action} className="glass-card p-5 rounded-2xl">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-heading font-bold mb-4 bg-cy-orange/10 border border-cy-orange/20 text-cy-orange flex-shrink-0">
                {String(i + 1).padStart(2, "0")}
              </div>
              <h3 className="text-sm font-heading font-semibold text-white mb-2 leading-snug">{step.action}</h3>
              <p className="text-xs text-cy-gray-400 leading-relaxed">{step.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
