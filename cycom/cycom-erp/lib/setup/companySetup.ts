/**
 * Browser-side client + types for the Company Setup wizard.
 * Talks to /api/cycom/setup/company which orchestrates the actual Cycom calls server-side.
 */

import type { IndustryKey } from './industry-templates';

export type CompanySetupBranch = {
  name: string;
  city?: string;
};

export type CompanySetupPayload = {
  legalName: string;
  shortName?: string;
  industry: IndustryKey;
  countryCode: string;
  currency: string;
  fiscalYearStartMonth: number;
  taxRegistrationNumber?: string;
  multiSite: boolean;
  branches: CompanySetupBranch[];
  paymentTerms: 'net_30' | 'net_15' | 'on_delivery' | 'cash';
  pricingMode: 'tax_inclusive' | 'tax_exclusive';
};

export type CompanySetupResult = {
  ok: true;
  parentCompanyId: number;
  branchIds: number[];
  warnings: string[];
  summary: string[];
};

export type CompanySetupError = {
  ok: false;
  error: string;
  warnings?: string[];
};

export async function applyCompanySetup(
  payload: CompanySetupPayload,
): Promise<CompanySetupResult | CompanySetupError> {
  const res = await fetch('/api/cycom/setup/company', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    credentials: 'include',
  });
  const data = (await res.json()) as CompanySetupResult | CompanySetupError;
  return data;
}
