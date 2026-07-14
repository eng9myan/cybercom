import type { CostingMethod } from './warehouse-templates';

export type WarehouseSetupPayload = {
  costingMethod: CostingMethod;
  negativeStockGuard: boolean;
  lowStockThreshold: number;
  enableWarehouseRestriction: boolean;
  enableDiscrepancyWorkflow: boolean;
};

export type WarehouseSetupResult =
  | { ok: true; summary: string[]; warnings: string[] }
  | { ok: false; error: string; warnings?: string[] };

export async function applyWarehouseSetup(p: WarehouseSetupPayload): Promise<WarehouseSetupResult> {
  const res = await fetch('/api/cycom/setup/warehouse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(p),
    credentials: 'include',
  });
  return (await res.json()) as WarehouseSetupResult;
}
