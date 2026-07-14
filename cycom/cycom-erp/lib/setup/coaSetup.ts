export type CoaSetupPayload = {
  countryCode: string;
  l10nModule: string;
  salesTaxPct: number;
  purchaseTaxPct: number;
};

export type CoaSetupResult =
  | { ok: true; summary: string[]; warnings: string[]; l10nModule: string; moduleId: number | null }
  | { ok: false; error: string; warnings?: string[] };

export async function applyCoaSetup(payload: CoaSetupPayload): Promise<CoaSetupResult> {
  const res = await fetch('/api/cycom/setup/coa', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    credentials: 'include',
  });
  return (await res.json()) as CoaSetupResult;
}

export type TenantPrefs = {
  industry?: string;
  countryCode?: string;
  pricingMode?: 'tax_inclusive' | 'tax_exclusive';
};

/** Read the cycom.tenant.* hints that Company Setup persisted in Cycom. */
export async function fetchTenantPrefs(): Promise<TenantPrefs> {
  const res = await fetch('/api/cycom/setup/tenant-prefs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });
  if (!res.ok) return {};
  return (await res.json()) as TenantPrefs;
}
