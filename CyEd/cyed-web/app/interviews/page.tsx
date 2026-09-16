"use client";

import { useEffect, useState } from "react";
import { CalendarPlus } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { AU_LOCALE } from "@/lib/portal";

/**
 * Staff side of parent–teacher interviews.
 *
 * Two jobs, and they belong to different people: the office creates a round and
 * lays out each teacher's evening; a teacher opens their own schedule to see
 * who is coming and where the gaps are.
 *
 * Slots are generated from a start time, a finish time and a duration, because
 * that is how a teacher thinks about an evening — not as eighteen individual
 * appointment times to enter by hand.
 */

type Round = {
  id: string;
  name: string;
  is_open: boolean;
  is_published: boolean;
  bookings_open_at: string;
  bookings_close_at: string;
  slot_count: number;
  max_bookings_per_student: number;
};

type Staff = { id: string; first_name: string; last_name: string };

type ScheduleRow = {
  slot: string;
  starts_at: string;
  ends_at: string;
  is_available: boolean;
  student_name: string | null;
  booked_by: string;
  note: string;
};

type Schedule = { slots: number; booked: number; free: number; schedule: ScheduleRow[] };

const clock = (iso: string) =>
  new Date(iso).toLocaleTimeString(AU_LOCALE, { hour: "numeric", minute: "2-digit" });

