"use client";

import { useEffect, useState } from "react";
import { Building2, AlertTriangle } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { money } from "@/lib/portal";

/**
 * The group view: every campus side by side.
 *
 * The number that matters most here is the one nobody asks for — students with
 * no campus assigned. The rollup builds every figure by iterating campuses, so
 * those students land in no row and in no total: the group headline silently
 * understates the roll. That is the failure this page exists to surface.
 */

type CampusRow = {
  campus: string;
  name: string;
  state: string;
  students: number;
  staff: number;
  classes: number;
  fees_outstanding: string;
};

type Rollup = {
  campuses: CampusRow[];
  group_totals: {
    campuses: number;
    students: number;
    staff: number;
    classes: number;
    fees_outstanding: string;
    students_unassigned_campus: number;
  };
};

type Campus = { id: string; name: string; code: string; state: string; is_active: boolean };

const STATES = ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"];

export default function CampusesPage() {
  const [rollup, setRollup] = useState<Rollup | null>(null);
  const [campuses, setCampuses] = useState<Campus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [state, setState] = useState("NSW");
  const toast = useToast();

  const load = async () => {
    try {
      const [r, list] = await Promise.all([
        cyed.get<Rollup>("org/rollup/").catch(() => null),
        cyed.list<Campus>("org/campuses/"),
      ]);
      setRollup(r);
      setCampuses(list);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load campuses");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const add = async () => {
    if (!name.trim() || !code.trim()) return;
    setBusy(true);
    try {
      await cyed.create("org/campuses/", { name, code, state, is_active: true });
      toast.push("Campus added.");
      setName("");
      setCode("");
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not add that campus");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  const totals = rollup?.group_totals;
  const orphans = totals?.students_unassigned_campus ?? 0;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader title="Campuses" subtitle="Every site in the group, side by side" />

      {totals && (
        <div
          style={{
            display: "grid",
            gap: "0.6rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(10rem, 1fr))",
          }}
        >
          <div className="card p-5">
            <span className="label">Campuses</span>
            <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{totals.campuses}</div>
          </div>
          <div className="card p-5">
            <span className="label">Students</span>
            <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{totals.students}</div>
          </div>
          <div className="card p-5">
            <span className="label">Staff</span>
            <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{totals.staff}</div>
          </div>
          <div className="card p-5">
            <span className="label">Fees outstanding</span>
            <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>
              {money(totals.fees_outstanding)}
            </div>
          </div>
        </div>
      )}

      {orphans > 0 && (
        <div
          className="card p-4"
          style={{
            display: "flex",
            gap: 10,
            fontSize: 13,
            color: "var(--muted)",
            borderColor: "color-mix(in srgb, var(--amber, #fbbf24) 35%, var(--border))",
          }}
        >
          <AlertTriangle size={18} style={{ color: "var(--amber, #fbbf24)", flexShrink: 0 }} />
          <span>
            <strong style={{ color: "var(--ink)" }}>{orphans} student(s) have no campus.</strong>{" "}
            The rollup counts students per campus, so these appear in no campus row{" "}
            <em>and</em> in no group total — the {totals!.students} above understates the roll by{" "}
            {orphans}. Assign them before anyone reports either figure.
          </span>
        </div>
      )}

      {!rollup ? (
        <Empty label="The group rollup is leadership-only. Sign in as a principal to see totals." />
      ) : rollup.campuses.length === 0 ? (
        <Empty label="No campuses yet. Add the first one below." />
      ) : (
        <Panel pad={false}>
          <div style={{ overflowX: "auto" }}>
            <table className="table" style={{ width: "100%" }}>
              <thead>
                <tr>
                  <th>Campus</th>
                  <th>State</th>
                  <th style={{ textAlign: "right" }}>Students</th>
                  <th style={{ textAlign: "right" }}>Staff</th>
                  <th style={{ textAlign: "right" }}>Classes</th>
                  <th style={{ textAlign: "right" }}>Fees outstanding</th>
                </tr>
              </thead>
              <tbody>
                {rollup.campuses.map((c) => (
                  <tr key={c.campus}>
                    <td>
                      <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <Building2 size={15} style={{ color: "var(--faint)" }} />
                        <strong>{c.name}</strong>
                      </span>
                    </td>
                    <td>{c.state || "—"}</td>
                    <td style={{ textAlign: "right" }}>{c.students}</td>
                    <td style={{ textAlign: "right" }}>{c.staff}</td>
                    <td style={{ textAlign: "right" }}>{c.classes}</td>
                    <td style={{ textAlign: "right" }}>{money(c.fees_outstanding)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      <Panel title="Add a campus">
        <div
          style={{
            display: "grid",
            gap: "0.9rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(11rem, 1fr))",
            alignItems: "end",
          }}
        >
          <Field label="Name">
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <Field label="Code">
            <input
              className="input"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="e.g. PARR"
            />
          </Field>
          <Field label="State">
            <select className="input" value={state} onChange={(e) => setState(e.target.value)}>
              {STATES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </Field>
          <button className="btn btn-primary" disabled={busy || !name.trim() || !code.trim()} onClick={add}>
            Add campus
          </button>
        </div>
      </Panel>

      {campuses.length > 0 && (
        <Panel title="All campuses">
          <div style={{ display: "grid", gap: "0.4rem" }}>
            {campuses.map((c) => (
              <div
                key={c.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "0.75rem",
                  padding: "0.45rem 0",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <span>
                  <strong>{c.name}</strong>
                  <span style={{ color: "var(--muted)", fontSize: "0.83rem" }}>
                    {" "}· {c.code}
                    {c.state && ` · ${c.state}`}
                  </span>
                </span>
                <Badge value={c.is_active ? "active" : "inactive"} />
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}
