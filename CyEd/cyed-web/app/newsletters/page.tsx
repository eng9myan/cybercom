"use client";

import { useEffect, useState } from "react";
import { Send, Users } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { fmtDateTime } from "@/lib/portal";

/**
 * Newsletters.
 *
 * The one thing this screen must not let a school do is send twice, or send to
 * the wrong people. So the recipient count is fetched *before* the send button
 * is usable — "all parents" and "Year 9 parents" look identical on a form and
 * differ by nine hundred recipients — and a sent newsletter loses its send
 * button entirely rather than relying on the API to refuse.
 */

type Newsletter = {
  id: string;
  title: string;
  body: string;
  audience: string;
  year_levels: string;
  channel: string;
  status: string;
  sent_at: string | null;
  sent_by: string;
  recipients: number;
};

type Preview = { total: number; by_kind: Record<string, number> };

const AUDIENCES = [
  { value: "parents", label: "Parents and guardians" },
  { value: "staff", label: "Staff" },
  { value: "students", label: "Students" },
  { value: "all", label: "Everyone" },
];

// SMS is deliberately absent: bulk texting a school is a bill nobody approved.
const CHANNELS = [
  { value: "in_app", label: "In the portal" },
  { value: "email", label: "Email" },
  { value: "push", label: "Push notification" },
];

export default function NewslettersPage() {
  const [rows, setRows] = useState<Newsletter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [previews, setPreviews] = useState<Record<string, Preview>>({});
  const toast = useToast();

  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [audience, setAudience] = useState("parents");
  const [years, setYears] = useState("");
  const [channel, setChannel] = useState("in_app");

  const load = async () => {
    setLoading(true);
    try {
      setRows(await cyed.list<Newsletter>("notifications/newsletters/"));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load newsletters");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  // Drafts get their audience counted on load, so the send button can say how
  // many people it is about to reach rather than asking the sender to guess.
  useEffect(() => {
    (async () => {
      for (const row of rows.filter((r) => r.status === "draft" && !previews[r.id])) {
        try {
          const data = await cyed.get<Preview>(`notifications/newsletters/${row.id}/preview/`);
          setPreviews((current) => ({ ...current, [row.id]: data }));
        } catch {
          // A failed count leaves the button disabled rather than sending blind.
        }
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows]);

  const create = async () => {
    if (!title.trim() || !body.trim()) return;
    setBusy("create");
    try {
      await cyed.create("notifications/newsletters/", {
        title, body, audience, year_levels: years, channel,
      });
      toast.push("Saved as a draft. Check the audience before sending.");
      setTitle("");
      setBody("");
      setYears("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not save that");
    } finally {
      setBusy(null);
    }
  };

  const send = async (row: Newsletter) => {
    const count = previews[row.id]?.total ?? 0;
    if (!window.confirm(`Send "${row.title}" to ${count} recipient(s)? This cannot be undone.`)) {
      return;
    }
    setBusy(row.id);
    try {
      const resp = await cyed.action<Newsletter>(`notifications/newsletters/${row.id}/send/`);
      toast.push(`Sent to ${resp.recipients} recipient(s).`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not send that");
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Newsletters" subtitle="Bulk messages to families and staff" />

      <Panel title="Write a newsletter">
        <div style={{ display: "grid", gap: "0.9rem" }}>
          <Field label="Title">
            <input
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Week 4 newsletter"
            />
          </Field>
          <Field label="Message">
            <textarea
              className="input"
              rows={6}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              style={{ width: "100%", resize: "vertical" }}
            />
          </Field>
          <div
            style={{
              display: "grid",
              gap: "0.9rem",
              gridTemplateColumns: "repeat(auto-fit, minmax(11rem, 1fr))",
            }}
          >
            <Field label="Who receives it">
              <select
                className="input"
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
              >
                {AUDIENCES.map((a) => (
                  <option key={a.value} value={a.value}>
                    {a.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Year levels">
              <input
                className="input"
                value={years}
                onChange={(e) => setYears(e.target.value)}
                placeholder="e.g. 9,10 — blank for all"
              />
            </Field>
            <Field label="How it is sent">
              <select className="input" value={channel} onChange={(e) => setChannel(e.target.value)}>
                {CHANNELS.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button className="btn btn-primary" disabled={busy !== null} onClick={create}>
              Save as draft
            </button>
          </div>
        </div>
      </Panel>

      {rows.length === 0 ? (
        <Empty label="No newsletters yet." />
      ) : (
        rows.map((row) => {
          const preview = previews[row.id];
          const sent = row.status === "sent";
          return (
            <Panel
              key={row.id}
              title={
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <strong style={{ fontSize: "1rem" }}>{row.title}</strong>
                  <Badge value={row.status} />
                </span>
              }
              action={
                sent ? (
                  <span style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                    {row.recipients} sent {fmtDateTime(row.sent_at)}
                  </span>
                ) : (
                  <button
                    className="btn btn-primary"
                    // Disabled until the count is known: sending blind is how a
                    // school reaches the wrong nine hundred people.
                    disabled={busy !== null || !preview || preview.total === 0}
                    onClick={() => send(row)}
                  >
                    <Send size={15} style={{ marginRight: 6 }} />
                    {preview ? `Send to ${preview.total}` : "Counting…"}
                  </button>
                )
              }
            >
              <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.55 }}>{row.body}</div>
              <div
                style={{
                  fontSize: "0.8rem",
                  color: "var(--faint)",
                  marginTop: "0.7rem",
                  display: "flex",
                  gap: "0.5rem",
                  alignItems: "center",
                  flexWrap: "wrap",
                }}
              >
                <Users size={13} />
                {AUDIENCES.find((a) => a.value === row.audience)?.label}
                {row.year_levels && ` · Years ${row.year_levels}`}
                {` · ${CHANNELS.find((c) => c.value === row.channel)?.label ?? row.channel}`}
                {preview && !sent && preview.total === 0 && (
                  <span style={{ color: "var(--amber, #fbbf24)" }}>
                    — this audience matches nobody
                  </span>
                )}
                {sent && row.sent_by && ` · by ${row.sent_by}`}
              </div>
            </Panel>
          );
        })
      )}
    </div>
  );
}
