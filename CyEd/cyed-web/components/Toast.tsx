"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { CheckCircle2, AlertTriangle, Info, X } from "lucide-react";

type Kind = "ok" | "bad" | "info";
type Toast = { id: number; kind: Kind; msg: string };

type Ctx = { push: (msg: string, kind?: Kind) => void };
const ToastCtx = createContext<Ctx>({ push: () => {} });

export function useToast() {
  return useContext(ToastCtx);
}

let seq = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback((msg: string, kind: Kind = "ok") => {
    const id = ++seq;
    setToasts((t) => [...t, { id, kind, msg }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4200);
  }, []);

  return (
    <ToastCtx.Provider value={{ push }}>
      {children}
      <div className="toast-wrap" role="region" aria-label="Notifications" aria-live="polite">
        {toasts.map((t) => (
          <ToastCard key={t.id} toast={t} onClose={() => setToasts((x) => x.filter((y) => y.id !== t.id))} />
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

function ToastCard({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  useEffect(() => {}, []);
  const Icon = toast.kind === "ok" ? CheckCircle2 : toast.kind === "bad" ? AlertTriangle : Info;
  const color = toast.kind === "ok" ? "var(--ok)" : toast.kind === "bad" ? "var(--bad)" : "var(--cyan)";
  return (
    <div className={`toast ${toast.kind}`}>
      <Icon size={18} style={{ color, flexShrink: 0, marginTop: 1 }} aria-hidden="true" />
      <span style={{ flex: 1 }}>{toast.msg}</span>
      <button onClick={onClose} aria-label="Dismiss" style={{ color: "var(--faint)", cursor: "pointer" }}>
        <X size={14} />
      </button>
    </div>
  );
}
