"use client";

import { useEffect, useMemo, useState } from "react";
import { Users, UserCheck, CalendarOff, Star } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Loading, Field, SkeletonRows } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge, Segmented, Modal } from "@/components/kit";
import { useToast } from "@/components/Toast";

type Staff = {
  id: string;
  first_name: string;
  last_name: string;
  email?: string;
  role: string;
  department?: string;
  staff_number?: string;
  is_active: boolean;
};
type Leave = {
  id: string;
  staff: string;
  leave_type: string;
  start_date?: string;
  end_date?: string;
  days?: string;
  status: string;
  reason?: string;
};
type Review = {
  id: string;
  staff: string;
  staff_name?: string;
  review_period: string;
  overall_rating?: number | null;
  status: string;
};
type Task = {
  id: string;
  staff: string;
  staff_name?: string;
  kind: string;
  title: string;
  is_completed: boolean;
  due_date?: string | null;
};

type Tab = "staff" | "leave" | "reviews" | "onboarding";

export default function HrPage() {
  const [tab, setTab] = useState<Tab>("staff");
  const [staff, setStaff] = useState<Staff[]>([]);
  const [leave, setLeave] = useState<Leave[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  // add-staff form
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("teacher");
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [s, l, r, t] = await Promise.all([
        cyed.list<Staff>("hr/staff/"),
        cyed.list<Leave>("hr/leave/"),
        cyed.list<Review>("hr/performance-reviews/"),
        cyed.list<Task>("hr/onboarding-tasks/"),
      ]);
      setStaff(s);
      setLeave(l);
      setReviews(r);
      setTasks(t);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load HR data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const name = (id: string) => {
    const s = staff.find((x) => x.id === id);
    return s ? `${s.first_name} ${s.last_name}` : "—";
  };

  const stats = useMemo(
    () => ({
      active: staff.filter((s) => s.is_active).length,
      pendingLeave: leave.filter((l) => l.status === "requested").length,
      openTasks: tasks.filter((t) => !t.is_completed).length,
      reviews: reviews.length,
    }),
    [staff, leave, tasks, reviews]
  );

  const addStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await cyed.create("hr/staff/", { first_name: first, last_name: last, email, role });
      toast.push(`${first} ${last} added`);
      setFirst("");
      setLast("");
      setEmail("");
      await load();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Could not add staff", "bad");
    } finally {
      setSaving(false);
    }
  };

  const act = async (path: string, ok: string) => {
    try {
      await cyed.action(path, {});
      toast.push(ok);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Action failed", "bad");
    }
  };

  if (loading) return <Loading label="Loading HR…" />;

  const staffCols: Column<Staff>[] = [
    {
      key: "name",
      header: "Name",
      render: (s) => (
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{
              width: 30, height: 30, borderRadius: 9, display: "grid", placeItems: "center",
              background: "var(--grad-primary)", color: "#fff", fontWeight: 700, fontSize: 12, flexShrink: 0,
            }}
          >
            {(s.first_name?.[0] ?? "") + (s.last_name?.[0] ?? "")}
          </span>
          <span style={{ fontWeight: 600 }}>{s.first_name} {s.last_name}</span>
        </div>
      ),
    },
    { key: "role", header: "Role", width: 120, render: (s) => <span className="pill" style={{ textTransform: "capitalize" }}>{s.role}</span> },
    { key: "dept", header: "Department", render: (s) => <span style={{ color: "var(--muted)" }}>{s.department || "—"}</span> },
    { key: "email", header: "Email", render: (s) => <span style={{ color: "var(--muted)" }}>{s.email || "—"}</span> },
    { key: "status", header: "Status", width: 120, render: (s) => <Badge value={s.is_active ? "active" : "withdrawn"} /> },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (s) => (
        <span style={{ display: "inline-flex", gap: 6 }}>
          <button className="btn btn-ghost" onClick={() => act(`hr/staff/${s.id}/onboard/`, "Onboarding checklist created")}>
            Onboard
          </button>
          {s.is_active && (
            <button className="btn btn-ghost" onClick={() => act(`hr/staff/${s.id}/offboard/`, "Offboarded — contract ended")}>
              Offboard
            </button>
          )}
        </span>
      ),
    },
  ];

  const leaveCols: Column<Leave>[] = [
    { key: "staff", header: "Staff", render: (l) => <span style={{ fontWeight: 600 }}>{name(l.staff)}</span> },
    { key: "type", header: "Type", width: 120, render: (l) => <span className="pill" style={{ textTransform: "capitalize" }}>{l.leave_type}</span> },
    { key: "dates", header: "Dates", render: (l) => <span style={{ color: "var(--muted)" }}>{l.start_date} → {l.end_date}</span> },
    { key: "days", header: "Days", width: 80, align: "right", render: (l) => l.days ?? "—" },
    { key: "status", header: "Status", width: 130, render: (l) => <Badge value={l.status} /> },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (l) =>
        l.status === "requested" ? (
          <span style={{ display: "inline-flex", gap: 6 }}>
            <button className="btn btn-primary" onClick={() => act(`hr/leave/${l.id}/approve/`, "Leave approved — written to staff attendance")}>
              Approve
            </button>
            <button className="btn btn-ghost" onClick={() => act(`hr/leave/${l.id}/reject/`, "Leave rejected")}>Reject</button>
          </span>
        ) : null,
    },
  ];

  const reviewCols: Column<Review>[] = [
    { key: "staff", header: "Staff", render: (r) => <span style={{ fontWeight: 600 }}>{r.staff_name || name(r.staff)}</span> },
    { key: "period", header: "Period", width: 150, render: (r) => r.review_period },
    {
      key: "rating",
      header: "Rating",
      width: 120,
      render: (r) =>
        r.overall_rating ? (
          <span style={{ color: "var(--warn)" }}>{"★".repeat(r.overall_rating)}<span style={{ color: "var(--border-strong)" }}>{"★".repeat(5 - r.overall_rating)}</span></span>
        ) : (
          <span style={{ color: "var(--faint)" }}>—</span>
        ),
    },
    { key: "status", header: "Status", width: 150, render: (r) => <Badge value={r.status} /> },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (r) =>
        r.status === "draft" ? (
          <button className="btn btn-ghost" onClick={() => act(`hr/performance-reviews/${r.id}/submit/`, "Review submitted")}>Submit</button>
        ) : null,
    },
  ];

  const taskCols: Column<Task>[] = [
    { key: "title", header: "Task", render: (t) => <span style={{ fontWeight: 600 }}>{t.title}</span> },
    { key: "staff", header: "Staff", render: (t) => <span style={{ color: "var(--muted)" }}>{t.staff_name || name(t.staff)}</span> },
    { key: "kind", header: "Kind", width: 130, render: (t) => <span className="pill" style={{ textTransform: "capitalize" }}>{t.kind}</span> },
    { key: "done", header: "Status", width: 130, render: (t) => <Badge value={t.is_completed ? "completed" : "pending"} /> },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (t) =>
        !t.is_completed ? (
          <button className="btn btn-ghost" onClick={() => act(`hr/onboarding-tasks/${t.id}/complete/`, "Task completed")}>Complete</button>
        ) : null,
    },
  ];

  return (
    <div>
      <PageHeader
        title="Human Resources"
        subtitle="Staff records, contracts, leave, performance reviews and onboarding."
        action={
          <Segmented
            value={tab}
            onChange={setTab}
            options={[
              { value: "staff", label: "Staff" },
              { value: "leave", label: "Leave" },
              { value: "reviews", label: "Reviews" },
              { value: "onboarding", label: "Onboarding" },
            ]}
          />
        }
      />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Active staff" value={stats.active} accent="cyan" icon={<Users size={17} />} />
        <StatCard label="Leave awaiting" value={stats.pendingLeave} accent="violet" icon={<CalendarOff size={17} />} />
        <StatCard label="Open checklist tasks" value={stats.openTasks} accent="blue" icon={<UserCheck size={17} />} />
        <StatCard label="Performance reviews" value={stats.reviews} accent="cyan" icon={<Star size={17} />} />
      </div>

      {error && <ErrorNote error={error} />}

      {tab === "staff" && (
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
          <Panel title="New staff member">
            <form onSubmit={addStaff} className="space-y-3">
              <Field label="First name"><input className="input" value={first} onChange={(e) => setFirst(e.target.value)} required /></Field>
              <Field label="Last name"><input className="input" value={last} onChange={(e) => setLast(e.target.value)} required /></Field>
              <Field label="Email"><input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
              <Field label="Role">
                <select className="input" value={role} onChange={(e) => setRole(e.target.value)}>
                  {["teacher", "admin", "support", "leadership", "finance", "other"].map((r) => <option key={r}>{r}</option>)}
                </select>
              </Field>
              <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} disabled={saving}>
                {saving ? "Adding…" : "Add staff"}
              </button>
            </form>
          </Panel>
          <DataTable columns={staffCols} rows={staff} filterKeys={["first_name", "last_name", "email"]} emptyLabel="No staff yet." />
        </div>
      )}

      {tab === "leave" && <DataTable columns={leaveCols} rows={leave} emptyLabel="No leave requests." />}
      {tab === "reviews" && <DataTable columns={reviewCols} rows={reviews} emptyLabel="No performance reviews." />}
      {tab === "onboarding" && <DataTable columns={taskCols} rows={tasks} filterKeys={["title"]} emptyLabel="No onboarding or offboarding tasks." />}
    </div>
  );
}
