"use client";

import { useCallback, useEffect, useState } from "react";
import { LogIn, LogOut, ShieldCheck, ShieldAlert } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty, Field } from "@/components/ui";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";
import { fmtDateTime } from "@/lib/portal";

/**
 * Visitor sign-in.
 *
 * Front desk screen, so it opens on who is on site — that list is what gets
 * read out at an evacuation, and it is the only reason the register exists.
 *
 * Working With Children status is asked at sign-in and shown on the badge row.
 * A volunteer without a verified check is not blocked here, because the front
 * office is not the right place to adjudicate one, but they are visibly marked
 * so a teacher can decide whether to leave them with children.
 */

type Visitor = {
  id: string;
  full_name: string;
  organisation: string;
  purpose: string;
  host_name: string;
  badge_no: string;
  phone: string;
  signed_in_at: string | null;
  signed_out_at: string | null;
  wwc_verified: boolean;
};

export default function VisitorsPage() {
  const [view, setView] = useState<"onsite" | "today">("onsite");
  const [rows, setRows] = useState<Visitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const toast = useToast();

  const [name, setName] = useState("");
  const [org, setOrg] = useState("");
  const [purpose, setPurpose] = useState("");
  const [host, setHost] = useState("");
  const [phone, setPhone] = useState("");
  const [wwc, setWwc] = useState(false);

  const load = useCallback(async () => {
    try {
      setRows(await cyed.list<Visitor>("visitors/"));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load the visitor register");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const signIn = async () => {
    if (!name.trim()) return;
    setBusy("in");
    try {
      await cyed.create("visitors/", {
        full_name: name, organisation: org, purpose, host_name: host,
        phone, wwc_verified: wwc,
        badge_no: `V${Math.floor(100 + Math.random() * 900)}`,
      });
      toast.push(`${name} signed in.`);
      setName(""); setOrg(""); setPurpose(""); setHost(""); setPhone(""); setWwc(false);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not sign that visitor in");
    } finally {
      setBusy(null);
    }
  };

  const signOut = async (v: Visitor) => {
    setBusy(v.id);
    try {
      await cyed.action(`visitors/${v.id}/sign_out/`);
      toast.push(`${v.full_name} signed out.`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Could not sign that visitor out");
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;

  const onSite = rows.filter((v) => v.signed_in_at && !v.signed_out_at);
  const shown = view === "onsite" ? onSite : rows;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Visitors"
        subtitle={
          onSite.length
            ? `${onSite.length} visitor(s) on site right now`
            : "Nobody is signed in"
        }
        action={
          <Segmented
            value={view}
            onChange={setView}
            options={[
              { value: "onsite", label: `On site (${onSite.length})` },
              { value: "today", label: "Register" },
            ]}
          />
        }
      />

      <Panel title="Sign a visitor in">
        <div
          style={{
            display: "grid",
            gap: "0.9rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(12rem, 1fr))",
          }}
        >
          <Field label="Name">
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <Field label="Organisation">
            <input className="input" value={org} onChange={(e) => setOrg(e.target.value)} />
          </Field>
          <Field label="Here to see">
            <input className="input" value={host} onChange={(e) => setHost(e.target.value)} />
          </Field>
          <Field label="Purpose">
            <input className="input" value={purpose} onChange={(e) => setPurpose(e.target.value)} />
          </Field>
          <Field label="Phone">
            <input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </Field>
        </div>
        <label
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
            marginTop: "0.9rem",
            fontSize: "0.88rem",
          }}
        >
          <input type="checkbox" checked={wwc} onChange={(e) => setWwc(e.target.checked)} />
          Working With Children check sighted
        </label>
        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.9rem" }}>
          <button className="btn btn-primary" disabled={!name.trim() || busy !== null} onClick={signIn}>
            <LogIn size={15} style={{ marginRight: 6 }} />
            Sign in
          </button>
        </div>
      </Panel>

      {shown.length === 0 ? (
        <Empty label={view === "onsite" ? "Nobody is on site." : "No visitors recorded."} />
      ) : (
        <Panel pad={false}>
          {shown.map((v) => {
            const here = v.signed_in_at && !v.signed_out_at;
            return (
              <div
                key={v.id}
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
                    {v.wwc_verified ? (
                      <ShieldCheck size={15} style={{ color: "var(--green, #34d399)" }} />
                    ) : (
                      <ShieldAlert size={15} style={{ color: "var(--amber, #fbbf24)" }} />
                    )}
                    <strong>{v.full_name}</strong>
                    {v.badge_no && <Badge value={`badge ${v.badge_no}`} />}
                    {!here && <Badge value="signed out" />}
                  </div>
                  <div style={{ fontSize: "0.83rem", color: "var(--muted)", marginTop: 2 }}>
                    {v.organisation && `${v.organisation} · `}
                    {v.purpose}
                    {v.host_name && ` · seeing ${v.host_name}`}
                  </div>
                  <div style={{ fontSize: "0.78rem", color: "var(--faint)", marginTop: 2 }}>
                    In {fmtDateTime(v.signed_in_at)}
                    {v.signed_out_at && ` · out ${fmtDateTime(v.signed_out_at)}`}
                    {!v.wwc_verified && " · no WWC check sighted"}
                  </div>
                </div>
                {here && (
                  <button className="btn" disabled={busy !== null} onClick={() => signOut(v)}>
                    <LogOut size={14} style={{ marginRight: 4 }} />
                    Sign out
                  </button>
                )}
              </div>
            );
          })}
        </Panel>
      )}
    </div>
  );
}