export default function InterviewsAdminPage() {
  const [rounds, setRounds] = useState<Round[]>([]);
  const [staff, setStaff] = useState<Staff[]>([]);
  const [round, setRound] = useState<Round | null>(null);
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  // New round
  const [name, setName] = useState("Semester 1 interviews");
  const [opensAt, setOpensAt] = useState("");
  const [closesAt, setClosesAt] = useState("");

  // Slot generation
  const [teacher, setTeacher] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [duration, setDuration] = useState(10);
  const [location, setLocation] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const [roundRows, staffRows] = await Promise.all([
        cyed.list<Round>("meetings/interview-rounds/"),
        cyed.list<Staff>("hr/staff/"),
      ]);
      setRounds(roundRows);
      setStaff(staffRows);
      setRound((current) => roundRows.find((r) => r.id === current?.id) ?? roundRows[0] ?? null);
      if (!teacher && staffRows[0]) setTeacher(staffRows[0].id);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load interview rounds");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const createRound = async () => {
    if (!name.trim() || !opensAt || !closesAt) return;
    setBusy(true);
    try {
      await cyed.create("meetings/interview-rounds/", {
        name,
        bookings_open_at: new Date(opensAt).toISOString(),
        bookings_close_at: new Date(closesAt).toISOString(),
        is_published: false,
      });
      toast.push("Round created as a draft. Publish it when the slots are ready.");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not create the round");
    } finally {
      setBusy(false);
    }
  };

  const publish = async (target: Round) => {
    setBusy(true);
    try {
      await cyed.patch(`meetings/interview-rounds/${target.id}/`, {
        is_published: !target.is_published,
      });
      toast.push(target.is_published ? "Unpublished." : "Published — families can book now.");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not change that");
    } finally {
      setBusy(false);
    }
  };

  const generate = async () => {
    if (!round || !teacher || !start || !end) return;
    setBusy(true);
    try {
      const resp = await cyed.action<{ created: number }>(
        `meetings/interview-rounds/${round.id}/generate-slots/`,
        {
          teacher,
          start: new Date(start).toISOString(),
          end: new Date(end).toISOString(),
          duration_minutes: duration,
          location,
        },
      );
      toast.push(`${resp.created} slot(s) created.`);
      await load();
      await loadSchedule();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not create slots");
    } finally {
      setBusy(false);
    }
  };

  const loadSchedule = async () => {
    if (!round) return;
    try {
      setSchedule(
        await cyed.get<Schedule>(`meetings/interview-rounds/${round.id}/my-schedule/`),
      );
    } catch {
      // A staff account with no linked Staff record has no schedule of its own.
      setSchedule(null);
    }
  };

  useEffect(() => {
    loadSchedule();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [round]);

  if (loading) return <SkeletonRows rows={6} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Interviews" subtitle="Parent–teacher interview rounds" />

      <Panel title="Create a round">
        <div style={{ display: "grid", gap: "0.9rem", gridTemplateColumns: "repeat(auto-fit, minmax(14rem, 1fr))" }}>
          <Field label="Name">
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <Field label="Bookings open">
            <input
              className="input"
              type="datetime-local"
              value={opensAt}
              onChange={(e) => setOpensAt(e.target.value)}
            />
          </Field>
          <Field label="Bookings close">
            <input
              className="input"
              type="datetime-local"
              value={closesAt}
              onChange={(e) => setClosesAt(e.target.value)}
            />
          </Field>
        </div>
        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.75rem" }}>
          <button className="btn btn-primary" disabled={busy} onClick={createRound}>
            Create as draft
          </button>
        </div>
      </Panel>

      {rounds.length > 0 && (
        <Panel title="Rounds" pad={false}>
          {rounds.map((r) => (
            <div
              key={r.id}
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "0.75rem",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0.9rem 1.1rem",
                borderBottom: "1px solid var(--border)",
                background: r.id === round?.id ? "var(--panel-2)" : undefined,
              }}
            >
              <button
                onClick={() => setRound(r)}
                style={{
                  background: "transparent",
                  border: 0,
                  color: "inherit",
                  font: "inherit",
                  textAlign: "left",
                  cursor: "pointer",
                }}
              >
                <div style={{ fontWeight: 650 }}>{r.name}</div>
                <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                  {r.slot_count} slot(s) · max {r.max_bookings_per_student} per family
                </div>
              </button>
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                <Badge value={r.is_published ? (r.is_open ? "active" : "completed") : "draft"} />
                <button className="btn" disabled={busy} onClick={() => publish(r)}>
                  {r.is_published ? "Unpublish" : "Publish"}
                </button>
              </div>
            </div>
          ))}
        </Panel>
      )}

      {round && (
        <Panel title={`Lay out an evening — ${round.name}`}>
          <div
            style={{
              display: "grid",
              gap: "0.9rem",
              gridTemplateColumns: "repeat(auto-fit, minmax(12rem, 1fr))",
            }}
          >
            <Field label="Teacher">
              <select className="input" value={teacher} onChange={(e) => setTeacher(e.target.value)}>
                {staff.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.first_name} {s.last_name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="From">
              <input
                className="input"
                type="datetime-local"
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </Field>
            <Field label="Until">
              <input
                className="input"
                type="datetime-local"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </Field>
            <Field label="Minutes each">
              <input
                className="input"
                type="number"
                min={5}
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
              />
            </Field>
            <Field label="Room (optional)">
              <input
                className="input"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </Field>
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.75rem" }}>
            <button className="btn btn-primary" disabled={busy} onClick={generate}>
              <CalendarPlus size={15} style={{ marginRight: 6 }} />
              Create slots
            </button>
          </div>
        </Panel>
      )}

      {schedule && schedule.slots > 0 && (
        <Panel
          title={`My evening — ${schedule.booked} booked, ${schedule.free} free`}
          pad={false}
        >
          {schedule.schedule.map((row) => (
            <div
              key={row.slot}
              style={{
                display: "flex",
                gap: "1rem",
                alignItems: "center",
                padding: "0.7rem 1.1rem",
                borderBottom: "1px solid var(--border)",
                opacity: row.student_name ? 1 : 0.6,
              }}
            >
              <span
                style={{
                  fontVariantNumeric: "tabular-nums",
                  color: "var(--muted)",
                  minWidth: "5rem",
                }}
              >
                {clock(row.starts_at)}
              </span>
              <span style={{ flex: 1 }}>
                {row.student_name ? (
                  <>
                    <strong>{row.student_name}</strong>
                    {row.note && (
                      <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>{row.note}</div>
                    )}
                  </>
                ) : (
                  <span style={{ color: "var(--muted)" }}>
                    {row.is_available ? "Free" : "Blocked"}
                  </span>
                )}
              </span>
            </div>
          ))}
        </Panel>
      )}

      {round && schedule === null && (
        <Empty label="No staff record is linked to this account, so there is no personal schedule to show." />
      )}
    </div>
  );
}
