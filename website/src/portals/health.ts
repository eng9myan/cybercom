/**
 * health.cy-com.com — Clinical / Healthcare Portal Login Entry Point
 * CyMed Patient Portal (P3.6) and Provider clinical tools (P3.7).
 * Initiates CyIdentity login with health portal branding and MFA enforcement.
 */

import { cyIdentity } from "../lib/auth/cyidentity.js";
import { config } from "../lib/config.js";

async function initHealthLogin(): Promise<void> {
  const params = new URLSearchParams(window.location.search);
  const returnUrl = params.get("return_url") ?? config.portals.health;
  const role = params.get("role") ?? "patient";

  const extraScopes =
    role === "provider"
      ? ["cymed.clinical.read", "cymed.clinical.write", "cymed.orders.write"]
      : ["cymed.patient.read", "cymed.health_records.read"];

  await cyIdentity.login({
    returnUrl,
    portalHint: "health",
    extraScopes,
    prompt: "login", // always require fresh auth for clinical access
  });
}

async function redirectIfAuthenticated(): Promise<void> {
  if (cyIdentity.isAuthenticated()) {
    const params = new URLSearchParams(window.location.search);
    const returnUrl = params.get("return_url") ?? config.portals.health;
    window.location.href = returnUrl;
    return;
  }
  await initHealthLogin();
}

redirectIfAuthenticated().catch(console.error);
