import { NextRequest, NextResponse } from 'next/server';
import { cycomCallKw } from '@/lib/cycomServer';

/**
 * Chart of Accounts orchestrator.
 *
 * 1. Resolve the requested l10n_<cc> Cycom module
 * 2. If not installed, call ir.module.module.button_immediate_install (this is slow — up to ~60s)
 * 3. After install, adjust the default sales / purchase tax amounts to the user's preference
 * 4. Persist cycom.tenant.setup.coa_done
 *
 * Note: install is synchronous from Cycom's perspective but can take a while. Next.js route handlers
 * have no default timeout in dev. In production behind a reverse proxy, you may need to raise the
 * proxy timeout for this single endpoint.
 */

type Payload = {
  countryCode: string;
  l10nModule: string;
  salesTaxPct: number;
  purchaseTaxPct: number;
};

async function rpc<T = unknown>(
  req: NextRequest,
  model: string,
  method: string,
  args: unknown[] = [],
  kwargs: Record<string, unknown> = {},
): Promise<T> {
  const res = await cycomCallKw(req, { model, method, args, kwargs });
  const data = (await res.json()) as { result?: T; error?: { message?: string; data?: { message?: string } } };
  if (data.error) {
    throw new Error(data.error.data?.message || data.error.message || `Cycom backend error on ${model}.${method}`);
  }
  return data.result as T;
}

async function adjustTax(req: NextRequest, taxUse: 'sale' | 'purchase', targetPct: number, warnings: string[], summary: string[]): Promise<void> {
  if (targetPct <= 0) return;
  const taxes = await rpc<Array<{ id: number; name: string; amount: number }>>(
    req,
    'account.tax',
    'search_read',
    [
      [['type_tax_use', '=', taxUse], ['amount_type', '=', 'percent']],
      ['id', 'name', 'amount'],
    ],
    { limit: 1, order: 'sequence asc' },
  );
  if (!taxes.length) {
    warnings.push(`No default ${taxUse} tax found after installation — set manually under Accounting → Taxes.`);
    return;
  }
  const tax = taxes[0];
  if (Math.abs((tax.amount ?? 0) - targetPct) < 0.001) {
    summary.push(`Default ${taxUse} tax "${tax.name}" already at ${targetPct}%.`);
    return;
  }
  await rpc<boolean>(req, 'account.tax', 'write', [[tax.id], { amount: targetPct }]);
  summary.push(`Set default ${taxUse} tax "${tax.name}" to ${targetPct}%.`);
}

export async function POST(req: NextRequest) {
  let payload: Payload;
  try {
    payload = (await req.json()) as Payload;
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON payload' }, { status: 400 });
  }

  if (!payload.l10nModule?.trim()) {
    return NextResponse.json({ ok: false, error: 'Localization module is required' }, { status: 400 });
  }

  const summary: string[] = [];
  const warnings: string[] = [];

  try {
    // 1) Look up the module
    const rows = await rpc<Array<{ id: number; state: string; shortdesc?: string }>>(
      req,
      'ir.module.module',
      'search_read',
      [[['name', '=', payload.l10nModule]], ['id', 'state', 'shortdesc']],
      { limit: 1 },
    );
    if (!rows.length) {
      return NextResponse.json(
        {
          ok: false,
          error: `Cycom does not expose a module named "${payload.l10nModule}". Click Update Apps List in Cycom, or pick a different localization.`,
        },
        { status: 404 },
      );
    }
    const mod = rows[0];

    if (mod.state === 'installed' || mod.state === 'to upgrade') {
      summary.push(`Localization "${mod.shortdesc ?? payload.l10nModule}" already installed.`);
    } else {
      await rpc(req, 'ir.module.module', 'button_immediate_install', [[mod.id]]);
      summary.push(`Installed localization "${mod.shortdesc ?? payload.l10nModule}".`);
    }

    // 2) Adjust default taxes
    await adjustTax(req, 'sale', payload.salesTaxPct, warnings, summary);
    await adjustTax(req, 'purchase', payload.purchaseTaxPct, warnings, summary);

    // 3) Persist tenant flag
    await rpc<boolean>(req, 'ir.config_parameter', 'set_param', [
      'cycom.tenant.setup.coa_done', 'true',
    ]);
    await rpc<boolean>(req, 'ir.config_parameter', 'set_param', [
      'cycom.tenant.coa_module', payload.l10nModule,
    ]);

    return NextResponse.json({ ok: true, summary, warnings, l10nModule: payload.l10nModule, moduleId: mod.id });
  } catch (e) {
    return NextResponse.json(
      { ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings },
      { status: 500 },
    );
  }
}
