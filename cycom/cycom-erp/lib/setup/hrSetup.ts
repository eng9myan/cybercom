import type { OrgSize } from './hr-templates';

export type HrSetupPayload = {
  orgSize: OrgSize;
  departments: string[];
  enableBiometricZk: boolean;
  enableSingleDeviceBinding: boolean;
  enableGeofence: boolean;
  enableHealthInsurance: boolean;
  enableEmployeeCode: boolean;
  enableEmployeeSpouse: boolean;
  enableAutoPortal: boolean;
  enableDocumentExpiry: boolean;
  enableEmployeeRequest: boolean;
};

export type HrSetupResult =
  | { ok: true; summary: string[]; warnings: string[]; departmentIds: number[] }
  | { ok: false; error: string; warnings?: string[] };

export async function applyHrSetup(p: HrSetupPayload): Promise<HrSetupResult> {
  const res = await fetch('/api/cycom/setup/hr', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(p),
    credentials: 'include',
  });
  return (await res.json()) as HrSetupResult;
}
