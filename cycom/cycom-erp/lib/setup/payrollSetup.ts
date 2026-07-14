import type { PayFrequency } from './payroll-templates';

export type PayrollSetupPayload = {
  frequency: PayFrequency;
  weeklyHours: number;
  otMultiplier: number;
  latenessGraceMinutes: number;
  enableCycomOvertime: boolean;
  enableMassReconciliation: boolean;
};

export type PayrollSetupResult =
  | { ok: true; summary: string[]; warnings: string[] }
  | { ok: false; error: string; warnings?: string[] };

export async function applyPayrollSetup(p: PayrollSetupPayload): Promise<PayrollSetupResult> {
  const res = await fetch('/api/cycom/setup/payroll', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(p),
    credentials: 'include',
  });
  return (await res.json()) as PayrollSetupResult;
}
