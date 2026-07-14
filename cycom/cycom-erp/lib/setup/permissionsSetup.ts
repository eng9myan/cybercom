import type { RoleTemplate } from './permissions-templates';

export type PermissionsSetupPayload = {
  roleTemplate: RoleTemplate;
  financeRestricted: boolean;
  payrollRestricted: boolean;
  inventoryRestricted: boolean;
  posRestricted: boolean;
  createCycomManagerGroup: boolean;
};

export type PermissionsSetupResult =
  | { ok: true; summary: string[]; warnings: string[]; groupId: number | null }
  | { ok: false; error: string; warnings?: string[] };

export async function applyPermissionsSetup(p: PermissionsSetupPayload): Promise<PermissionsSetupResult> {
  const res = await fetch('/api/cycom/setup/permissions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(p),
    credentials: 'include',
  });
  return (await res.json()) as PermissionsSetupResult;
}
