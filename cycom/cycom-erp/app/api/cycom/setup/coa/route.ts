import { NextRequest, NextResponse } from 'next/server';
import { cycomBackendJson, cycomCallKw } from '@/lib/cycomServer';

/**
 * Chart of Accounts orchestrator.
 *
 * Creates the tenant's chart from its country pack (platform.provisioning
 * country templates: a common IFRS-style backbone plus each country's own
 * statutory liabilities -- end-of-service provisions in the GCC/Jordan,
 * Zakat in Saudi Arabia, withholding tax, UK PAYE/NIC, ...), with Arabic
 * account names for an Arabic-locale tenant. Idempotent: accounts that
 * already exist are left untouched, so re-running only fills gaps.
 *
 * The chosen tax rates are stored as the tenant's defaults; tax itself is
 * applied per invoice line (there is no shared tax-rate entity to create).
 */

type Payload = {
  countryCode: string;
  l10nModule?: string;
  salesTaxPct: number;
  purchaseTaxPct: number;
};

async function setParam(req: NextRequest, key: string, value: string) {
  const res = await cycomCallKw(req, { model: 'ir.config_parameter', method: 'set_param', args: [key, value], kwargs: {} });
  const data = (await res.json()) as { error?: { message?: string } };
  if (data.error) throw new Error(data.error.message || `Could not save ${key}`);
}

export async function POST(req: NextRequest) {
  let payload: Payload;
  try {
    payload = (await req.json()) as Payload;
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON payload' }, { status: 400 });
  }
  const country = (payload.countryCode || '').trim().toUpperCase();
  if (!country) return NextResponse.json({ ok: false, error: 'Country is required' }, { status: 400 });

  const summary: string[] = [];
  const warnings: string[] = [];
  try {
    const seeded = await cycomBackendJson<{ created: number; existing: number; total: number; detail?: string }>(
      req, '/api/v1/accounting/chart/seed/', { method: 'POST', body: JSON.stringify({ country_code: country }) });
    if (!seeded.ok || !seeded.data) {
      return NextResponse.json(
        { ok: false, error: seeded.data?.detail || `Chart of accounts could not be created (${seeded.status})` },
        { status: seeded.status >= 400 ? seeded.status : 500 },
      );
    }
    summary.push(`Chart of accounts (${country}): created ${seeded.data.created} account(s), ${seeded.data.existing} already existed.`);

    await setParam(req, 'cycom.tenant.coa_country', country);
    await setParam(req, 'cycom.tenant.coa_sales_tax_pct', String(payload.salesTaxPct));
    await setParam(req, 'cycom.tenant.coa_purchase_tax_pct', String(payload.purchaseTaxPct));
    await setParam(req, 'cycom.tenant.setup.coa_done', 'true');
    summary.push(`Default tax rates: sales ${payload.salesTaxPct}%, purchases ${payload.purchaseTaxPct}%.`);

    return NextResponse.json({ ok: true, summary, warnings, created: seeded.data.created });
  } catch (e) {
    return NextResponse.json({ ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings }, { status: 500 });
  }
}
