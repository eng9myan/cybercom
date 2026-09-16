"use client";

import { useEffect, useState } from "react";
import { cyed } from "@/lib/cyed";
import type { Student } from "@/lib/types";

/**
 * The children this account can see.
 *
 * `sis/students/` is already scoped server-side — a parent gets their own
 * children and nobody else's — so the portal asks for the list rather than
 * trying to work out who the caller is. The alternative (a "who am I"
 * endpoint plus a client-side filter) puts an access decision in the browser,
 * which is the wrong place for one.
 */
export function useMyChildren() {
  const [children, setChildren] = useState<Student[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const rows = await cyed.list<Student>("sis/students/");
        setChildren(rows);
        setSelected((current) => current || rows[0]?.id || "");
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load your children");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const child = children.find((c) => c.id === selected) ?? null;
  return { children, selected, setSelected, child, loading, error };
}

export const fullName = (s: { first_name: string; last_name: string }) =>
  `${s.first_name} ${s.last_name}`.trim();

/** Best available label for a person, whichever name fields came back. */
export const displayName = (p: {
  first_name?: string;
  last_name?: string;
  full_name?: string;
}) => p.full_name || `${p.first_name ?? ""} ${p.last_name ?? ""}`.trim() || "—";

/**
 * Dates are formatted en-AU, not in the browser's locale.
 *
 * A school in Melbourne reading 05/06/2026 means 5 June. A staff laptop set to
 * en-US renders the same date as 6 May, and nothing on the screen says which
 * one it is. The product is Australian; the format is fixed to match it.
 */
export const AU_LOCALE = "en-AU";

export const fmtDate = (value?: string | null) =>
  value ? new Date(value).toLocaleDateString(AU_LOCALE) : "—";

export const fmtDateTime = (value?: string | null) =>
  value ? new Date(value).toLocaleString(AU_LOCALE) : "—";

/** Time of day only — "9:05 am". */
export const fmtTime = (value?: string | null) =>
  value
    ? new Date(value).toLocaleTimeString(AU_LOCALE, { hour: "numeric", minute: "2-digit" })
    : "—";

export type AttendanceMarkRow = {
  id: string;
  roll_call: string;
  student: string;
  status: string;
  minutes_late: number;
  note?: string;
  // Carried on the mark itself: joining to roll calls client-side needs every
  // roll call in the school, which is unbounded after a term or two.
  date?: string | null;
  class_section_name?: string;
  period_label?: string;
};

export type RollCallRow = {
  id: string;
  date: string;
  period_label?: string;
  class_section?: string;
  class_section_name?: string;
};

export type NotificationRow = {
  id: string;
  subject: string;
  body?: string;
  category: string;
  status: string;
  created_at: string;
};

/**
 * Attendance rate from a set of marks.
 *
 * `late` counts as attended. A rate that penalised lateness as absence would
 * disagree with what the school reports to the department, and a parent
 * comparing the two would be right to say the portal is wrong.
 */
export function attendanceStats(marks: AttendanceMarkRow[]) {
  const counts: Record<string, number> = {};
  for (const m of marks) counts[m.status] = (counts[m.status] ?? 0) + 1;
  const total = marks.length;
  const attended = (counts.present ?? 0) + (counts.late ?? 0);
  return {
    total,
    attended,
    absent: counts.absent ?? 0,
    late: counts.late ?? 0,
    excused: counts.excused ?? 0,
    rate: total ? Math.round((attended / total) * 1000) / 10 : 0,
  };
}

export const money = (value: string | number | null | undefined) => {
  const n = Number(value ?? 0);
  // en-AU renders AUD as "$1,234.00"; en-US renders the same currency as
  // "A$1,234.00", which reads to a school like a foreign currency.
  return n.toLocaleString(AU_LOCALE, { style: "currency", currency: "AUD" });
};

export const DAY_LABELS: Record<string, string> = {
  mon: "Monday",
  tue: "Tuesday",
  wed: "Wednesday",
  thu: "Thursday",
  fri: "Friday",
  sat: "Saturday",
  sun: "Sunday",
};

export const DAY_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

/** "09:00:00" → "9:00am". Time-of-day, not a timestamp — no timezone maths. */
export function clock(value?: string | null) {
  if (!value) return "";
  const [h, m] = value.split(":");
  const hour = Number(h);
  const suffix = hour < 12 ? "am" : "pm";
  const display = hour % 12 === 0 ? 12 : hour % 12;
  return `${display}:${m}${suffix}`;
}

export type FamilyStatement = {
  family: string;
  name: string;
  billing_email: string;
  children_total: number;
  totals: {
    billed: string;
    paid: string;
    balance: string;
    overdue: string;
    sibling_discount_applied: string;
  };
  children: {
    student: string;
    name: string;
    year_level: number;
    balance: string;
    overdue: string;
    sibling_discount: { rule: string | null; percent: string; amount_off: string } | null;
    installments: {
      installment: string;
      bill: string;
      installment_no: number;
      due_date: string | null;
      amount_due: string;
      paid: string;
      balance: string;
      status: string;
    }[];
    invoices: {
      invoice: string;
      description: string;
      amount: string;
      balance: string;
      due_date: string | null;
      status: string;
    }[];
  }[];
};

export type TimetableSlot = {
  id: string;
  class_section: string;
  class_section_name?: string;
  day_of_week: string;
  period_label: string;
  start_time: string;
  end_time: string;
  room?: string;
  teacher_display?: string;
};

export type PortalThread = {
  thread: string;
  subject: string;
  kind: string;
  last_message_at: string | null;
  last_message_preview: string;
  last_sender: string;
  unread: number;
  observing: boolean;
  is_closed: boolean;
  participants: string[];
};
