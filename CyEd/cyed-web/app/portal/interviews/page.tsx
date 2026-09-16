"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarClock } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel } from "@/components/kit";
import { Note, PersonSwitcher } from "@/app/portal/_parts";
import { useToast } from "@/components/Toast";
import { useMyChildren, AU_LOCALE } from "@/lib/portal";

/**
 * Booking parent–teacher interviews.
 *
 * A parent's real task is "get a time with each of my child's teachers, in a
 * sensible order, without driving back and forth". So slots are grouped by
 * teacher rather than listed as one long chronological wall, and the evening
 * being assembled sits at the top where it can be checked at a glance.
 */

type Round = {
  id: string;
  name: string;
  is_open: boolean;
  bookings_open_at: string;
  bookings_close_at: string;
  instructions: string;
  max_bookings_per_student: number;
};

type Slot = {
  slot: string;
  teacher: string;
  teacher_name: string;
  starts_at: string;
  ends_at: string;
  location: string;
  booked_by_me: boolean;
};

type Appointment = {
  booking: string;
  teacher_name: string;
  starts_at: string;
  location: string;
};

const clock = (iso: string) =>
  new Date(iso).toLocaleTimeString(AU_LOCALE, { hour: "numeric", minute: "2-digit" });
const dayLabel = (iso: string) =>
  new Date(iso).toLocaleDateString(AU_LOCALE, { weekday: "short", day: "numeric", month: "short" });

export default function PortalInterviewsPage() {
  const { children, selected, setSelected, loading, error } = useMyChildren();
  const [rounds, setRounds] = useState<Round[]>([]);
  const [round, setRound] = useState<Round | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [mine, setMine] = useState<Appointment[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    (async () => {
      try {
        const rows = await cyed.list<Round>("meetings/interview-rounds/");
        setRounds(rows);
        setRound(rows.find((r) => r.is_open) ?? rows[0] ?? null);
      } catch (e) {
        setPageError(e instanceof Error ? e.message : "Could not load interview rounds");
      }
    })();
  }, []);

  const load = async () => {
    if (!round || !selected) return;
    try {
      const [slotData, scheduleData] = await Promise.all([
        cyed.get<{ results: Slot[] }>(
          `meetings/interview-rounds/${round.id}/slots/?student=${selected}`,
        ),
        cyed.get<{ appointments: Appointment[] }>(
          `meetings/interview-rounds/${round.id}/my-schedule/?student=${selected}`,
        ),
      ]);
      setSlots(slotData.results ?? []);
      setMine(scheduleData.appointments ?? []);
      setPageError(null);
    } catch (e) {
      setPageError(e instanceof Error ? e.message : "Could not load times");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [round, selected]);

  const byTeacher = useMemo(() => {
    const grouped: Record<string, Slot[]> = {};
    for (const slot of slots) {
      if (slot.booked_by_me) continue;
      (grouped[slot.teacher_name] ||= []).push(slot);
    }
    return Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b));
  }, [slots]);

  const book = async (slot: Slot) => {
    setBusy(slot.slot);
    try {
      await cyed.action(`meetings/interview-slots/${slot.slot}/book/`, { student: selected });
      toast.push(`Booked ${clock(slot.starts_at)} with ${slot.teacher_name}.`);
      await load();
    } catch (e) {
      // Losing a race is the common failure: another family took it first.
      toast.push(e instanceof Error ? e.message : "Could not book that time");
      await load();
    } finally {
      setBusy(null);
    }
  };

  const cancel = async (appointment: Appointment) => {
    setBusy(appointment.booking);
    try {
      await cyed.action(`meetings/interview-bookings/${appointment.booking}/cancel/`);
      toast.push("Cancelled.");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not cancel that");
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;
  if (!children.length) return <Empty label="No children are linked to this account yet." />;

  if (!round) {
    return (
      <div style={{ display: "grid", gap: "1.25rem" }}>
        <PageHeader title="Interviews" subtitle="Parent–teacher interviews" />
        <Empty label="There are no interview rounds open at the moment. The school will let you know when bookings open." />
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Interviews" subtitle={round.name} />
      <PersonSwitcher people={children} value={selected} onChange={setSelected} label="For" />

      {pageError && <ErrorNote error={pageError} />}

      {rounds.length > 1 && (
        <select
          className="input"
          value={round.id}
          onChange={(e) => setRound(rounds.find((r) => r.id === e.target.value) ?? round)}
          style={{ maxWidth: 320 }}
        >
          {rounds.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
              {r.is_open ? "" : " (closed)"}
            </option>
          ))}
        </select>
      )}

      {round.instructions && <Note>{round.instructions}</Note>}

      <Panel title={`Your evening (${mine.length} of ${round.max_bookings_per_student})`}>
        {mine.length === 0 ? (
          <Empty label="Nothing booked yet. Pick a time below." />
        ) : (
          <div>
            {mine.map((appointment) => (
              <div key={appointment.booking} className="portal-day">
                <div className="when">{clock(appointment.starts_at)}</div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "0.75rem",
                  }}
                >
                  <div>
                    <div className="what">{appointment.teacher_name}</div>
                    <div className="where">
                      {dayLabel(appointment.starts_at)}
                      {appointment.location && ` · ${appointment.location}`}
                    </div>
                  </div>
                  <button
                    className="btn"
                    disabled={busy !== null || !round.is_open}
                    onClick={() => cancel(appointment)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>

      {!round.is_open ? (
        <Note tone="warn">
          Bookings for this round are closed. Contact the office if you still need a time.
        </Note>
      ) : byTeacher.length === 0 ? (
        <Empty label="Every remaining time has been taken. Contact the office if you still need an appointment." />
      ) : (
        byTeacher.map(([teacherName, teacherSlots]) => (
          <Panel
            key={teacherName}
            title={
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <CalendarClock size={16} style={{ color: "var(--muted)" }} />
                <span className="label">{teacherName}</span>
              </span>
            }
          >
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
              {teacherSlots.map((slot) => (
                <button
                  key={slot.slot}
                  className="btn"
                  disabled={busy !== null}
                  onClick={() => book(slot)}
                  style={{ padding: "0.5rem 0.85rem" }}
                  title={`${dayLabel(slot.starts_at)} ${clock(slot.starts_at)}–${clock(slot.ends_at)}`}
                >
                  {clock(slot.starts_at)}
                </button>
              ))}
            </div>
          </Panel>
        ))
      )}
    </div>
  );
}
