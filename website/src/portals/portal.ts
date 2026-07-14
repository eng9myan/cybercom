/**
 * portal.cy-com.com — Patient / Citizen Portal Login Entry Point
 * Initiates CyIdentity login with portal branding hint.
 * This module is bundled separately and loaded on the portal redirect page.
 */

import { cyIdentity } from "../lib/auth/cyidentity.js";
import { config } from "../lib/config.js";

async function initPortalLogin(): Promise<void> {
  const params = new URLSearchParams(window.location.search);
  const returnUrl = params.get("return_url") ?? config.portals.portal;
  const prompt = params.get("prompt") as "login" | "none" | undefined;

  await cyIdentity.login({
    returnUrl,
    prompt: prompt ?? undefined,
    portalHint: "portal",
    extraScopes: ["cymed.patient.read", "cymed.appointments.write"],
  });
}

/** Redirect immediately to portal if already authenticated */
async function redirectIfAuthenticated(): Promise<void> {
  if (cyIdentity.isAuthenticated()) {
    const params = new URLSearchParams(window.location.search);
    const returnUrl = params.get("return_url") ?? config.portals.portal;
    window.location.href = returnUrl;
    return;
  }
  await initPortalLogin();
}

// Auto-execute on module load
redirectIfAuthenticated().catch(console.error);
