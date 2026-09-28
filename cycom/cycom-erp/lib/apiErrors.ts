/** Flattens a DRF error body ({detail}, a string list, or a nested
 * field -> messages dict like {"lines": [{"quantity": ["..."]}]}) into
 * readable "field: message" lines, so a validation failure shows what to
 * fix instead of a generic "failed". */
export function formatApiErrors(body: unknown, prefix = ''): string[] {
  if (body == null) return [];
  if (typeof body === 'string') return [prefix ? `${prefix}: ${body}` : body];
  if (Array.isArray(body)) {
    return body.flatMap((item, idx) =>
      typeof item === 'string' ? formatApiErrors(item, prefix) : formatApiErrors(item, `${prefix}[${idx + 1}]`),
    );
  }
  if (typeof body === 'object') {
    return Object.entries(body as Record<string, unknown>).flatMap(([key, value]) =>
      formatApiErrors(value, key === 'detail' || key === 'non_field_errors' ? prefix : prefix ? `${prefix}.${key}` : key),
    );
  }
  return [String(body)];
}
