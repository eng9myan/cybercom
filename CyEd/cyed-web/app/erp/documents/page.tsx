"use client";

import { useEffect, useMemo, useState } from "react";
import { FileSignature, Send, ShieldCheck, Clock } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Loading, Field, Empty } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge, Modal } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { AU_LOCALE } from "@/lib/portal";

type Signatory = {
  id: string; name: string; email: string; role: string; order: number;
  status: string; signed_at?: string | null; typed_signature?: string;
};
type Doc = {
  id: string; title: string; doc_type: string; body?: string; status: string;
  due_date?: string | null; content_hash?: string; verified?: boolean;
  signed_count?: number; pending_count?: number; signatories?: Signatory[];
};
type AuditEvent = { id: string; action: string; actor: string; detail?: string; created_at: string };

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [sel, setSel] = useState<Doc | null>(null);
  const [audit, setAudit] = useState<AuditEvent[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const [title, setTitle] = useState("");
  const [docType, setDocType] = useState("staff_contract");
  const [body, setBody] = useState("");
  const [addSig, setAddSig] = useState(false);
  const [sigName, setSigName] = useState("");
  const [sigEmail, setSigEmail] = useState("");
  const [sigRole, setSigRole] = useState("staff");
  const [signOpen, setSignOpen] = useState(false);
  const [typed, setTyped] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const d = await cyed.list<Doc>("docsign/documents/");
      setDocs(d);
      if (sel) setSel(d.find((x) => x.id === sel.id) || null);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const open = async (d: Doc) => {
    setAudit(null);
    try {
      setSel(await cyed.get<Doc>(`docsign/documents/${d.id}/`));
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not open document", "bad");
    }
  };

  const stats = useMemo(() => ({
    total: docs.length,
    awaiting: docs.filter((d) => ["sent", "partially_signed"].includes(d.status)).length,
    completed: docs.filter((d) => d.status === "completed").length,
    drafts: docs.filter((d) => d.status === "draft").length,
  }), [docs]);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const d = await cyed.create<Doc>("docsign/documents/", { title, doc_type: docType, body });
      toast.push("Document drafted");
      setTitle(""); setBody("");
      await load();
      open(d);
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Could not create document", "bad");
    }
  };

  const addSignatory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sel) return;
    try {
      await cyed.action(`docsign/documents/${sel.id}/signatories/`, {
        name: sigName, email: sigEmail, role: sigRole, order: (sel.signatories?.length || 0) + 1,
      });
      toast.push(`${sigName} added as a signatory`);
      setAddSig(false); setSigName(""); setSigEmail("");
      open(sel);
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Could not add signatory", "bad");
    }
  };

  const act = async (action: string, ok: string, body: Record<string, unknown> = {}) => {
    if (!sel) return;
    try {
      await cyed.action(`docsign/documents/${sel.id}/${action}/`, body);
      toast.push(ok);
      await load();
      open(sel);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Action failed", "bad");
    }
  };

  const showAudit = async () => {
    if (!sel) return;
    try {
      const data = await cyed.get<{ events: AuditEvent[] }>(`docsign/documents/${sel.id}/audit/`);
      setAudit(data.events || []);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not load audit trail", "bad");
    }
  };

  if (loading) return <Loading label="Loading documents…" />;

  const docCols: Column<Doc>[] = [
    { key: "title", header: "Document", render: (d) => <span style={{ fontWeight: 600 }}>{d.title}</span> },
    { key: "type", header: "Type", width: 180, render: (d) => <span className="pill" style={{ textTransform: "capitalize" }}>{d.doc_type.replace(/_/g, " ")}</span> },
    {
      key: "signed", header: "Signed", width: 110, align: "right",
      render: (d) => `${d.signed_count ?? 0}/${(d.signed_count ?? 0) + (d.pending_count ?? 0)}`,
    },
    { key: "status", header: "Status", width: 160, render: (d) => <Badge value={d.status} /> },
    { key: "act", header: "", align: "right", render: (d) => <button className="btn btn-ghost" onClick={() => open(d)}>Open</button> },
  ];

  return (
    <div>
      <PageHeader
        title="Document Sign"
        subtitle="E-signature for staff contracts, permission slips and consent forms — sealed with a hash, with a full audit trail."
      />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Documents" value={stats.total} accent="cyan" icon={<FileSignature size={17} />} />
        <StatCard label="Awaiting signature" value={stats.awaiting} accent="violet" icon={<Clock size={17} />} />
        <StatCard label="Completed" value={stats.completed} accent="blue" icon={<ShieldCheck size={17} />} />
        <StatCard label="Drafts" value={stats.drafts} accent="cyan" icon={<Send size={17} />} />
      </div>

      {error && <ErrorNote error={error} />}

      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 20, alignItems: "start" }}>
        <Panel title="New document">
          <form onSubmit={create} className="space-y-3">
            <Field label="Title"><input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required /></Field>
            <Field label="Type">
              <select className="input" value={docType} onChange={(e) => setDocType(e.target.value)}>
                <option value="staff_contract">Staff contract</option>
                <option value="permission_slip">Excursion permission slip</option>
                <option value="consent_form">Parent consent form</option>
                <option value="policy">Policy acknowledgement</option>
                <option value="other">Other</option>
              </select>
            </Field>
            <Field label="Body"><textarea className="input" rows={5} value={body} onChange={(e) => setBody(e.target.value)} /></Field>
            <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }}>Create draft</button>
          </form>
        </Panel>

        <div className="space-y-4">
          <DataTable columns={docCols} rows={docs} filterKeys={["title"]} emptyLabel="No documents yet." />

          {sel && (
            <Panel
              title={<div className="font-semibold">{sel.title} · <Badge value={sel.status} /></div>}
              action={
                <div style={{ display: "flex", gap: 8 }}>
                  {sel.status === "draft" && (
                    <>
                      <button className="btn btn-ghost" onClick={() => setAddSig(true)}>Add signatory</button>
                      <button className="btn btn-primary" onClick={() => act("send", "Sent — document sealed")}>Send</button>
                    </>
                  )}
                  {["sent", "partially_signed"].includes(sel.status) && (
                    <button className="btn btn-primary" onClick={() => setSignOpen(true)}>Sign</button>
                  )}
                  <button className="btn btn-ghost" onClick={showAudit}>Audit trail</button>
                </div>
              }
            >
              {sel.content_hash && (
                <div className="mb-3" style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  <span className={`status ${sel.verified ? "status-ok" : "status-bad"}`}>
                    {sel.verified ? "verified · untampered" : "ALTERED AFTER SENDING"}
                  </span>
                  <span className="text-xs" style={{ color: "var(--faint)", wordBreak: "break-all" }}>
                    SHA-256 {sel.content_hash.slice(0, 32)}…
                  </span>
                </div>
              )}

              <div className="label mb-2">Signatories</div>
              {(sel.signatories || []).length === 0 ? (
                <div style={{ fontSize: 13, color: "var(--faint)" }}>None yet — add at least one before sending.</div>
              ) : (
                <div className="space-y-1">
                  {(sel.signatories || []).map((s) => (
                    <div key={s.id} style={{ display: "flex", gap: 10, alignItems: "center", fontSize: 13, padding: "0.35rem 0", borderBottom: "1px solid var(--border)" }}>
                      <span className="pill">#{s.order}</span>
                      <span style={{ fontWeight: 600 }}>{s.name}</span>
                      <span style={{ color: "var(--muted)" }}>{s.email}</span>
                      <span className="pill" style={{ textTransform: "capitalize" }}>{s.role}</span>
                      <div style={{ flex: 1 }} />
                      <Badge value={s.status} />
                      {s.typed_signature && <span style={{ color: "var(--faint)", fontStyle: "italic" }}>{s.typed_signature}</span>}
                    </div>
                  ))}
                </div>
              )}

              {audit && (
                <div className="mt-4">
                  <div className="label mb-2">Audit trail</div>
                  <div className="space-y-1">
                    {audit.map((e) => (
                      <div key={e.id} style={{ display: "flex", gap: 10, fontSize: 12, color: "var(--muted)" }}>
                        <span className="pill" style={{ textTransform: "capitalize" }}>{e.action}</span>
                        <span>{e.actor || "system"}</span>
                        <div style={{ flex: 1 }} />
                        <span style={{ color: "var(--faint)" }}>{new Date(e.created_at).toLocaleString(AU_LOCALE)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Panel>
          )}
        </div>
      </div>

      <Modal open={addSig} onClose={() => setAddSig(false)} title="Add signatory">
        <form onSubmit={addSignatory} className="space-y-3">
          <Field label="Name"><input className="input" value={sigName} onChange={(e) => setSigName(e.target.value)} required autoFocus /></Field>
          <Field label="Email"><input className="input" type="email" value={sigEmail} onChange={(e) => setSigEmail(e.target.value)} required /></Field>
          <Field label="Role">
            <select className="input" value={sigRole} onChange={(e) => setSigRole(e.target.value)}>
              <option value="staff">Staff</option>
              <option value="parent">Parent / Guardian</option>
              <option value="student">Student</option>
              <option value="other">Other</option>
            </select>
          </Field>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn btn-ghost" onClick={() => setAddSig(false)}>Cancel</button>
            <button className="btn btn-primary">Add</button>
          </div>
        </form>
      </Modal>

      <Modal open={signOpen} onClose={() => setSignOpen(false)} title="Sign document">
        <div className="space-y-3">
          <div style={{ fontSize: 13, color: "var(--muted)" }}>
            Typing your full name signs this document. The signature records what you signed, when, and from where.
          </div>
          <Field label="Type your full name"><input className="input" value={typed} onChange={(e) => setTyped(e.target.value)} autoFocus /></Field>
          <div className="flex justify-end gap-2">
            <button className="btn btn-ghost" onClick={() => setSignOpen(false)}>Cancel</button>
            <button
              className="btn btn-primary"
              disabled={!typed.trim()}
              onClick={async () => {
                await act("sign", "Signed", { typed_signature: typed });
                setSignOpen(false);
                setTyped("");
              }}
            >
              Sign
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
