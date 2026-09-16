"use client";

import { useCallback, useEffect, useState } from "react";
import { Syringe, Pill, ShieldAlert } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { fmtDate } from "@/lib/portal";

/**
 * The health office: immunisation evidence and medication.
 *
 * Opens on gaps rather than the register, because the register is a list of
 * children nobody needs to do anything about. The gap list includes students
 * with *no* record at all — the common real case, and the one a report built
 * over existing rows silently misses.
 *
 * The outbreak view is separate and deliberately blunt: during a measles
 * notification the question is "who goes home today", and a medically exempt
 * child is on that list, not off it.
 */

type Gap = {
  student: string;
  name: string;
  year_level: number;
  status: string;
  verified_on: string | null;
  reason: string;
};

type Excluded = {
  student: string;
  name: string;
  year_level: number;
  status: string;
  basis: string;
};

type Due = {
  authority: string;
  student: string;
  name: string;
  medication: string;
  dose: string;
  route: string;
  max_doses_per_day: number;
  given_today: number;
  remaining_today: number;
  self_administer_permitted: boolean;
};

type Staff = { id: string; first_name: string; last_name: string };

const DISEASES = [
  "measles", "mumps", "rubella", "pertussis", "diphtheria", "tetanus",
  "polio", "hepatitis_b", "hib", "pneumococcal", "meningococcal", "varicella",
];

const STATUS_LABELS: Record<string, string> = {
  no_record: "No record",
  not_provided: "Not provided",
  catch_up: "On a catch-up schedule",
  medical_exemption: "Medical exemption",
  not_immunised: "Not immunised",
  up_to_date: "Up to date",
};

