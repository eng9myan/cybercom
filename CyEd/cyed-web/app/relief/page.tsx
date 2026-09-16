"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, PhoneCall } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";

/**
 * Casual relief teacher (CRT) booking.
 *
 * The daily organiser's 7:30am job: someone has called in sick, find a
 * replacement. So the search is the landing state — pick a date and a subject,
 * get a ranked list with phone numbers, offer the work.
 *
 * People who cannot be booked never appear in the search. They appear on the
 * clearance tab instead, which is also the answer to "why did that come back
 * empty?" — an organiser under time pressure will ring the first name they see.
 */

type Available = {
  relief_teacher: string;
  name: string;
  phone: string;
  email: string;
  agency: string;
  subjects: string;
  daily_rate: string;
  subject_match: boolean;
};

type Blocked = {
  relief_teacher: string;
  name: string;
  agency: string;
  problems: string[];
  wwcc_expires_on: string | null;
};

type Booking = {
  id: string;
  relief_teacher_name: string;
  date: string;
  status: string;
  periods: string;
  agreed_rate: string;
};

const today = () => new Date().toISOString().slice(0, 10);

export default function ReliefPage() {
  const [view, setView] = useState<"find" | "bookings" | "clearances">("find");
  const [date, setDate] = useState(today());
  const [subject, setSubject] = useState("");
  const [available, setAvailable] = useState<Available[]>([]);
  const [blocked, setBlocked] = useState<Blocked[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const toast = useToast();

  const search = async () => {
    setLoading(true);
    try {
      const data = await cyed.get<{ results: Available[] }>(
        `substitution/relief-teachers/available/?date=${date}` +
          (subject ? `&subject=${encodeURIComponent(subject)}` : ""),
      );
      setAvailable(data.results ?? []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not search the register");
    } finally {
      setLoading(false);
    }
  };

  const loadBlocked = async () => {
    try {
      const data = await cyed.get<{ results: Blocked[] }>(
        "substitution/relief-teachers/clearance-issues/",
      );
      setBlocked(data.results ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load clearance issues");
    }
  };

  const loadBookings = async () => {
    try {
      setBookings(await cyed.list<Booking>(`substitution/relief-bookings/?date=${date}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load bookings");
    }
  };

  useEffect(() => {
    if (view === "find") search();
    if (view === "clearances") loadBlocked();
    if (view === "bookings") loadBookings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view, date]);

  const offer = async (person: Available) => {
    setBusy(person.relief_teacher);
    try {
      await cyed.action(`substitution/relief-teachers/${person.relief_teacher}/offer/`, {
        date,
        is_full_day: true,
      });
      toast.push(`Offered to ${person.name}. Waiting on their answer.`);
      await search();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not offer that");
    } finally {
      setBusy(null);
    }
  };

  const respond = async (booking: Booking, accepted: boolean) => {
    setBusy(booking.id);
    try {
      await cyed.action(
        `substitution/relief-bookings/${booking.id}/${accepted ? "accept" : "decline"}/`,
      );
      toast.push(accepted ? "Confirmed." : "Marked declined — the day is free again.");
      await loadBookings();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not record that");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Relief teachers"
        subtitle="Cover for absent staff"
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "find", label: "Find" },
              { value: "bookings", label: "Bookings" },
              { value: "clearances", label: "Clearances" },
            ]}
          />
        }
      />

      {error && <ErrorNote error={error} />}

      {view !== "clearances" && (
        <Panel>
          <div
            style={{
              display: "grid",
              gap: "0.9rem",
              gridTemplateColumns: "repeat(auto-fit, minmax(11rem, 1fr))",
              alignItems: "end",
            }}
          >
            <Field label="Date">
              <input
                className="input"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </Field>
            {view === "find" && (
              <>
                <Field label="Subject (optional)">
                  <input
                    className="input"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="e.g. Maths"
                  />
                </Field>
                <button className="btn btn-primary" onClick={search} disabled={loading}>
                  Search
                </button>
              </>
            )}
          </div>
        </Panel>
      )}

      {loading && <SkeletonRows rows={4} />}

      {!loading && view === "find" && (
        available.length === 0 ? (
          <Empty label="Nobody on the register is available and cleared for that day. Check the Clearances tab — someone may be blocked rather than busy." />
        ) : (
          <Panel pad={false}>
            {available.map((person) => (
              <div
                key={person.relief_teacher}
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.9rem 1.1rem",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <div>
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                    <strong>{person.name}</strong>
                    {person.subject_match && <Badge value="subject match" />}
                  </div>
                  <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                    {person.subjects || "—"}
                    {person.agency && ` · ${person.agency}`} · ${person.daily_rate}/day
                  </div>
                  {person.phone && (
                    <a
                      href={`tel:${person.phone}`}
                      style={{
                        fontSize: "0.85rem",
                        display: "inline-flex",
                        gap: 4,
                        alignItems: "center",
                        marginTop: 3,
                      }}
                    >
                      <PhoneCall size={13} />
                      {person.phone}
                    </a>
                  )}
                </div>
                <button
                  className="btn btn-primary"
                  disabled={busy !== null}
                  onClick={() => offer(person)}
                >
                  Offer work
                </button>
              </div>
            ))}
          </Panel>
        )
      )}

      {!loading && view === "bookings" && (
        bookings.length === 0 ? (
          <Empty label="No relief booked for that day." />
        ) : (
          <Panel pad={false}>
            {bookings.map((booking) => (
              <div
                key={booking.id}
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.9rem 1.1rem",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <div>
                  <strong>{booking.relief_teacher_name}</strong>
                  <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                    {booking.periods || "Full day"} · ${booking.agreed_rate}
                  </div>
                </div>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  <Badge value={booking.status} />
                  {booking.status === "offered" && (
                    <>
                      <button
                        className="btn btn-primary"
                        disabled={busy !== null}
                        onClick={() => respond(booking, true)}
                      >
                        They accepted
                      </button>
                      <button
                        className="btn"
                        disabled={busy !== null}
                        onClick={() => respond(booking, false)}
                      >
                        Declined
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </Panel>
        )
      )}

      {view === "clearances" && (
        blocked.length === 0 ? (
          <Empty label="Everyone on the register has current clearances." />
        ) : (
          <Panel
            title="Cannot be booked"
            pad={false}
          >
            {blocked.map((person) => (
              <div
                key={person.relief_teacher}
                style={{
                  display: "flex",
                  gap: "0.75rem",
                  alignItems: "flex-start",
                  padding: "0.9rem 1.1rem",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <AlertTriangle size={18} style={{ color: "var(--amber, #fbbf24)", flexShrink: 0 }} />
                <div>
                  <strong>{person.name}</strong>
                  {person.agency && (
                    <span style={{ color: "var(--muted)" }}> · {person.agency}</span>
                  )}
                  <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: 2 }}>
                    {person.problems.join(", ")}
                    {person.wwcc_expires_on && ` (WWCC expired ${person.wwcc_expires_on})`}
                  </div>
                </div>
              </div>
            ))}
          </Panel>
        )
      )}
    </div>
  );
}
