/**
 * Shared server-side helpers used by every setup orchestrator under app/api/cycom/setup/*.
 * Keeping these centralized keeps each wizard's orchestrator small and consistent.
 */

import { NextRequest } from 'next/server';
import { cycomCallKw } from '@/lib/cycomServer';

export async function cycomRpc<T = unknown>(
  req: NextRequest,
  model: string,
  method: string,
  args: unknown[] = [],
  kwargs: Record<string, unknown> = {},
): Promise<T> {
  const res = await cycomCallKw(req, { model, method, args, kwargs });
  const data = (await res.json()) as {
    result?: T;
    error?: { message?: string; data?: { message?: string } };
  };
  if (data.error) {
    throw new Error(
      data.error.data?.message || data.error.message || `Cycom backend error on ${model}.${method}`,
    );
  }
  return data.result as T;
}

export async function setParam(req: NextRequest, key: string, value: string): Promise<void> {
  await cycomRpc<boolean>(req, 'ir.config_parameter', 'set_param', [key, value]);
}

export async function getParam(req: NextRequest, key: string): Promise<string | null> {
  const v = await cycomRpc<string | false>(req, 'ir.config_parameter', 'get_param', [key, false]);
  if (v === false || v == null) return null;
  return String(v);
}

/**
 * Install an Cycom module if it isn't already installed. Returns one of:
 *   { installed: true, alreadyInstalled }      — success
 *   { installed: false, notFound: true }       — module name doesn't exist
 *   { installed: false, error: string }        — install failed
 *
 * Idempotent — safe to call repeatedly.
 */
export async function installModule(
  req: NextRequest,
  technicalName: string,
): Promise<
  | { installed: true; alreadyInstalled: boolean; shortdesc?: string }
  | { installed: false; notFound: true }
  | { installed: false; error: string }
> {
  try {
    const rows = await cycomRpc<Array<{ id: number; state: string; shortdesc?: string }>>(
      req,
      'ir.module.module',
      'search_read',
      [[['name', '=', technicalName]], ['id', 'state', 'shortdesc']],
      { limit: 1 },
    );
    if (!rows.length) return { installed: false, notFound: true };
    const mod = rows[0];
    if (mod.state === 'installed' || mod.state === 'to upgrade') {
      return { installed: true, alreadyInstalled: true, shortdesc: mod.shortdesc };
    }
    await cycomRpc(req, 'ir.module.module', 'button_immediate_install', [[mod.id]]);
    return { installed: true, alreadyInstalled: false, shortdesc: mod.shortdesc };
  } catch (e) {
    return { installed: false, error: e instanceof Error ? e.message : 'unknown error' };
  }
}

/** Install several modules, accumulate summary+warning lines. Order matters — earlier first. */
export async function installModules(
  req: NextRequest,
  modules: Array<{ name: string; required?: boolean }>,
  summary: string[],
  warnings: string[],
): Promise<void> {
  for (const m of modules) {
    const r = await installModule(req, m.name);
    if ('alreadyInstalled' in r && r.installed) {
      summary.push(
        r.alreadyInstalled
          ? `Module "${r.shortdesc ?? m.name}" already installed.`
          : `Installed "${r.shortdesc ?? m.name}".`,
      );
    } else if ('notFound' in r) {
      const msg = `Module "${m.name}" is not available in this Cycom instance.`;
      if (m.required) throw new Error(msg + ' Update Apps List in Cycom and retry.');
      warnings.push(msg);
    } else {
      const msg = `Failed to install "${m.name}": ${r.error}`;
      if (m.required) throw new Error(msg);
      warnings.push(msg);
    }
  }
}
