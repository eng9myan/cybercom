import type { ApprovalPolicy } from './procurement-templates';

export type ProcurementSetupPayload = {
  approvalPolicy: ApprovalPolicy;
  approvalThresholdAmount: number;
  rfqValidityDays: number;
  defaultLeadTimeDays: number;
  enableAltanmyaExtension: boolean;
  enableApprovalContact: boolean;
};

export type ProcurementSetupResult =
  | { ok: true; summary: string[]; warnings: string[] }
  | { ok: false; error: string; warnings?: string[] };

export async function applyProcurementSetup(p: ProcurementSetupPayload): Promise<ProcurementSetupResult> {
  const res = await fetch('/api/cycom/setup/procurement', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(p),
    credentials: 'include',
  });
  return (await res.json()) as ProcurementSetupResult;
}
