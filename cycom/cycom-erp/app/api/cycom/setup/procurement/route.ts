import { NextRequest, NextResponse } from 'next/server';
import { installModules, setParam } from '@/lib/setup/serverHelpers';

type Payload = {
  approvalPolicy: 'auto' | 'single' | 'dual';
  approvalThresholdAmount: number;
  rfqValidityDays: number;
  defaultLeadTimeDays: number;
  enableAltanmyaExtension: boolean;
  enableApprovalContact: boolean;
};

export async function POST(req: NextRequest) {
  let p: Payload;
  try { p = (await req.json()) as Payload; } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 }); }

  const summary: string[] = [];
  const warnings: string[] = [];

  try {
    await installModules(req, [
      { name: 'purchase', required: true },
      ...(p.enableAltanmyaExtension ? [{ name: 'ALTANMYA_Purchase_Extension' }] : []),
      ...(p.enableApprovalContact ? [{ name: 'approval_contact' }] : []),
    ], summary, warnings);

    await setParam(req, 'cycom.procurement.approval_policy', p.approvalPolicy);
    await setParam(req, 'cycom.procurement.approval_threshold_amount', String(p.approvalThresholdAmount));
    await setParam(req, 'cycom.procurement.rfq_validity_days', String(p.rfqValidityDays));
    await setParam(req, 'cycom.procurement.default_lead_time_days', String(p.defaultLeadTimeDays));
    await setParam(req, 'cycom.tenant.setup.procurement_done', 'true');
    summary.push(`Saved procurement policy: ${p.approvalPolicy} approval over ${p.approvalThresholdAmount}, RFQ valid ${p.rfqValidityDays}d, lead time ${p.defaultLeadTimeDays}d.`);

    return NextResponse.json({ ok: true, summary, warnings });
  } catch (e) {
    return NextResponse.json({ ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings }, { status: 500 });
  }
}
