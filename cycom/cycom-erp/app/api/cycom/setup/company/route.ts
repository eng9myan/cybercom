import { NextRequest, NextResponse } from 'next/server';
import { cycomCallKw } from '@/lib/cycomServer';

/**
 * Company Setup orchestrator.
 *
 * Takes the business-language wizard payload and translates it into a sequence of Cycom writes:
 *   1. Look up the country by code → res.country
 *   2. Look up the currency by name → res.currency (activate if inactive)
 *   3. Create or update the primary res.company (parent)
 *   4. Create one child res.company per branch if multiSite is true
 *   5. Persist business-level choices (industry, payment terms, pricing mode) as
 *      ir.config_parameter records keyed `cycom.tenant.*` for later wizards to read.
 *
 * Errors short-circuit and return partial progress + a clear message. Doctrine: any single failure
 * should leave the tenant in a recoverable state — we don't roll back what already succeeded
 * because Cycom doesn't support cross-call transactions over JSON-RPC, but we tell the user
 * exactly what got created.
 */

type CompanySetupBranch = { name: string; city?: string };

type Payload = {
  legalName: string;
  shortName?: string;
  industry: string;
  countryCode: string;
  currency: string;
  fiscalYearStartMonth: number;
  taxRegistrationNumber?: string;
  multiSite: boolean;
  branches: CompanySetupBranch[];
  paymentTerms: 'net_30' | 'net_15' | 'on_delivery' | 'cash';
  pricingMode: 'tax_inclusive' | 'tax_exclusive';
};

// Tiny helper: invoke cycomCallKw and unwrap result/error.
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
    const msg = data.error.data?.message || data.error.message || `Cycom backend error on ${model}.${method}`;
    throw new Error(msg);
  }
  return data.result as T;
}

async function findCountryId(req: NextRequest, code: string): Promise<number> {
  const rows = await rpc<Array<{ id: number }>>(req, 'res.country', 'search_read', [
    [['code', '=', code.toUpperCase()]],
    ['id'],
  ], { limit: 1 });
  if (!rows.length) throw new Error(`Country not found: ${code}`);
  return rows[0].id;
}

async function findCurrencyId(req: NextRequest, name: string): Promise<number> {
  // Currencies may be deactivated by default — search all, then activate if needed.
  const rows = await rpc<Array<{ id: number; active: boolean }>>(req, 'res.currency', 'search_read', [
    [['name', '=', name.toUpperCase()]],
    ['id', 'active'],
  ], { limit: 1, context: { active_test: false } });
  if (!rows.length) throw new Error(`Currency not found in Cycom: ${name}`);
  if (!rows[0].active) {
    await rpc<boolean>(req, 'res.currency', 'write', [[rows[0].id], { active: true }]);
  }
  return rows[0].id;
}

async function setConfigParam(req: NextRequest, key: string, value: string): Promise<void> {
  await rpc<boolean>(req, 'ir.config_parameter', 'set_param', [key, value]);
}

export async function POST(req: NextRequest) {
  let payload: Payload;
  try {
    payload = (await req.json()) as Payload;
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON payload' }, { status: 400 });
  }

  if (!payload.legalName?.trim()) {
    return NextResponse.json({ ok: false, error: 'Legal name is required' }, { status: 400 });
  }
  if (!payload.countryCode) {
    return NextResponse.json({ ok: false, error: 'Country is required' }, { status: 400 });
  }
  if (!payload.currency) {
    return NextResponse.json({ ok: false, error: 'Currency is required' }, { status: 400 });
  }

  const warnings: string[] = [];
  const summary: string[] = [];

  try {
    const countryId = await findCountryId(req, payload.countryCode);
    const currencyId = await findCurrencyId(req, payload.currency);

    // 1) Create or update the primary company.
    const parentVals: Record<string, unknown> = {
      name: payload.legalName.trim(),
      country_id: countryId,
      currency_id: currencyId,
    };
    if (payload.taxRegistrationNumber) {
      parentVals.vat = payload.taxRegistrationNumber.trim();
    }

    // If a company with the same name already exists, update it instead of creating a duplicate.
    const existing = await rpc<Array<{ id: number }>>(req, 'res.company', 'search_read', [
      [['name', '=', payload.legalName.trim()]],
      ['id'],
    ], { limit: 1 });

    let parentCompanyId: number;
    if (existing.length) {
      parentCompanyId = existing[0].id;
      await rpc<boolean>(req, 'res.company', 'write', [[parentCompanyId], parentVals]);
      summary.push(`Updated existing company "${payload.legalName}" (id ${parentCompanyId}).`);
    } else {
      parentCompanyId = await rpc<number>(req, 'res.company', 'create', [parentVals]);
      summary.push(`Created company "${payload.legalName}" (id ${parentCompanyId}).`);
    }

    // 2) Create branches as child companies if multi-site.
    const branchIds: number[] = [];
    if (payload.multiSite) {
      for (const branch of payload.branches) {
        if (!branch.name?.trim()) {
          warnings.push('Skipped a branch with empty name.');
          continue;
        }
        const branchVals: Record<string, unknown> = {
          name: `${payload.legalName.trim()} — ${branch.name.trim()}`,
          parent_id: parentCompanyId,
          country_id: countryId,
          currency_id: currencyId,
        };
        if (branch.city) branchVals.city = branch.city.trim();
        try {
          const id = await rpc<number>(req, 'res.company', 'create', [branchVals]);
          branchIds.push(id);
          summary.push(`Created branch company "${branch.name}" (id ${id}).`);
        } catch (e) {
          warnings.push(`Could not create branch "${branch.name}": ${e instanceof Error ? e.message : 'unknown error'}`);
        }
      }
    }

    // 3) Persist business-level choices as ir.config_parameter so downstream wizards inherit them.
    await setConfigParam(req, 'cycom.tenant.industry', payload.industry);
    await setConfigParam(req, 'cycom.tenant.country_code', payload.countryCode);
    await setConfigParam(req, 'cycom.tenant.short_name', payload.shortName || payload.legalName);
    await setConfigParam(req, 'cycom.tenant.fiscal_year_start_month', String(payload.fiscalYearStartMonth));
    await setConfigParam(req, 'cycom.tenant.payment_terms', payload.paymentTerms);
    await setConfigParam(req, 'cycom.tenant.pricing_mode', payload.pricingMode);
    await setConfigParam(req, 'cycom.tenant.setup.company_done', 'true');
    summary.push(`Saved tenant defaults: industry=${payload.industry}, fiscal-year-start=month ${payload.fiscalYearStartMonth}, payment terms=${payload.paymentTerms}, pricing=${payload.pricingMode}.`);

    return NextResponse.json({
      ok: true,
      parentCompanyId,
      branchIds,
      warnings,
      summary,
    });
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Setup failed';
    return NextResponse.json({ ok: false, error: message, warnings }, { status: 500 });
  }
}
