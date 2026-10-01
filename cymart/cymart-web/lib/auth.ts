"use client";

const TOKEN_COOKIE = "cymart_token";

/** Reads the dev-session token the browser set after /api/dev-login. In
 * production this cookie is set by the real identity flow instead — this
 * module only knows how to read it, never how it was minted. */
export function getToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${TOKEN_COOKIE}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export function clearToken(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0`;
}

export function isAuthed(): boolean {
  return !!getToken();
}
