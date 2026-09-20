"use client";

import { useEffect, useMemo, useState } from "react";
import { FileSignature } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { fmtDate, useMyChildren, type SignableDocument } from "@/lib/portal";

/**
 * Permission slips and consent forms this family needs to act on.
 *
 * The backend already scopes `docsign/documents/` to whatever the caller is
 * a signatory on (by email match) — this page adds nothing to that, it just
 * points the design system at it. Signing/declining is authorized server-
 * side against the caller's own signatory row, so a wrong click here can
 * fail with a clear error rather than silently succeeding for someone else.
 */
export default function ConsentsPage() {
  const { children } = useMyChildren();
  const [docs, setDocs] = useState<SignableDocument[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [signing, setSigning] = useState<SignableDocument | null>(null);
  const [typedName, setTypedName] = useState("");
  const [declining, setDeclining] = useState<SignableDocument | null>(null);
  const [declineReason, setDeclineReason] = useState("");
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      setDocs(await cyed.list<SignableDocument>("docsign/documents/"));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load your consent forms");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const childName = (studentId?: string | null) => {
    const c = children.find((k) => k.id === studentId);
    return c ? `${c.first_name} ${c.last_name}` : null;
  };

  const pending = useMemo(
    () => (docs ?? []).filter((d) => d.status === "sent" || d.status === "partially_signed"),
    [docs],
  );
  const done = useMemo(
    () => (docs ?? []).filter((d) => d.status === "completed" || d.status === "declined" || d.status === "voided"),
    [docs],
  );

  const confirmSign = async () => {
    if (!signing) return;
    if (!typedName.trim()) {
      toast.push("Type your full name to sign", "bad");
      return;
    }
    setBusyId(signing.id);
    try {
      await cyed.action(`docsign/documents/${signing.id}/sign/`, { typed_signature: typedName.trim() });
      toast.push(`Signed: ${signing.title}`);
      setSigning(null);
      setTypedName("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not sign this document", "bad");
    } finally {
      setBusyId(null);
    }
  };

  const confirmDecline = async () => {
    if (!declining) return;
    setBusyId(declining.id);
    try {
      await cyed.action(`docsign/documents/${declining.id}/decline/`, { reason: declineReason });
      toast.push(`Declined: ${declining.title}`);
      setDeclining(null);
      setDeclineReason("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not decline this document", "bad");
    } finally {
      setBusyId(null);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Consents" subtitle="Permission slips and forms needing your signature" />

      <Panel title={`Needs your action${pending.length ? ` (${pending.length})` : ""}`}>
        {pending.length === 0 ? (
          <Empty label="Nothing needs signing right now." />
        ) : (
          pending.map((d) => (
            <div
              key={d.id}
              style={{
                display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "center",
                justifyContent: "space-between", padding: "0.7rem 0", borderBottom: "1px solid var(--border)",
              }}
            >
              <div>
                <div style={{ fontWeight: 650 }}>{d.title}</div>
                <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                  {childName(d.student) ? `${childName(d.student)} · ` : ""}
                  {d.due_date ? `Due ${fmtDate(d.due_date)}` : "No due date"}
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                <Badge value={d.status} />
                <button
                  className="btn"
                  disabled={busyId === d.id}
                  onClick={() => { setDeclining(d); setDeclineReason(""); }}
                >
                  Decline
                </button>
                <button
                  className="btn btn-primary"
                  disabled={busyId === d.id}
                  onClick={() => { setSigning(d); setTypedName(""); }}
                >
                  Review & sign
                </button>
              </div>
            </div>
          ))
        )}
      </Panel>

      {done.length > 0 && (
        <Panel title="Past forms">
          {done.map((d) => (
            <div
              key={d.id}
              style={{
                display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "center",
                justifyContent: "space-between", padding: "0.6rem 0", borderBottom: "1px solid var(--border)",
              }}
            >
              <div>
                <div style={{ fontWeight: 600 }}>{d.title}</div>
                <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                  {childName(d.student) ? `${childName(d.student)} · ` : ""}
                  {d.due_date ? `Due ${fmtDate(d.due_date)}` : ""}
                </div>
              </div>
              <Badge value={d.status} />
            </div>
          ))}
        </Panel>
      )}

      {signing && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={signing.title}
          onClick={() => setSigning(null)}
          style={{
            position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
            display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50, padding: "1rem",
          }}
        >
          <div
            className="card"
            onClick={(e) => e.stopPropagation()}
            style={{ width: "min(560px, 92vw)", padding: "1.4rem", display: "grid", gap: "0.9rem" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <FileSignature size={18} />
              <strong>{signing.title}</strong>
            </div>
            <div
              style={{
                whiteSpace: "pre-wrap", fontSize: "0.9rem", color: "var(--muted)",
                maxHeight: 260, overflowY: "auto", border: "1px solid var(--border)",
                borderRadius: 8, padding: "0.75rem",
              }}
            >
              {signing.body}
            </div>
            <label className="label">Type your full name to sign</label>
            <input
              className="input"
              value={typedName}
              onChange={(e) => setTypedName(e.target.value)}
              placeholder="Full name"
              autoFocus
            />
            <div style={{ display: "flex", gap: "0.6rem", justifyContent: "flex-end" }}>
              <button className="btn" onClick={() => setSigning(null)}>Cancel</button>
              <button className="btn btn-primary" disabled={busyId === signing.id} onClick={confirmSign}>
                {busyId === signing.id ? "Signing…" : "Sign"}
              </button>
            </div>
          </div>
        </div>
      )}

      {declining && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={`Decline ${declining.title}`}
          onClick={() => setDeclining(null)}
          style={{
            position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
            display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50, padding: "1rem",
          }}
        >
          <div
            className="card"
            onClick={(e) => e.stopPropagation()}
            style={{ width: "min(460px, 92vw)", padding: "1.4rem", display: "grid", gap: "0.9rem" }}
          >
            <strong>Decline &quot;{declining.title}&quot;</strong>
            <label className="label">Reason (optional)</label>
            <input
              className="input"
              value={declineReason}
              onChange={(e) => setDeclineReason(e.target.value)}
              placeholder="Let the school know why"
              autoFocus
            />
            <div style={{ display: "flex", gap: "0.6rem", justifyContent: "flex-end" }}>
              <button className="btn" onClick={() => setDeclining(null)}>Cancel</button>
              <button className="btn btn-primary" disabled={busyId === declining.id} onClick={confirmDecline}>
                {busyId === declining.id ? "Declining…" : "Confirm decline"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
