"use client";

import React, { useState } from "react";
import { Empty } from "@/components/ui";

export type Column<T> = {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  width?: number | string;
  align?: "left" | "right" | "center";
};

/** Glass data table: sticky header, horizontal scroll containment, row-hover
    glow, optional inline filter + selectable rows with a sliding bulk bar. */
export function DataTable<T extends { id?: string | number }>({
  columns,
  rows,
  filterKeys,
  emptyLabel = "Nothing here yet.",
  bulkActions,
}: {
  columns: Column<T>[];
  rows: T[];
  filterKeys?: (keyof T)[];
  emptyLabel?: string;
  bulkActions?: (selected: T[], clear: () => void) => React.ReactNode;
}) {
  const [q, setQ] = useState("");
  const [sel, setSel] = useState<Set<string | number>>(new Set());

  const filtered =
    filterKeys && q.trim()
      ? rows.filter((r) =>
          filterKeys.some((k) => String(r[k] ?? "").toLowerCase().includes(q.toLowerCase()))
        )
      : rows;

  const selected = rows.filter((r) => r.id != null && sel.has(r.id));
  const clear = () => setSel(new Set());
  const toggle = (id: string | number) =>
    setSel((s) => {
      const n = new Set(s);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });

  return (
    <div className="card" style={{ overflow: "hidden" }}>
      {filterKeys && (
        <div style={{ padding: "0.7rem 0.8rem", borderBottom: "1px solid var(--border)" }}>
          <input
            className="input"
            placeholder="Filter…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            style={{ maxWidth: 280 }}
            aria-label="Filter rows"
          />
        </div>
      )}

      {filtered.length === 0 ? (
        <div style={{ padding: "1rem" }}>
          <Empty label={emptyLabel} />
        </div>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                {bulkActions && <th style={{ width: 36 }} aria-label="Select" />}
                {columns.map((c) => (
                  <th key={c.key} style={{ width: c.width, textAlign: c.align ?? "left" }}>
                    {c.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="stagger">
              {filtered.map((r, i) => (
                <tr key={r.id ?? i}>
                  {bulkActions && (
                    <td>
                      <input
                        type="checkbox"
                        checked={r.id != null && sel.has(r.id)}
                        onChange={() => r.id != null && toggle(r.id)}
                        aria-label="Select row"
                      />
                    </td>
                  )}
                  {columns.map((c) => (
                    <td key={c.key} style={{ textAlign: c.align ?? "left" }}>
                      {c.render ? c.render(r) : String((r as Record<string, unknown>)[c.key] ?? "—")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {bulkActions && selected.length > 0 && (
        <div
          style={{
            position: "sticky",
            bottom: 0,
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "0.7rem 1rem",
            borderTop: "1px solid var(--border-strong)",
            background: "var(--panel-solid)",
            animation: "fade-up 0.25s ease both",
          }}
        >
          <span className="pill">{selected.length} selected</span>
          <div style={{ flex: 1 }} />
          {bulkActions(selected, clear)}
        </div>
      )}
    </div>
  );
}
