/**
 * Cycom UI ↔ Cycom model mapping helpers.
 *
 * Each Cycom module page calls `useCycomList(model, domain, fields, mapper)` and gets
 * back `{ rows, loading, error, reload }`. The mapper converts an Cycom record into
 * whatever shape the existing page UI already expects, so wiring a page = (a) point
 * at the right Cycom model, (b) list the Cycom fields you need, (c) write a one-liner
 * that maps Cycom → existing UI shape. Nothing else changes; visual design is untouched.
 */

import { useCallback, useEffect, useState } from 'react';
import { searchRead } from '@/lib/cycom';

export type Many2One = [number, string] | false | null;

export function m2oName(v: Many2One | undefined, fallback = '—'): string {
  if (!v) return fallback;
  return v[1] ?? fallback;
}

export function m2oId(v: Many2One | undefined): number | null {
  return v ? v[0] : null;
}

export function fmtDate(s?: string): string {
  if (!s) return '—';
  const d = new Date(s.replace(' ', 'T') + (s.length === 10 ? '' : 'Z'));
  if (isNaN(d.getTime())) return s;
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: '2-digit' });
}

export function fmtMoney(n?: number, currency = ''): string {
  if (n == null) return '—';
  return `${currency ? currency + ' ' : ''}${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function fmtCode(prefix: string, id: number, width = 4): string {
  return `${prefix}-${String(id).padStart(width, '0')}`;
}

export type CycomListOpts<T> = {
  limit?: number;
  order?: string;
  /** Re-fetch when any of these change */
  deps?: unknown[];
};

export function useCycomList<TRaw, TMapped>(
  model: string,
  domain: unknown[],
  fields: string[],
  mapper: (r: TRaw) => TMapped,
  opts: CycomListOpts<TMapped> = {},
) {
  const [rows, setRows] = useState<TMapped[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    searchRead<TRaw>(model, domain, fields, { limit: opts.limit ?? 200, order: opts.order })
      .then((raw) => setRows(raw.map(mapper)))
      .catch((e) => setError(e instanceof Error ? e.message : `Failed to load ${model}`))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model, JSON.stringify(domain), JSON.stringify(fields), opts.limit, opts.order]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    searchRead<TRaw>(model, domain, fields, { limit: opts.limit ?? 200, order: opts.order })
      .then((raw) => {
        if (!cancelled) setRows(raw.map(mapper));
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : `Failed to load ${model}`);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model, JSON.stringify(domain), JSON.stringify(fields), opts.limit, opts.order, ...(opts.deps || [])]);

  return { rows, loading, error, reload: load };
}
