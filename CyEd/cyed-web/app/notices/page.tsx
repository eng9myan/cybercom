"use client";

import { useEffect, useState } from "react";
import { Megaphone } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { fmtDate } from "@/lib/portal";

/**
 * Daily notices — the board that gets read at assembly.
 *
 * The compose form defaults to "today, everyone, ends in a week". A notice with
 * no end date is possible but not the default: a board that only grows is one
 * nobody reads by week three, and the fastest way to get there is to make
 * "forever" the easy option.
 */

type Notice = {
  id: string;
  title: string;
  body: string;
  audience: string;
  year_levels: string;
  priority: string;
  starts_on: string;
  ends_on: string | null;
  is_published: boolean;
  is_active: boolean;
  posted_by: string;
};

const AUDIENCES = [
  { value: "all", label: "Everyone" },
  { value: "staff", label: "Staff" },
  { value: "students", label: "Students" },
  { value: "parents", label: "Parents" },
];

const PRIORITIES = [
  { value: "normal", label: "Normal" },
  { value: "important", label: "Important" },
  { value: "urgent", label: "Urgent" },
];

const today = () => new Date().toISOString().slice(0, 10);
const inAWeek = () => {
  const d = new Date();
  d.setDate(d.getDate() + 7);
  return d.toISOString().slice(0, 10);
};

export default function NoticesPage() {
  const [view, setView] = useState<"today" | "all">("today");
  const [rows, setRows] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [audience, setAudience] = useState("all");
  const [years, setYears] = useState("");
  const [priority, setPriority] = useState("normal");
  const [starts, setStarts] = useState(today());
  const [ends, setEnds] = useState(inAWeek());

  const load = async () => {
    setLoading(true);
    try {
      if (view === "today") {
        const data = await cyed.get<{ results: Notice[] }>("school/notices/today/");
        setRows(data.results ?? []);
      } else {
        setRows(await cyed.list<Notice>("school/notices/"));
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load notices");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view]);

  const post = async () => {
    if (!title.trim() || !body.trim()) return;
    setBusy(true);
    try {
      await cyed.create("school/notices/", {
        title,
        body,
        audience,
        year_levels: years,
        priority,
        starts_on: starts,
        ends_on: ends || null,
      });
      toast.push("Posted.");
      setTitle("");
      setBody("");
      setYears("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not post that");
    } finally {
      setBusy(false);
    }
  };

  const takeDown = async (notice: Notice) => {
    setBusy(true);
    try {
      await cyed.patch(`school/notices/${notice.id}/`, { is_published: !notice.is_published });
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not change that");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Daily notices"
        subtitle="What goes on the board"
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "today", label: "On the board" },
              { value: "all", label: "All" },
            ]}
          />
        }
      />

      <Panel title="Post a notice">
        <div style={{ display: "grid", gap: "0.9rem" }}>
          <Field label="Title">
            <input
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Bus 12 cancelled this afternoon"
            />
          </Field>
          <Field label="Notice">
            <textarea
              className="input"
              rows={3}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              style={{ width: "100%", resize: "vertical" }}
            />
          </Field>
          <div
            style={{
              display: "grid",
              gap: "0.9rem",
              gridTemplateColumns: "repeat(auto-fit, minmax(10rem, 1fr))",
            }}
          >
            <Field label="Who sees it">
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
            <Field label="Priority">
              <select
                className="input"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                {PRIORITIES.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="From">
              <input
                className="input"
                type="date"
                value={starts}
                onChange={(e) => setStarts(e.target.value)}
              />
            </Field>
            <Field label="Until">
              <input
                className="input"
                type="date"
                value={ends}
                min={starts}
                onChange={(e) => setEnds(e.target.value)}
              />
            </Field>
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button className="btn btn-primary" disabled={busy} onClick={post}>
              <Megaphone size={15} style={{ marginRight: 6 }} />
              Post
            </button>
          </div>
        </div>
      </Panel>

      {error && <ErrorNote error={error} />}
      {loading && <SkeletonRows rows={4} />}

      {!loading &&
        (rows.length === 0 ? (
          <Empty
            label={view === "today" ? "Nothing on the board today." : "No notices yet."}
          />
        ) : (
          <Panel pad={false}>
            {rows.map((notice) => (
              <div
                key={notice.id}
                style={{
                  padding: "0.9rem 1.1rem",
                  borderBottom: "1px solid var(--border)",
                  opacity: notice.is_published ? 1 : 0.55,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "0.6rem",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                    <strong>{notice.title}</strong>
                    {notice.priority !== "normal" && <Badge value={notice.priority} />}
                    {!notice.is_published && <Badge value="draft" />}
                  </div>
                  <button className="btn" disabled={busy} onClick={() => takeDown(notice)}>
                    {notice.is_published ? "Take down" : "Put back up"}
                  </button>
                </div>
                <div style={{ marginTop: 4, whiteSpace: "pre-wrap" }}>{notice.body}</div>
                <div style={{ fontSize: "0.78rem", color: "var(--faint)", marginTop: 6 }}>
                  {AUDIENCES.find((a) => a.value === notice.audience)?.label}
                  {notice.year_levels && ` · Years ${notice.year_levels}`} ·{" "}
                  {fmtDate(notice.starts_on)}
                  {notice.ends_on ? ` – ${fmtDate(notice.ends_on)}` : " onwards"}
                  {notice.posted_by && ` · ${notice.posted_by}`}
                </div>
              </div>
            ))}
          </Panel>
        ))}
    </div>
  );
}
