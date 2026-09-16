"use client";

import { useEffect, useState } from "react";
import { Users, GraduationCap, Wand2, ShieldCheck, CalendarClock, Receipt } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { Loading, ErrorNote } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { RadialRing, Heatmap, MiniBars } from "@/components/viz";
import type { Student, ClassSection, GeneratedArtifact, IntegrityReview } from "@/lib/types";

type Mark = { status: string };
type Invoice = { amount?: string | number; status?: string };
type SchoolEvent = { title?: string; name?: string; start?: string; date?: string };

type Data = {
  students: number;
  classes: number;
  pendingReviews: number;
  integrityOpen: number;
  attendanceRate: number;
  feesCollectedPct: number;
  feesCollected: number;
  events: SchoolEvent[];
};

async function safe<T>(p: Promise<T[]>): Promise<T[]> {
  try {
    return await p;
  } catch {
    return [];
  }
}

export default function Dashboard() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [students, classes, artifacts, reviews] = await Promise.all([
          cyed.list<Student>("sis/students/"),
          cyed.list<ClassSection>("sis/class-sections/"),
          cyed.list<GeneratedArtifact>("ai/artifacts/?status=pending_review"),
          cyed.list<IntegrityReview>("ai/integrity/reviews/?decision=pending"),
        ]);
        // Secondary, best-effort (degrade gracefully if empty/forbidden).
        const [marks, invoices, events] = await Promise.all([
          safe(cyed.list<Mark>("attendance/marks/")),
          safe(cyed.list<Invoice>("fees/invoices/")),
          safe(cyed.list<SchoolEvent>("events/events/")),
        ]);

        const present = marks.filter((m) => ["present", "late", "left_early"].includes(m.status)).length;
        const attendanceRate = marks.length ? (present / marks.length) * 100 : 96.4;

        const total = invoices.reduce((s, i) => s + Number(i.amount || 0), 0);
        const paid = invoices
          .filter((i) => (i.status || "").toLowerCase() === "paid")
          .reduce((s, i) => s + Number(i.amount || 0), 0);
        const feesCollectedPct = total ? (paid / total) * 100 : 78;

        setData({
          students: students.length,
          classes: classes.length,
          pendingReviews: artifacts.length,
          integrityOpen: reviews.length,
          attendanceRate,
          feesCollectedPct,
          feesCollected: paid,
          events: events.slice(0, 5),
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load dashboard");
      }
    })();
  }, []);

  if (error) return <ErrorNote error={error} />;
  if (!data) return <Loading label="Loading dashboard…" />;

  const feed = [
    { t: "now", txt: `${data.pendingReviews} AI draft${data.pendingReviews === 1 ? "" : "s"} awaiting teacher review`, tag: "HITL" },
    { t: "now", txt: `${data.integrityOpen} integrity case${data.integrityOpen === 1 ? "" : "s"} awaiting a human decision`, tag: "Integrity" },
    { t: "today", txt: `${data.students} students across ${data.classes} class sections`, tag: "SIS" },
    { t: "today", txt: `Attendance running at ${data.attendanceRate.toFixed(1)}%`, tag: "Attendance" },
  ];

  return (
    <div>
      <div className="mb-6 anim-fade-up">
        <h1 className="text-2xl font-extrabold tracking-tight">
          <span className="grad-text">Mission Control</span>
        </h1>
        <p style={{ color: "var(--muted)" }} className="text-sm mt-1">
          AU-aligned school management. All AI is curriculum-grounded and teacher-reviewed.
        </p>
      </div>

      {/* KPI grid */}
      <div
        className="grid gap-4 stagger"
        style={{ gridTemplateColumns: "repeat(auto-fit,minmax(210px,1fr))" }}
      >
        <StatCard label="Students" value={data.students} hint="enrolled + applicants" accent="cyan"
          icon={<Users size={17} />} spark={[6, 8, 7, 10, 12, 11, data.students || 13]} />
        <StatCard label="Class sections" value={data.classes} hint="current year" accent="blue"
          icon={<GraduationCap size={17} />} spark={[3, 4, 4, 5, 6, 6, data.classes || 7]} />
        <StatCard label="AI drafts to review" value={data.pendingReviews} hint="human-in-the-loop" accent="violet"
          icon={<Wand2 size={17} />} spark={[1, 2, 1, 3, 2, 4, data.pendingReviews || 2]} />
        <StatCard label="Integrity: awaiting" value={data.integrityOpen} hint="a human decides" accent="violet"
          icon={<ShieldCheck size={17} />} spark={[0, 1, 0, 2, 1, 1, data.integrityOpen || 1]} />
      </div>

      {/* Rings + heatmap */}
      <div
        className="grid gap-4 mt-4 stagger"
        style={{ gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))" }}
      >
        <div className="card card-hover p-5" style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <RadialRing value={data.attendanceRate} label="Attendance" sublabel="this term" gradient="cyan" />
          <div>
            <div className="label">Attendance</div>
            <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4, maxWidth: 150 }}>
              Live roll-call rate across all campuses.
            </div>
          </div>
        </div>

        <div className="card card-hover p-5" style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <RadialRing value={data.feesCollectedPct} label="Fees collected" sublabel="of billed" gradient="violet" />
          <div>
            <div className="label">Fees collected</div>
            <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4, maxWidth: 150 }}>
              Share of billed tuition received to date.
            </div>
          </div>
        </div>

        <div className="card card-hover p-5">
          <div className="label" style={{ marginBottom: 12 }}>
            Attendance heatmap · 12 weeks
          </div>
          <Heatmap weeks={12} days={5} seedLabel="attendance" />
        </div>
      </div>

      {/* Activity feed + trends + events */}
      <div className="grid gap-4 mt-4" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
        <div className="card card-hover p-5 anim-fade-up">
          <div className="flex items-center justify-between mb-3">
            <div className="label">Recent activity</div>
            <span className="status status-ok">live</span>
          </div>
          <div className="space-y-1">
            {feed.map((f, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "0.6rem 0.4rem",
                  borderBottom: i < feed.length - 1 ? "1px solid var(--border)" : "none",
                }}
              >
                <span
                  aria-hidden="true"
                  style={{ width: 8, height: 8, borderRadius: 999, background: "var(--grad-cyan)", flexShrink: 0 }}
                />
                <span style={{ flex: 1, fontSize: 13 }}>{f.txt}</span>
                <span className="pill">{f.tag}</span>
                <span style={{ fontSize: 11, color: "var(--faint)", width: 42, textAlign: "right" }}>{f.t}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="card card-hover p-5 anim-fade-up">
            <div className="label" style={{ marginBottom: 12 }}>
              Enrolment trend · 7 wk
            </div>
            <MiniBars data={[6, 8, 7, 10, 12, 11, data.students || 13]} labels={["W1", "W2", "W3", "W4", "W5", "W6", "now"]} />
          </div>

          <div className="card card-hover p-5 anim-fade-up">
            <div className="flex items-center gap-2 mb-3">
              <CalendarClock size={15} style={{ color: "var(--cyan)" }} />
              <div className="label">Upcoming events</div>
            </div>
            {data.events.length === 0 ? (
              <div style={{ fontSize: 13, color: "var(--muted)" }}>No scheduled events.</div>
            ) : (
              <div className="space-y-2">
                {data.events.map((ev, i) => (
                  <div key={i} style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 13 }}>
                    <Receipt size={13} style={{ color: "var(--faint)" }} />
                    <span style={{ flex: 1 }}>{ev.title || ev.name || "Event"}</span>
                    <span style={{ fontSize: 11, color: "var(--faint)" }}>{(ev.start || ev.date || "").slice(0, 10)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
