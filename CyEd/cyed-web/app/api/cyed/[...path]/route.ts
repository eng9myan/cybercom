import { NextRequest, NextResponse } from "next/server";

// Server-side proxy to the CyEd Django backend. Injects the demo tenant header
// so the dev-auth backend scopes to the seeded school. In production this is
// where a real OIDC access token + the authenticated user's tenant would be
// attached instead.
const BACKEND = process.env.CYED_BACKEND_URL || "http://localhost:8095";
const DEV_TENANT = process.env.CYED_DEV_TENANT_ID || "11111111-1111-1111-1111-111111111111";

/**
 * Demo identity.
 *
 * With no Authorization header the dev backend falls back to `tenant_admin`,
 * which makes every screen an admin screen — the parent portal then lists every
 * child in the school rather than one family's, because the scoping code is
 * never asked to do anything. That looks like a data leak in a demo and hides
 * whether the real scoping works at all.
 *
 * So the `cyed-dev-identity` cookie is turned into an unsigned JWT and sent as
 * a bearer token. The dev middleware reads its claims and every downstream
 * permission and scoping path then runs for real.
 *
 * This is development only. Production runs `core.settings`, whose middleware
 * verifies signatures — an unsigned token like this is rejected outright.
 */
const DEV_IDENTITY_ENABLED = process.env.NODE_ENV !== "production";

function devBearer(raw: string | undefined): string | null {
  if (!DEV_IDENTITY_ENABLED || !raw) return null;
  try {
    const identity = JSON.parse(raw) as { email?: string; roles?: string[]; sub?: string };
    if (!identity.email || !Array.isArray(identity.roles) || identity.roles.length === 0) {
      return null;
    }
    const b64 = (o: unknown) =>
      Buffer.from(JSON.stringify(o)).toString("base64url");
    // No signature: the dev middleware decodes without verifying, and the real
    // one would reject this whatever we put in the third segment.
    return `${b64({ alg: "none", typ: "JWT" })}.${b64({
      sub: identity.sub || identity.email,
      email: identity.email,
      roles: identity.roles,
      tenant_id: DEV_TENANT,
    })}.`;
  } catch {
    return null;
  }
}

async function forward(req: NextRequest, path: string[]) {
  const suffix = path.join("/");
  const search = req.nextUrl.search || "";
  const url = `${BACKEND}/api/v1/${suffix}/${search}`.replace(/\/\/(?=\?|$)/, "/");

  const headers: Record<string, string> = { "X-Tenant-ID": DEV_TENANT };
  const bearer = devBearer(req.cookies.get("cyed-dev-identity")?.value);
  if (bearer) headers["Authorization"] = `Bearer ${bearer}`;
  // Forward the client's content-type (JSON, or multipart for logo uploads).
  const ct = req.headers.get("content-type");
  if (ct) headers["content-type"] = ct;

  const init: RequestInit = { method: req.method, headers };
  if (!["GET", "HEAD"].includes(req.method)) {
    init.body = Buffer.from(await req.arrayBuffer());
  }

  let upstream: Response;
  try {
    upstream = await fetch(url, init);
  } catch {
    return NextResponse.json(
      { detail: "CyEd backend unreachable. Start it on :8095 (settings_dev)." },
      { status: 502 },
    );
  }

  // Binary-safe pass-through (PDFs, logo images) — never decode as text.
  const body = Buffer.from(await upstream.arrayBuffer());
  const contentType = upstream.headers.get("content-type") || "application/json";
  return new NextResponse(body, {
    status: upstream.status,
    headers: { "content-type": contentType },
  });
}

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}
export async function POST(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}
export async function PATCH(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}
export async function DELETE(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}
