import type { PaymentMix } from './pos-templates';

export type PosSetupPayload = {
  paymentMix: PaymentMix;
  dailyCashCloseout: boolean;
  enableAdvanceOrder: boolean;
  enablePledge: boolean;
  enableRefundBuyer: boolean;
  enableCashMoveAccess: boolean;
  enablePredefinedDiscounts: boolean;
  enablePosRounding: boolean;
};

export type PosSetupResult =
  | { ok: true; summary: string[]; warnings: string[] }
  | { ok: false; error: string; warnings?: string[] };

export async function applyPosSetup(p: PosSetupPayload): Promise<PosSetupResult> {
  const res = await fetch('/api/cycom/setup/pos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(p),
    credentials: 'include',
  });
  return (await res.json()) as PosSetupResult;
}
