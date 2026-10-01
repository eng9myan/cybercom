"use client";

import { useSyncExternalStore } from "react";
import { KeyRound } from "lucide-react";
import { isAuthed } from "@/lib/auth";

// Cookie state never changes from outside this tab's own navigation, so
// there's nothing to subscribe to — useSyncExternalStore here purely to
// read browser-only state safely (server snapshot assumes authed, so SSR
// never flashes the banner before the client can check the real cookie).
function subscribe() {
  return () => {};
}

/** Dev-only: shows a one-click sign-in when no session cookie exists yet,
 * so the app is usable immediately against core.settings_dev without a
 * real identity provider. Renders nothing once a token is present. */
export function DevLoginBanner() {
  const authed = useSyncExternalStore(subscribe, isAuthed, () => true);

  if (authed) return null;

  return (
    <div
      className="border-b px-4 py-2.5 text-[13px]"
      style={{ background: "var(--amber-bg)", borderColor: "var(--line)", color: "var(--amber)" }}
    >
      <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
        <span className="flex items-center gap-1.5">
          <KeyRound size={14} />
          No dev session yet — sign in to talk to CyMart.
        </span>
        <a
          href="/api/dev-login"
          className="rounded-[8px] border px-2.5 py-1 text-xs font-medium transition hover:brightness-95"
          style={{ borderColor: "var(--line-2)", background: "var(--panel)", color: "var(--ink)" }}
        >
          Dev sign in
        </a>
      </div>
    </div>
  );
}
