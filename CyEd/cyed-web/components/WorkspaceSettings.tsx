"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, Pin, PinOff, RotateCcw, Sparkles, X } from "lucide-react";
import { NAV_GROUPS } from "@/lib/nav";
import { PRESETS, usePrefs } from "@/lib/prefs";

/**
 * Workspace customiser. Lets each person decide which of CyEd's ~28 modules
 * appear in their navigation, and which five reach the mobile bottom bar.
 *
 * Hidden modules stay reachable through the command palette (⌘K) — hiding is a
 * decluttering choice, never a permission boundary. Access control lives on the
 * server; this only changes what is on screen.
 */
export default function WorkspaceSettings({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { prefs, update, toggleHidden, togglePinned, reset, applyPreset } = usePrefs();
  const [, force] = useState(0);

  // Close on Escape — every overlay needs a keyboard escape route.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const counts = useMemo(() => {
    const total = NAV_GROUPS.reduce((n, g) => n + g.items.length, 0);
    return { total, visible: total - prefs.hidden.length };
  }, [prefs.hidden.length]);

  if (!open) return null;

  return (
    <div className="cmdk-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Customise workspace">
      <div className="ws-panel" onClick={(e) => e.stopPropagation()}>
        <header className="ws-head">
          <div>
            <h2 style={{ fontSize: "1.05rem", fontWeight: 800 }}>Customise workspace</h2>
            <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
              {counts.visible} of {counts.total} modules shown · hidden ones stay searchable with ⌘K
            </p>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <X size={16} />
          </button>
        </header>

        <div className="ws-body">
          <section aria-labelledby="ws-presets">
            <div id="ws-presets" className="label" style={{ marginBottom: 8 }}>
              Start from a role
            </div>
            <div className="ws-presets">
              {PRESETS.map((p) => (
                <button
                  key={p.id}
                  className={`ws-preset ${prefs.preset === p.id ? "active" : ""}`}
                  onClick={() => {
                    applyPreset(p.id);
                    force((n) => n + 1);
                  }}
                >
                  <span style={{ fontWeight: 700, fontSize: "0.85rem" }}>{p.label}</span>
                  <span style={{ fontSize: 11, color: "var(--muted)" }}>{p.description}</span>
                  {prefs.preset === p.id && <Check size={14} className="ws-preset-check" />}
                </button>
              ))}
            </div>
          </section>

          <section aria-labelledby="ws-modules" style={{ marginTop: 22 }}>
            <div id="ws-modules" className="label" style={{ marginBottom: 8 }}>
              Modules
            </div>
            {NAV_GROUPS.map((g) => (
              <div key={g.group} style={{ marginBottom: 14 }}>
                <div className="ws-group">{g.group}</div>
                {g.items.map(({ href, label, icon: Icon }) => {
                  const hidden = prefs.hidden.includes(href);
                  const pinned = prefs.pinned.includes(href);
                  return (
                    <div key={href} className={`ws-row ${hidden ? "off" : ""}`}>
                      <label className="ws-row-main">
                        <input
                          type="checkbox"
                          checked={!hidden}
                          onChange={() => toggleHidden(href)}
                          aria-label={`Show ${label}`}
                        />
                        <Icon size={15} aria-hidden="true" />
                        <span>{label}</span>
                      </label>
                      <button
                        className="ws-pin"
                        onClick={() => togglePinned(href)}
                        disabled={hidden}
                        aria-pressed={pinned}
                        aria-label={pinned ? `Unpin ${label} from bottom bar` : `Pin ${label} to bottom bar`}
                        title={pinned ? "Pinned to mobile bottom bar" : "Pin to mobile bottom bar"}
                      >
                        {pinned ? <Pin size={14} /> : <PinOff size={14} />}
                      </button>
                    </div>
                  );
                })}
              </div>
            ))}
          </section>

          <section aria-labelledby="ws-display" style={{ marginTop: 8 }}>
            <div id="ws-display" className="label" style={{ marginBottom: 8 }}>
              Display
            </div>
            <div className="ws-row">
              <span style={{ fontSize: "0.85rem" }}>Compact density</span>
              <input
                type="checkbox"
                checked={prefs.density === "compact"}
                onChange={(e) => update({ density: e.target.checked ? "compact" : "comfortable" })}
                aria-label="Compact density"
              />
            </div>
            <div className="ws-row">
              <span style={{ fontSize: "0.85rem" }}>
                Reduce motion
                <span style={{ display: "block", fontSize: 11, color: "var(--faint)" }}>
                  {prefs.reduceMotion === null ? "Following your device setting" : "Overriding your device setting"}
                </span>
              </span>
              <input
                type="checkbox"
                checked={prefs.reduceMotion === true}
                onChange={(e) => update({ reduceMotion: e.target.checked ? true : null })}
                aria-label="Reduce motion"
              />
            </div>
          </section>
        </div>

        <footer className="ws-foot">
          <button className="btn btn-ghost" onClick={reset}>
            <RotateCcw size={14} /> Reset
          </button>
          <button className="btn btn-primary" onClick={onClose}>
            <Sparkles size={14} /> Done
          </button>
        </footer>
      </div>
    </div>
  );
}
