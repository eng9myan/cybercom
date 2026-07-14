import type { ManufacturingType } from './manufacturing-templates';

export type ManufacturingSetupPayload = {
  mfgType: ManufacturingType;
  enableMrp: boolean;
  enableWorkorders: boolean;
  enableMaintenance: boolean;
  enableQuality: boolean;
  enablePlm: boolean;
};

export type ManufacturingSetupResult =
  | { ok: true; summary: string[]; warnings: string[] }
  | { ok: false; error: string; warnings?: string[] };

export async function applyManufacturingSetup(p: ManufacturingSetupPayload): Promise<ManufacturingSetupResult> {
  const res = await fetch('/api/cycom/setup/manufacturing', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(p),
    credentials: 'include',
  });
  return (await res.json()) as ManufacturingSetupResult;
}
