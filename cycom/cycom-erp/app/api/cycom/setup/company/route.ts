import { NextRequest, NextResponse } from 'next/server';
import { cycomCallKw } from '@/lib/cycomServer';

/**
 * Company Setup orchestrator.
 *
 * The real Company model (products.cycom.company) is much flatter than
 * Odoo's res.company: name, legal_name, tax_id, currency (a plain code
 * string, not an FK), parent_company, is_active -- no country_id/
 * currency_id lookups, no city field. Company is also opt-in in this
 * architecture (a tenant that never creates one is unaffected everywhere
 * else), so this wizard just creates/updates one if the tenant wants
 * multi-company; nothing else in Cycom requires it to exist.
 *
 *   1. Create or update the primary Company
 *   2. Create one child Company per branch if multiSite is true
 *   3. Persist business-level choices (industry, country, payment terms,
 *      pricing mode) as ir.config_parameter records for later wizards to
 *      read -- this is the only place the tenant's country/currency
 *      choice is recorded now, since the real model has nowhere to put a
 *      country FK.
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

async function setConfigParam(req: NextRequest, key: string, value: string): Promise<void> {
  await rpc<boolean>(req, 'ir.config_parameter', 'set_param', [key, value]);
}

async function findCompanyIdByName(req: NextRequest, name: string): Promise<string | null> {
  // res.company's adapter has no server-side name filter (Company has no
  // "name" django-filter field) -- the list is small (a handful of
  // companies per tenant), so filter client-side after fetching it all.
  const all = await rpc<Array<{ id: string; name: string }>>(req, 'res.company', 'search_read', [[], ['id', 'name']]);
  return all.find((c) => c.name === name)?.id ?? null;
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
    // 1) Create or update the primary company.
    const parentVals: Record<string, unknown> = {
      name: payload.legalName.trim(),
      currency: payload.currency.toUpperCase(),
    };
    if (payload.taxRegistrationNumber) {
      parentVals.tax_id = payload.taxRegistrationNumber.trim();
    }

    // If a company with the same name already exists, update it instead of creating a duplicate.
    const existingId = await findCompanyIdByName(req, payload.legalName.trim());

    let parentCompanyId: string;
    if (existingId) {
      parentCompanyId = existingId;
      await rpc<boolean>(req, 'res.company', 'write', [[parentCompanyId], parentVals]);
      summary.push(`Updated existing company "${payload.legalName}".`);
    } else {
      parentCompanyId = await rpc<string>(req, 'res.company', 'create', [parentVals]);
      summary.push(`Created company "${payload.legalName}".`);
    }

    // 2) Create branches as child companies if multi-site.
    const branchIds: string[] = [];
    if (payload.multiSite) {
      for (const branch of payload.branches) {
        if (!branch.name?.trim()) {
          warnings.push('Skipped a branch with empty name.');
          continue;
        }
        const branchVals: Record<string, unknown> = {
          name: `${payload.legalName.trim()} — ${branch.name.trim()}`,
          parent_company: parentCompanyId,
          currency: payload.currency.toUpperCase(),
        };
        try {
          const id = await rpc<string>(req, 'res.company', 'create', [branchVals]);
          branchIds.push(id);
          summary.push(`Created branch company "${branch.name}".`);
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
