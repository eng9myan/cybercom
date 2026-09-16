"use client";

import { useEffect, useState } from "react";
import { Check, X, Link2 } from "lucide-react";
import { cyed, cyedUrl } from "@/lib/cyed";
import { PageHeader, ErrorNote, SkeletonRows, Empty } from "@/components/ui";
import { Panel, Badge } from "@/components/kit";

/**
 * SIF AU interoperability.
 *
 * This page exists to be shown to an assessor, so it leads with what is *not*
 * built. CyEd implements the SIF AU v3.x data mapping and a stable RefId
 * registry; it is not a certified Zone integration, and describing it as "SIF
 * compliant" in a tender would be a false claim the school would wear.
 *
 * The element gaps are listed per object rather than summarised. "Mostly
 * mapped" is not something a jurisdiction's test harness accepts.
 */

type Coverage = {
  conformance: string;
  disclaimer: string;
  implemented: {
    objects: string[];
    bindings: string[];
    refids: string;
    pattern: string;
  };
  not_implemented: string[];
  // Each gap names the SIF element and why it is unmapped — not a string.
  element_gaps: Record<string, { element: string; reason: string }[]>;
  refids_issued: number;
};

export default function InteroperabilityPage() {
  const [data, setData] = useState<Coverage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setData(await cyed.get<Coverage>("sif/coverage/"));
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load SIF coverage");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <SkeletonRows rows={5} />;
  if (error) return <ErrorNote error={error} />;
  if (!data) return <Empty label="No coverage information." />;

  return (
    <div style={{ display: "grid", gap: "1.25rem" }}>
      <PageHeader
        title="Interoperability (SIF AU)"
        subtitle="What is implemented, and what is not"
        action={<Badge value={data.conformance.replace(/-/g, " ")} />}
      />

      <div
        className="card p-4"
        style={{
          fontSize: 13,
          lineHeight: 1.6,
          color: "var(--muted)",
          borderColor: "color-mix(in srgb, var(--amber, #fbbf24) 35%, var(--border))",
        }}
      >
        {data.disclaimer}
      </div>

      <div
        style={{
          display: "grid",
          gap: "0.6rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(10rem, 1fr))",
        }}
      >
        <div className="card p-5">
          <span className="label">Objects mapped</span>
          <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{data.implemented.objects.length}</div>
        </div>
        <div className="card p-5">
          <span className="label">RefIds issued</span>
          <div style={{ fontSize: "1.9rem", fontWeight: 800 }}>{data.refids_issued}</div>
        </div>
        <div className="card p-5">
          <span className="label">Bindings</span>
          <div style={{ fontSize: "1.1rem", fontWeight: 700, marginTop: 8 }}>
            {data.implemented.bindings.join(", ").toUpperCase()}
          </div>
        </div>
        <div className="card p-5">
          <span className="label">Pattern</span>
          <div style={{ fontSize: "0.95rem", fontWeight: 600, marginTop: 8 }}>
            {data.implemented.pattern}
          </div>
        </div>
      </div>

      <Panel title="Not implemented — read this first">
        <ul style={{ display: "grid", gap: "0.5rem", paddingLeft: 0, listStyle: "none" }}>
          {data.not_implemented.map((item) => (
            <li key={item} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
              <X size={16} style={{ color: "var(--red, #f87171)", flexShrink: 0, marginTop: 3 }} />
              <span style={{ fontSize: "0.9rem", lineHeight: 1.5 }}>{item}</span>
            </li>
          ))}
        </ul>
      </Panel>

      <Panel title="Objects and their element gaps">
        <p style={{ color: "var(--muted)", fontSize: "0.86rem", marginBottom: "0.9rem" }}>
          RefIds are {data.implemented.refids}.
        </p>
        <div style={{ display: "grid", gap: "0.7rem" }}>
          {data.implemented.objects.map((name) => {
            const gaps = data.element_gaps[name] ?? [];
            return (
              <div
                key={name}
                style={{
                  padding: "0.7rem 0.9rem",
                  border: "1px solid var(--border)",
                  borderRadius: 12,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "0.75rem",
                    alignItems: "center",
                    flexWrap: "wrap",
                  }}
                >
                  <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    {gaps.length === 0 ? (
                      <Check size={15} style={{ color: "var(--green, #34d399)" }} />
                    ) : (
                      <X size={15} style={{ color: "var(--amber, #fbbf24)" }} />
                    )}
                    <strong>{name}</strong>
                  </span>
                  <span style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                    <span style={{ fontSize: "0.8rem", color: "var(--faint)" }}>
                      {gaps.length === 0 ? "no known gaps" : `${gaps.length} gap(s)`}
                    </span>
                    {data.implemented.bindings.map((b) => (
                      <a
                        key={b}
                        className="btn"
                        style={{ padding: "0.25rem 0.6rem", fontSize: "0.78rem" }}
                        href={cyedUrl(`sif/objects/${name}/?binding=${b}`)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <Link2 size={12} style={{ marginRight: 4 }} />
                        {b.toUpperCase()}
                      </a>
                    ))}
                  </span>
                </div>
                {gaps.length > 0 && (
                  <ul
                    style={{
                      margin: "0.5rem 0 0",
                      paddingLeft: "1.1rem",
                      color: "var(--muted)",
                      fontSize: "0.84rem",
                      lineHeight: 1.6,
                    }}
                  >
                    {/* Keyed by index: two gaps can name the same element for
                        different reasons, so the element alone is not unique. */}
                    {gaps.map((g, i) => (
                      <li key={`${name}-${i}`}>
                        <code style={{ fontSize: "0.82rem" }}>{g.element}</code> — {g.reason}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      </Panel>
    </div>
  );
}
