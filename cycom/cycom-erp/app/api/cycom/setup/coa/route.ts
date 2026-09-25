import { NextRequest, NextResponse } from 'next/server';
import { cycomCallKw } from '@/lib/cycomServer';

/**
 * Chart of Accounts orchestrator.
 *
 * Used to install a per-country l10n_<cc> module (auto-loads a full chart
 * of accounts + tax templates) via Odoo's ir.module.module RPC, then
 * adjust the default sales/purchase tax rate. Neither ir.module.module
 * nor account.tax has any entry in MODEL_ADAPTERS -- there's no
 * "localization module" concept in the rewritten backend, and no central
 * tax-rate registry (products.cycom.sales/ar_ap store tax_percent inline
 * per line, not against a shared Tax entity). This always threw before
 * (confirmed live: every submission 500'd).
 *
 * Building a *real* per-country chart-of-accounts seeder (actual Account
 * rows per jurisdiction, not just a module-name string) is a genuinely
 * separate, larger feature -- flagged, not attempted here. What this now
 * does honestly: persist the tenant's choice (country/localization/tax
 * rates) via ir.config_parameter, which IS real, so the preference isn't
 * lost -- and tell the caller plainly that no accounts were created, so
 * the wizard doesn't claim more than actually happened.
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
  const warnings: string[] = [
    'No chart of accounts was created automatically -- set up accounts under Accounting → Chart of Accounts.',
  ];

  try {
    await rpc<boolean>(req, 'ir.config_parameter', 'set_param', ['cycom.tenant.setup.coa_done', 'true']);
    await rpc<boolean>(req, 'ir.config_parameter', 'set_param', ['cycom.tenant.coa_module', payload.l10nModule]);
    await rpc<boolean>(req, 'ir.config_parameter', 'set_param', ['cycom.tenant.coa_country', payload.countryCode]);
    await rpc<boolean>(req, 'ir.config_parameter', 'set_param', ['cycom.tenant.coa_sales_tax_pct', String(payload.salesTaxPct)]);
    await rpc<boolean>(req, 'ir.config_parameter', 'set_param', ['cycom.tenant.coa_purchase_tax_pct', String(payload.purchaseTaxPct)]);
    summary.push(
      `Saved chart-of-accounts preference: ${payload.countryCode} (${payload.l10nModule}), sales tax ${payload.salesTaxPct}%, purchase tax ${payload.purchaseTaxPct}%.`,
    );

    return NextResponse.json({ ok: true, summary, warnings, l10nModule: payload.l10nModule });
  } catch (e) {
    return NextResponse.json(
      { ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings },
      { status: 500 },
    );
  }
}
