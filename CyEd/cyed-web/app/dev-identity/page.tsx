"use client";

import { useEffect, useState } from "react";
import { UserCog } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";

/**
 * Who am I signed in as — demo and evaluation only.
 *
 * The local instance has no Keycloak, so without this every visitor is a tenant
 * admin and the parent and student portals show the whole school. That is not
 * what those screens do in production, and demonstrating them that way is
 * worse than not demonstrating them: a school evaluating the product would
 * reasonably read it as a data leak.
 *
 * Switching identity here sets a cookie the API proxy turns into a bearer
 * token, so the real permission classes and the real student-scoping run — the
 * parent genuinely cannot fetch another family's child. This route does not
 * exist in a production build, and the production middleware rejects unsigned
 * tokens anyway.
 */

type Identity = { email: string; roles: string[]; sub?: string };

type Guardian = { id: string; first_name: string; last_name: string; email: string };
type Student = { id: string; first_name: string; last_name: string; email: string; year_level: number };
type Staff = { id: string; first_name: string; last_name: string; email: string; role: string };

const COOKIE = "cyed-dev-identity";

const readCookie = (): Identity | null => {
  const hit = document.cookie.split("; ").find((c) => c.startsWith(`${COOKIE}=`));
  if (!hit) return null;
  try {
    return JSON.parse(decodeURIComponent(hit.split("=").slice(1).join("=")));
  } catch {
    return null;
  }
};

const setIdentity = (identity: Identity | null) => {
  if (identity === null) {
    document.cookie = `${COOKIE}=; path=/; max-age=0`;
  } else {
    document.cookie = `${COOKIE}=${encodeURIComponent(JSON.stringify(identity))}; path=/; max-age=86400`;
  }
  // A full reload, not a router push: every page holds data fetched as the
  // previous identity, and showing one row of it under the new one is exactly
  // the confusion this screen exists to prevent.
  window.location.href = identity?.roles.includes("parent")
    ? "/portal"
    : identity?.roles.includes("student")
      ? "/student"
      : "/";
};

export default function DevIdentityPage() {
  const [current, setCurrent] = useState<Identity | null>(null);
  const [guardians, setGuardians] = useState<Guardian[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [staff, setStaff] = useState<Staff[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setCurrent(readCookie());
    (async () => {
      // Fetched as whoever is signed in now. As a parent this list is already
      // scoped down — which is the point being demonstrated.
      const safe = async <T,>(path: string): Promise<T[]> => {
        try {
          return await cyed.list<T>(path);
        } catch {
          return [];
        }
      };
      const [g, s, h] = await Promise.all([
        safe<Guardian>("sis/guardians/"),
        safe<Student>("sis/students/"),
        safe<Staff>("hr/staff/"),
      ]);
      setGuardians(g.filter((x) => x.email));
      setStudents(s.filter((x) => x.email));
      setStaff(h.filter((x) => x.email));
      setLoading(false);
    })();
  }, []);

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Sign in as"
        subtitle="Demo only — switch role to see what each person actually sees"
        action={
          current ? (
            <button className="btn" onClick={() => setIdentity(null)}>
              Back to admin
            </button>
          ) : undefined
        }
      />

      <div
        className="card p-4"
        style={{ fontSize: 13, color: "var(--muted)", display: "flex", gap: 10 }}
      >
        <UserCog size={18} style={{ flexShrink: 0, marginTop: 2 }} />
        <div>
          Currently:{" "}
          <strong style={{ color: "var(--ink)" }}>
            {current ? `${current.email} — ${current.roles.join(", ")}` : "admin@cyed.dev — tenant_admin"}
          </strong>
          <div style={{ marginTop: 4 }}>
            Permissions and student scoping are enforced by the backend, not by this
            page. A parent signed in here cannot load another family&rsquo;s child even by
            typing the URL — that is worth testing.
          </div>
        </div>
      </div>

      {loading ? (
        <SkeletonRows rows={6} />
      ) : (
        <>
          <Panel title="Staff">
            {staff.length === 0 ? (
              <Empty label="No staff with an email address." />
            ) : (
              <Rows>
                {staff.slice(0, 12).map((s) => (
                  <Row
                    key={s.id}
                    name={`${s.first_name} ${s.last_name}`}
                    detail={s.email}
                    tag={s.role || "staff"}
                    onPick={() =>
                      setIdentity({ email: s.email, roles: [s.role || "teacher"], sub: s.id })
                    }
                  />
                ))}
              </Rows>
            )}
          </Panel>

          <Panel title="Leadership and office">
            <Rows>
              {[
                { label: "Principal", roles: ["principal"], email: "principal@cyed.dev" },
                { label: "Wellbeing lead", roles: ["wellbeing"], email: "wellbeing@cyed.dev" },
                { label: "Business manager", roles: ["finance"], email: "finance@cyed.dev" },
                { label: "Tenant admin", roles: ["tenant_admin"], email: "admin@cyed.dev" },
              ].map((r) => (
                <Row
                  key={r.email}
                  name={r.label}
                  detail={r.email}
                  tag={r.roles[0]}
                  onPick={() => setIdentity({ email: r.email, roles: r.roles })}
                />
              ))}
            </Rows>
          </Panel>

          <Panel title="Parents and carers">
            {guardians.length === 0 ? (
              <Empty label="No guardians with an email address." />
            ) : (
              <Rows>
                {guardians.slice(0, 12).map((g) => (
                  <Row
                    key={g.id}
                    name={`${g.first_name} ${g.last_name}`}
                    detail={g.email}
                    tag="parent"
                    onPick={() => setIdentity({ email: g.email, roles: ["parent"], sub: g.id })}
                  />
                ))}
              </Rows>
            )}
          </Panel>

          <Panel title="Students">
            {students.length === 0 ? (
              <Empty label="No students with an email address." />
            ) : (
              <Rows>
                {students.slice(0, 12).map((s) => (
                  <Row
                    key={s.id}
                    name={`${s.first_name} ${s.last_name}`}
                    detail={`${s.email} · Year ${s.year_level}`}
                    tag="student"
                    onPick={() => setIdentity({ email: s.email, roles: ["student"], sub: s.id })}
                  />
                ))}
              </Rows>
            )}
          </Panel>
        </>
      )}
    </div>
  );
}

function Rows({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "grid", gap: "0.4rem" }}>{children}</div>;
}

function Row({
  name,
  detail,
  tag,
  onPick,
}: {
  name: string;
  detail: string;
  tag: string;
  onPick: () => void;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "0.75rem",
        padding: "0.5rem 0",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <div>
        <strong>{name}</strong>
        <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{detail}</div>
      </div>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
        <Badge value={tag} />
        <button className="btn" onClick={onPick}>
          Sign in
        </button>
      </div>
    </div>
  );
}
