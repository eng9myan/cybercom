import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export function GET() {
  return NextResponse.json(
    {
      status: "ok",
      service: "cybercom-website",
      release: process.env.APP_RELEASE ?? "development",
    },
    { headers: { "Cache-Control": "no-store" } },
  );
}
