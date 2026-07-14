/**
 * CyberCom shared utility functions.
 * Used by frontend and mobile TypeScript applications.
 */

/** Format a date string to locale-appropriate display. */
export function formatDate(
  isoString: string,
  locale: "ar" | "en" = "en",
  options?: Intl.DateTimeFormatOptions
): string {
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
    ...options,
  };
  return new Intl.DateTimeFormat(locale === "ar" ? "ar-SA" : "en-US", defaultOptions).format(
    new Date(isoString)
  );
}

/** Truncate string with ellipsis. */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength - 3)}...`;
}

/** Deep clone a plain object (JSON-safe). */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj)) as T;
}

/** Check if a JWT token is expired. */
export function isTokenExpired(expiresAt: number, bufferSeconds = 60): boolean {
  return Date.now() >= (expiresAt - bufferSeconds) * 1000;
}

/** Generate a UUID v4. */
export function generateUUID(): string {
  return crypto.randomUUID();
}

/** Convert snake_case to camelCase. */
export function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase());
}

/** Convert object keys from snake_case to camelCase recursively. */
export function keysToCamelCase<T>(obj: unknown): T {
  if (Array.isArray(obj)) {
    return obj.map(keysToCamelCase) as T;
  }
  if (obj !== null && typeof obj === "object") {
    return Object.fromEntries(
      Object.entries(obj as Record<string, unknown>).map(([k, v]) => [
        toCamelCase(k),
        keysToCamelCase(v),
      ])
    ) as T;
  }
  return obj as T;
}
