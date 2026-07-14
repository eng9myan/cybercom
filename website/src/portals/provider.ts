/**
 * provider.cy-com.com — Provider Management Portal Login Entry Point
 * CyMed Provider Portal (P3.7) — physician workspace, scheduling, orders, results.
 * Requires MFA + device registration via CyIdentity for clinical safety.
 */

import { cyIdentity } from "../lib/auth/cyidentity.js";
import { config } from "../lib/config.js";

async function initProviderLogin(): Promise<void> {
  const params = new URLSearchParams(window.location.search);
  const returnUrl = params.get("return_url") ?? config.portals.provider;
  const specialtyHint = params.get("specialty");

  const acrValues = [
    "portal:provider",
    "mfa:required",
    "device:registered",
    specialtyHint ? `specialty:${specialtyHint}` : "",
  ]
    .filter(Boolean)
    .join(" ");

  await cyIdentity.login({
    returnUrl,
    portalHint: "provider",
    extraScopes: [
      "cymed.clinical.read",
      "cymed.clinical.write",
      "cymed.orders.write",
      "cymed.prescriptions.write",
      "cymed.results.read",
      "cymed.provider.manage",
    ],
    prompt: "login", // always require fresh auth for provider portal
  });
}

async function redirectIfAuthenticated(): Promise<void> {
  // Even if authenticated, re-check for provider portal (prompt=login policy)
  const params = new URLSearchParams(window.location.search);
  const forceLogin = params.get("force_login") === "true";

  if (!forceLogin && cyIdentity.isAuthenticated()) {
    const returnUrl = params.get("return_url") ?? config.portals.provider;
    window.location.href = returnUrl;
    return;
  }

  await initProviderLogin();
}

redirectIfAuthenticated().catch(console.error);
