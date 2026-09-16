"use client";

import { useEffect, useState } from "react";
import { Send, Plus, Archive } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { AU_LOCALE, fmtDateTime } from "@/lib/portal";

/**
 * Staff side of parent messaging.
 *
 * The counterpart to the family portal, which is reply-only: families answer
 * conversations, staff start them. Without this screen a parent's reply lands
 * nowhere anyone looks, which is worse than having no messaging at all —
 * the school looks like it is ignoring them.
 *
 * Unanswered threads sort to the top and are counted, because the number that
 * matters to a front office is "how many families are waiting on us", not how
 * many conversations exist.
 */

type Thread = {
  thread: string;
  subject: string;
  kind: string;
  student: string | null;
  is_closed: boolean;
  participants: string[];
  last_message_at: string | null;
  last_message_preview: string;
  last_sender: string;
  unread: number;
  observing: boolean;
};

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

type Student = { id: string; first_name: string; last_name: string; year_level: number };

const KIND_LABELS: Record<string, string> = {
  teacher_parent: "Teacher ↔ parent",
  teacher_student: "Teacher ↔ student",
  office_parent: "Office ↔ parent",
  staff_staff: "Staff ↔ staff",
};

export default function StaffMessagesPage() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [filter, setFilter] = useState<"waiting" | "all" | "closed">("waiting");
  const [open, setOpen] = useState<ThreadDetail | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);
  const [composing, setComposing] = useState(false);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [student, setStudent] = useState("");
  const [kind, setKind] = useState("teacher_parent");
  const toast = useToast();

  const loadInbox = async () => {
    try {
      const inbox = await cyed.get<{ results: Thread[] }>("messaging/threads/inbox/");
      const rows = inbox.results ?? [];
      setThreads(rows);
      // Land on the queue only when there *is* one. Opening on an empty
      // "waiting" filter while conversations exist reads as "messaging is
      // broken", which is the opposite of what an empty queue means.
      if (loading && !rows.some((t) => !t.is_closed && t.unread > 0)) {
        setFilter("all");
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load the inbox");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInbox();
    (async () => {
      try {
        setStudents(await cyed.list<Student>("sis/students/"));
      } catch {
        // Compose degrades; the inbox is the point of this screen.
      }
    })();
  }, []);

  const openThread = async (id: string) => {
    try {
      const detail = await cyed.get<ThreadDetail>(`messaging/threads/${id}/`);
      setOpen(detail);
      setReply("");
      await cyed.action(`messaging/threads/${id}/mark-read/`).catch(() => {
        // Observing a thread rather than participating in it is not an error.
      });
      loadInbox();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not open that conversation");
    }
  };

  const send = async () => {
    if (!open || !reply.trim()) return;
    setBusy(true);
    try {
      await cyed.action(`messaging/threads/${open.id}/reply/`, { body: reply });
      setReply("");
      await openThread(open.id);
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not send that reply");
    } finally {
      setBusy(false);
    }
  };

  const startThread = async () => {
    if (!subject.trim() || !body.trim() || !student) return;
    setBusy(true);
    try {
      // Participants are resolved server-side from the child, so a teacher
      // never has to pick the right guardian out of a directory.
      await cyed.action("messaging/threads/open/", { subject, body, kind, student });
      toast.push("Conversation started — the family can see it in their portal.");
      setComposing(false);
      setSubject("");
      setBody("");
      setStudent("");
      await loadInbox();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not start that conversation");
    } finally {
      setBusy(false);
    }
  };

  const closeThread = async () => {
    if (!open) return;
    if (!window.confirm(`Close "${open.subject}"? The family can no longer reply.`)) return;
    setBusy(true);
    try {
      await cyed.action(`messaging/threads/${open.id}/close/`);
      toast.push("Conversation closed.");
      await openThread(open.id);
      await loadInbox();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not close that conversation");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  // "Waiting on us" = a family spoke last. That is the queue, not unread count:
  // a thread someone opened and never answered is still outstanding.
  const waiting = threads.filter((t) => !t.is_closed && t.unread > 0);
  const shown =
    filter === "waiting" ? waiting
      : filter === "closed" ? threads.filter((t) => t.is_closed)
        : threads.filter((t) => !t.is_closed);

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Messages"
        subtitle={
          waiting.length
            ? `${waiting.length} conversation(s) waiting on a reply`
            : "Nothing waiting on a reply"
        }
        action={
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
            <Segmented
              value={filter}
              onChange={setFilter}
              options={[
                { value: "waiting", label: `Waiting${waiting.length ? ` (${waiting.length})` : ""}` },
                { value: "all", label: "Open" },
                { value: "closed", label: "Closed" },
              ]}
            />
            <button className="btn btn-primary" onClick={() => setComposing((c) => !c)}>
              <Plus size={15} style={{ marginRight: 4 }} />
              New
            </button>
          </div>
        }
      />

      {composing && (
        <Panel title="Start a conversation with a family">
          <div style={{ display: "grid", gap: "0.9rem" }}>
            <div
              style={{
                display: "grid",
                gap: "0.9rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(13rem, 1fr))",
              }}
            >
              <Field label="About which student">
                <select className="input" value={student} onChange={(e) => setStudent(e.target.value)}>
                  <option value="">Choose…</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.first_name} {s.last_name} — Year {s.year_level}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Kind">
                <select className="input" value={kind} onChange={(e) => setKind(e.target.value)}>
                  <option value="teacher_parent">Teacher ↔ parent</option>
                  <option value="office_parent">Office ↔ parent</option>
                </select>
              </Field>
            </div>
            <Field label="Subject">
              <input
                className="input"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g. Reading progress this term"
              />
            </Field>
            <Field label="Message">
              <textarea
                className="input"
                rows={4}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                style={{ width: "100%", resize: "vertical" }}
              />
            </Field>
            <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
              <button className="btn" onClick={() => setComposing(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                disabled={busy || !subject.trim() || !body.trim() || !student}
                onClick={startThread}
              >
                Send to the family
              </button>
            </div>
          </div>
        </Panel>
      )}

      <div
        style={{
          display: "grid",
          gap: "1rem",
          gridTemplateColumns: "minmax(18rem, 22rem) 1fr",
          alignItems: "start",
        }}
      >
        <Panel pad={false}>
          {shown.length === 0 ? (
            <div style={{ padding: "1.1rem" }}>
              <Empty
                label={
                  filter === "waiting"
                    ? "Nothing is waiting on a reply."
                    : filter === "closed"
                      ? "No closed conversations."
                      : "No open conversations."
                }
              />
            </div>
          ) : (
            shown.map((t) => (
              <button
                key={t.thread}
                onClick={() => openThread(t.thread)}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  padding: "0.8rem 1rem",
                  borderBottom: "1px solid var(--border)",
                  background:
                    open?.id === t.thread ? "color-mix(in srgb, var(--cyan) 10%, transparent)" : "transparent",
                  border: "none",
                  borderLeft: t.unread ? "3px solid var(--cyan)" : "3px solid transparent",
                  cursor: "pointer",
                  color: "inherit",
                  font: "inherit",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                  <strong style={{ fontSize: "0.92rem" }}>{t.subject}</strong>
                  {t.unread > 0 && <Badge value={`${t.unread} new`} />}
                </div>
                <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: 3 }}>
                  {t.participants.join(", ")}
                  {t.observing && " · observing"}
                </div>
                <div
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--faint)",
                    marginTop: 4,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {t.last_sender ? `${t.last_sender}: ` : ""}
                  {t.last_message_preview}
                </div>
                <div style={{ fontSize: "0.72rem", color: "var(--faint)", marginTop: 3 }}>
                  {t.last_message_at
                    ? new Date(t.last_message_at).toLocaleString(AU_LOCALE)
                    : "no messages"}
                  {" · "}
                  {KIND_LABELS[t.kind] ?? t.kind}
                </div>
              </button>
            ))
          )}
        </Panel>

        {!open ? (
          <Panel>
            <Empty label="Choose a conversation to read it." />
          </Panel>
        ) : (
          <Panel
            title={
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <strong style={{ fontSize: "1rem" }}>{open.subject}</strong>
                {open.is_closed && <Badge value="closed" />}
              </span>
            }
            action={
              !open.is_closed && (
                <button className="btn" disabled={busy} onClick={closeThread}>
                  <Archive size={14} style={{ marginRight: 4 }} />
                  Close
                </button>
              )
            }
          >
            <div style={{ display: "grid", gap: "0.7rem", marginBottom: "1rem" }}>
              {open.messages.map((m) => {
                const fromSchool = m.sender_kind === "staff";
                return (
                  <div
                    key={m.id}
                    style={{
                      justifySelf: fromSchool ? "end" : "start",
                      maxWidth: "80%",
                      padding: "0.65rem 0.9rem",
                      borderRadius: 14,
                      border: "1px solid var(--border)",
                      background: fromSchool
                        ? "color-mix(in srgb, var(--cyan) 12%, transparent)"
                        : "var(--panel-2)",
                    }}
                  >
                    <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: 3 }}>
                      {m.sender_name || m.sender_email} · {fmtDateTime(m.sent_at)}
                    </div>
                    <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.55 }}>{m.body}</div>
                  </div>
                );
              })}
            </div>

            {open.is_closed ? (
              <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                This conversation is closed. The record is kept; start a new one if the family
                needs something further.
              </p>
            ) : (
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "flex-end" }}>
                <textarea
                  className="input"
                  rows={3}
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                  placeholder="Write a reply…"
                  style={{ flex: 1, resize: "vertical" }}
                />
                <button className="btn btn-primary" disabled={busy || !reply.trim()} onClick={send}>
                  <Send size={15} style={{ marginRight: 4 }} />
                  Send
                </button>
              </div>
            )}
          </Panel>
        )}
      </div>
    </div>
  );
}
