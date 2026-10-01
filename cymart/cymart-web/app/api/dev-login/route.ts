import { NextRequest, NextResponse } from "next/server";

// DEV-ONLY: GET /api/dev-login?user_id=<uuid> mints an unsigned dev-shaped
// JWT and sets it as a client-readable cookie, then redirects home. The
// Django backend's DevAuthMiddleware (core/dev_auth.py) never verifies
// this token's signature in dev mode — it only base64-decodes the
// payload — so no shared secret or Keycloak is needed. Mirrors cycom's
// lib/cycomServer.ts cycomDevLogin() precedent for this project family.
// Enabled only when the backend runs with CYMART_DEV_AUTH=1; this route
// itself has no effect on a real deployment's auth, since the real
// CyIdentityAuthMiddleware verifies signatures against actual Keycloak
// keys and simply rejects a token shaped like this.

function b64url(obj: unknown): string {
  return Buffer.from(JSON.stringify(obj)).toString("base64url");
}

function mintDevToken(userId: string): string {
  const header = { alg: "none", typ: "JWT" };
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    sub: userId,
    iat: now,
    exp: now + 60 * 60 * 12,
    roles: ["customer"],
    permissions: [],
  };
  return `${b64url(header)}.${b64url(payload)}.devsig`;
}

export async function GET(req: NextRequest) {
  const userId = req.nextUrl.searchParams.get("user_id") || crypto.randomUUID();
  const token = mintDevToken(userId);
  const redirectTo = req.nextUrl.searchParams.get("next") || "/";

  const res = NextResponse.redirect(new URL(redirectTo, req.url));
  res.cookies.set("cymart_token", token, {
    httpOnly: false, // must be JS-readable — lib/auth.ts attaches it as a Bearer header
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 12,
  });
  res.cookies.set("cymart_user_id", userId, { path: "/", maxAge: 60 * 60 * 12 });
  return res;
}
