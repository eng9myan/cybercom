"use client";

import { useEffect, useState } from "react";
import { Send } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { AU_LOCALE, type PortalThread } from "@/lib/portal";

type Message = {
  id: string;
  sender_kind: string;
  sender_name: string;
  sender_email: string;
  body: string;
  sent_at: string;
};

type ThreadDetail = {
  id: string;
  subject: string;
  is_closed: boolean;
  messages: Message[];
  participants: { display_name: string; email: string; party_kind: string }[];
};

/**
 * Two-way messaging with the school.
 *
 * Reply-only by design: conversations are started by staff, who know which
 * teacher a question belongs to. A parent composing into the void — picking a
 * recipient from a staff directory — is how messages end up unanswered.
 */
export default function PortalMessagesPage() {
  const [threads, setThreads] = useState<PortalThread[]>([]);
  const [open, setOpen] = useState<ThreadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const toast = useToast();

  const loadInbox = async () => {
    try {
      const inbox = await cyed.get<{ results: PortalThread[] }>("messaging/threads/inbox/");
      setThreads(inbox.results ?? []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load your messages");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInbox();
  }, []);

  const openThread = async (id: string) => {
    try {
      const detail = await cyed.get<ThreadDetail>(`messaging/threads/${id}/`);
      setOpen(detail);
      await cyed.action(`messaging/threads/${id}/mark-read/`);
      await loadInbox();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not open that conversation");
    }
  };

  const send = async () => {
    if (!open || !reply.trim()) return;
    setSending(true);
    try {
      await cyed.action(`messaging/threads/${open.id}/reply/`, { body: reply });
      setReply("");
      await openThread(open.id);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not send your reply");
    } finally {
      setSending(false);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  if (open) {
    return (
      <div style={{ display: "grid", gap: "1rem" }}>
        <PageHeader
          title={open.subject}
          subtitle={open.participants.map((p) => p.display_name || p.email).join(", ")}
          action={
            <button className="btn" onClick={() => setOpen(null)}>
              Back
            </button>
          }
        />

        <Panel>
          <div style={{ display: "grid", gap: "0.9rem" }}>
            {open.messages.map((m) => {
              const fromSchool = m.sender_kind === "staff";
              return (
                <div
                  key={m.id}
                  style={{
                    justifySelf: fromSchool ? "start" : "end",
                    maxWidth: "min(38rem, 88%)",
                    background: fromSchool ? "var(--panel-2)" : "var(--panel)",
                    border: "1px solid var(--border)",
                    borderRadius: 14,
                    padding: "0.7rem 0.9rem",
                  }}
                >
                  <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: 4 }}>
                    {m.sender_name || m.sender_email} ·{" "}
                    {new Date(m.sent_at).toLocaleString(AU_LOCALE)}
                  </div>
                  <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{m.body}</div>
                </div>
              );
            })}
          </div>
        </Panel>

        {open.is_closed ? (
          <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
            This conversation has been closed by the school. Contact the office if you need to
            reopen it.
          </p>
        ) : (
          <Panel title="Reply">
            <textarea
              className="input"
              rows={4}
              value={reply}
              onChange={(e) => setReply(e.target.value)}
              placeholder="Write your reply…"
              style={{ width: "100%", resize: "vertical" }}
            />
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.6rem" }}>
              <button
                className="btn btn-primary"
                disabled={sending || !reply.trim()}
                onClick={send}
              >
                <Send size={15} style={{ marginRight: 6 }} />
                {sending ? "Sending…" : "Send"}
              </button>
            </div>
          </Panel>
        )}
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Messages" subtitle="Conversations with the school" />

      {threads.length === 0 ? (
        <Empty label="No messages yet. The school will start a conversation when they need to reach you." />
      ) : (
        <Panel pad={false}>
          {threads.map((t) => (
            <button
              key={t.thread}
              onClick={() => openThread(t.thread)}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: "0.9rem 1.1rem",
                background: "transparent",
                border: 0,
                borderBottom: "1px solid var(--border)",
                color: "inherit",
                font: "inherit",
                cursor: "pointer",
              }}
            >
              <div style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
                <strong style={{ fontWeight: t.unread ? 800 : 600 }}>{t.subject}</strong>
                {t.unread > 0 && <Badge value="unread" />}
                {t.is_closed && <Badge value="completed" />}
              </div>
              <div
                style={{
                  fontSize: "0.85rem",
                  color: "var(--muted)",
                  marginTop: 2,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {t.last_sender}: {t.last_message_preview}
              </div>
            </button>
          ))}
        </Panel>
      )}
    </div>
  );
}