export default function HealthPage() {
  const [view, setView] = useState<"gaps" | "medication" | "outbreak">("gaps");
  const [gaps, setGaps] = useState<Gap[]>([]);
  const [due, setDue] = useState<Due[]>([]);
  const [excluded, setExcluded] = useState<Excluded[]>([]);
  const [disease, setDisease] = useState("measles");
  const [staff, setStaff] = useState<Staff[]>([]);
  const [givenBy, setGivenBy] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const toast = useToast();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      if (view === "gaps") {
        const d = await cyed.get<{ results: Gap[] }>("health/immunisations/gaps/");
        setGaps(d.results ?? []);
      } else if (view === "medication") {
        const d = await cyed.get<{ results: Due[] }>("health/medication-authorities/due-today/");
        setDue(d.results ?? []);
      } else {
        const d = await cyed.get<{ results: Excluded[] }>(
          `health/immunisations/outbreak-exclusions/?disease=${disease}`,
        );
        setExcluded(d.results ?? []);
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load the health register");
    } finally {
      setLoading(false);
    }
  }, [view, disease]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    (async () => {
      try {
        setStaff(await cyed.list<Staff>("hr/staff/"));
      } catch {
        // Administering degrades to unavailable rather than breaking the page.
      }
    })();
  }, []);

  const administer = async (row: Due) => {
    if (!givenBy) {
      toast.push("Choose who is giving the dose first — it is recorded against them.");
      return;
    }
    setBusy(row.authority);
    try {
      await cyed.action(`health/medication-authorities/${row.authority}/administer/`, {
        administered_by: givenBy,
        dose_given: row.dose,
        outcome: "given",
      });
      toast.push(`Dose recorded for ${row.name}.`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not record that dose");
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Health register"
        subtitle="Immunisation evidence, medication and outbreak exclusions"
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "gaps", label: "Immunisation gaps" },
              { value: "medication", label: "Medication today" },
              { value: "outbreak", label: "Outbreak" },
            ]}
          />
        }
      />

      {view === "gaps" && (
        <>
          <div className="card p-4" style={{ fontSize: 13, color: "var(--muted)" }}>
            {gaps.length === 0
              ? "Every enrolled student has acceptable, sighted immunisation evidence."
              : `${gaps.length} enrolled student(s) cannot be evidenced as immunised at enrolment. ` +
                "Students with no record at all are included — they are the ones a register-only report misses."}
          </div>
          {gaps.length === 0 ? (
            <Empty label="No gaps." />
          ) : (
            <Panel pad={false}>
              {gaps.map((row) => (
                <div
                  key={row.student}
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "0.75rem",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0.8rem 1.1rem",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                      <Syringe size={15} style={{ color: "var(--amber, #fbbf24)" }} />
                      <strong>{row.name}</strong>
                      <span className="pill" style={{ fontSize: "0.72rem" }}>
                        Year {row.year_level}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.83rem", color: "var(--muted)", marginTop: 2 }}>
                      {row.reason}
                      {row.verified_on && ` · verified ${fmtDate(row.verified_on)}`}
                    </div>
                  </div>
                  <Badge value={STATUS_LABELS[row.status] ?? row.status} />
                </div>
              ))}
            </Panel>
          )}
        </>
      )}

      {view === "medication" && (
        <>
          <Panel title="Who is giving the dose">
            <Field label="Staff member">
              <select className="input" value={givenBy} onChange={(e) => setGivenBy(e.target.value)}>
                <option value="">Choose…</option>
                {staff.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.first_name} {s.last_name}
                  </option>
                ))}
              </select>
            </Field>
            <p style={{ fontSize: "0.8rem", color: "var(--faint)", marginTop: "0.5rem" }}>
              Every dose is recorded against a named staff member. That record is the
              school&rsquo;s evidence that the medication was given as authorised.
            </p>
          </Panel>

          {due.length === 0 ? (
            <Empty label="No current medication authorities." />
          ) : (
            <Panel pad={false}>
              {due.map((row) => (
                <div
                  key={row.authority}
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "0.75rem",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0.85rem 1.1rem",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                      <Pill size={15} style={{ color: "var(--cyan)" }} />
                      <strong>{row.name}</strong>
                      {row.self_administer_permitted && <Badge value="may self-administer" />}
                    </div>
                    <div style={{ fontSize: "0.83rem", color: "var(--muted)", marginTop: 2 }}>
                      {row.medication} · {row.dose}
                      {row.route && ` · ${row.route}`} · {row.given_today} of{" "}
                      {row.max_doses_per_day} given today
                    </div>
                  </div>
                  <button
                    className="btn btn-primary"
                    disabled={busy !== null || row.remaining_today === 0}
                    title={row.remaining_today === 0 ? "Daily maximum already reached" : undefined}
                    onClick={() => administer(row)}
                  >
                    {row.remaining_today === 0 ? "Daily max reached" : "Record a dose"}
                  </button>
                </div>
              ))}
            </Panel>
          )}
        </>
      )}

      {view === "outbreak" && (
        <>
          <Panel title="Outbreak exclusion list">
            <Field label="Disease notified">
              <select className="input" value={disease} onChange={(e) => setDisease(e.target.value)}>
                {DISEASES.map((d) => (
                  <option key={d} value={d}>
                    {d.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </Field>
            <div
              style={{
                marginTop: "0.7rem",
                display: "flex",
                gap: 8,
                fontSize: 13,
                color: "var(--muted)",
              }}
            >
              <ShieldAlert size={16} style={{ flexShrink: 0, marginTop: 2 }} />
              <span>
                A medical exemption does not remove a child from this list. An exempt child is
                precisely the one an exclusion directive is written to protect.
              </span>
            </div>
          </Panel>

          {excluded.length === 0 ? (
            <Empty label="No student would need to be excluded for this disease." />
          ) : (
            <Panel
              pad={false}
              title={`${excluded.length} student(s) would be excluded`}
            >
              {excluded.map((row) => (
                <div
                  key={row.student}
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "0.75rem",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0.8rem 1.1rem",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <div>
                    <strong>{row.name}</strong>
                    <span style={{ color: "var(--muted)", fontSize: "0.83rem" }}>
                      {" "}· Year {row.year_level} · {row.basis}
                    </span>
                  </div>
                  <Badge value={STATUS_LABELS[row.status] ?? row.status} />
                </div>
              ))}
            </Panel>
          )}
        </>
      )}
    </div>
  );
}
