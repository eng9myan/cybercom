import type { SalesMotion } from './sales-templates';

export type SalesSetupPayload = {
  motion: SalesMotion;
  freeDiscountLimitPct: number;
  managerDiscountLimitPct: number;
  dualApprovalThresholdPct: number;
  enableDiscountExceptionApproval: boolean;
  enableLineLevelApproval: boolean;
  enablePricingControl: boolean;
  enableSaleFiscalKeepPrice: boolean;
};

export type SalesSetupResult =
  | { ok: true; summary: string[]; warnings: string[] }
  | { ok: false; error: string; warnings?: string[] };

export async function applySalesSetup(p: SalesSetupPayload): Promise<SalesSetupResult> {
  const res = await fetch('/api/cycom/setup/sales', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(p),
    credentials: 'include',
  });
  return (await res.json()) as SalesSetupResult;
}
