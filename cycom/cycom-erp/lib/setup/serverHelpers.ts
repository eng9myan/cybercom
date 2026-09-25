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
 * Odoo-era holdover: onboarding used to "install a module" per tenant
 * (ir.module.module.button_immediate_install) to turn a feature on. The
 * rewritten backend has no such concept at all -- Django serves one shared
 * INSTALLED_APPS list to every tenant, so every app/model is already
 * available to everyone unconditionally. There is nothing to install.
 *
 * `ir.module.module` was never migrated (confirmed: zero entries in
 * lib/cycomServer.ts's MODEL_ADAPTERS), so every one of these calls
 * unconditionally threw -- and since payroll/pos/procurement/sales/
 * warehouse/hr all marked their core "module" `required: true`,
 * `installModules()` re-threw and hard-failed the whole onboarding step
 * with a 500, for every tenant, on every attempt. Rather than route each
 * of those ~30 module names to something real (there is nothing real for
 * most of them to route to), this now honestly reports "already
 * available" without any backend call -- the wizard's actual job (saving
 * the tenant's chosen preferences via ir.config_parameter, which IS real)
 * still happens exactly as before.
 */
export async function installModule(
  req: NextRequest,
  technicalName: string,
): Promise<{ installed: true; alreadyInstalled: true }> {
  void req;
  void technicalName;
  return { installed: true, alreadyInstalled: true };
}

/** See installModule() -- every entry reports "already available", nothing is called. */
export async function installModules(
  req: NextRequest,
  modules: Array<{ name: string; required?: boolean }>,
  summary: string[],
  warnings: string[],
): Promise<void> {
  void warnings;
  for (const m of modules) {
    await installModule(req, m.name);
    summary.push(`"${m.name}" is already available (no per-tenant activation needed).`);
  }
}
