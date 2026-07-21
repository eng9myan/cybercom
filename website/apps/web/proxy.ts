import createMiddleware from "next-intl/middleware";
import { NextRequest, NextResponse } from "next/server";
import { locales, defaultLocale } from "./lib/i18n";

const intlMiddleware = createMiddleware({
  locales,
  defaultLocale,
});

// demo.cy-com.com: same Next.js app, one extra host-based rewrite before
// next-intl's own locale negotiation. Real DNS/nginx/cert setup for this
// host is a separate, later production step — this only makes the app
// itself host-aware so that step has something real to point at.
const DEMO_HOST_PREFIX = "demo.";

export default function proxy(request: NextRequest) {
  const host = request.headers.get("host") ?? "";
  if (host.startsWith(DEMO_HOST_PREFIX)) {
    const url = request.nextUrl.clone();
    const localeMatch = url.pathname.match(/^\/(en|ar)(\/.*)?$/);
    const locale = localeMatch?.[1] ?? defaultLocale;
    const rest = localeMatch?.[2] ?? url.pathname;
    // The demo host's root reuses the existing /demo-center product grid
    // as-is (real content, already built for www) — no duplicated page.
    if (rest === "/" || rest === "") {
      url.pathname = `/${locale}/demo-center`;
      return NextResponse.rewrite(url);
    }
  }
  return intlMiddleware(request);
}

export const config = {
  matcher: ["/", "/(ar|en)/:path*"],
};
