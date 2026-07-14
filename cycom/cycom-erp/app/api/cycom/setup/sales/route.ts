import { NextRequest, NextResponse } from 'next/server';
import { installModules, setParam } from '@/lib/setup/serverHelpers';

type Payload = {
  motion: 'b2c' | 'b2b' | 'mixed';
  freeDiscountLimitPct: number;
  managerDiscountLimitPct: number;
  dualApprovalThresholdPct: number;
  enableDiscountExceptionApproval: boolean;
  enableLineLevelApproval: boolean;
  enablePricingControl: boolean;
  enableSaleFiscalKeepPrice: boolean;
};

export async function POST(req: NextRequest) {
  let p: Payload;
  try { p = (await req.json()) as Payload; } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 }); }

  const summary: string[] = [];
  const warnings: string[] = [];

  try {
    await installModules(req, [
      { name: 'sale_management', required: true },
      ...(p.enableDiscountExceptionApproval ? [{ name: 'sale_discount_exception_approval' }] : []),
      ...(p.enableLineLevelApproval ? [{ name: 'ag_sale_line_approval' }] : []),
      ...(p.enablePricingControl ? [{ name: 'cycom_sale_pricing_control' }] : []),
      ...(p.enableSaleFiscalKeepPrice ? [{ name: 'sale_fiscal_position_keep_price' }] : []),
    ], summary, warnings);

    await setParam(req, 'cycom.sales.motion', p.motion);
    await setParam(req, 'cycom.sales.free_discount_limit_pct', String(p.freeDiscountLimitPct));
    await setParam(req, 'cycom.sales.manager_discount_limit_pct', String(p.managerDiscountLimitPct));
    await setParam(req, 'cycom.sales.dual_approval_threshold_pct', String(p.dualApprovalThresholdPct));
    await setParam(req, 'cycom.tenant.setup.sales_done', 'true');
    summary.push(`Saved sales policy: motion=${p.motion}, free discount ≤${p.freeDiscountLimitPct}%, manager ≤${p.managerDiscountLimitPct}%, dual approval >${p.dualApprovalThresholdPct}%.`);

    return NextResponse.json({ ok: true, summary, warnings });
  } catch (e) {
    return NextResponse.json({ ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings }, { status: 500 });
  }
}
