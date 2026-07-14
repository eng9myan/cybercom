import { NextRequest, NextResponse } from 'next/server';
import { installModules, cycomRpc, setParam } from '@/lib/setup/serverHelpers';

type Payload = {
  paymentMix: 'cash_heavy' | 'card_heavy' | 'split';
  dailyCashCloseout: boolean;
  enableAdvanceOrder: boolean;
  enablePledge: boolean;
  enableRefundBuyer: boolean;
  enableCashMoveAccess: boolean;
  enablePredefinedDiscounts: boolean;
  enablePosRounding: boolean;
};

export async function POST(req: NextRequest) {
  let p: Payload;
  try { p = (await req.json()) as Payload; } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 }); }

  const summary: string[] = [];
  const warnings: string[] = [];

  try {
    await installModules(req, [
      { name: 'point_of_sale', required: true },
      ...(p.enableAdvanceOrder ? [{ name: 'pos_advance_order' }] : []),
      ...(p.enablePledge ? [{ name: 'pos_pledge' }, { name: 'pos_pledge_order' }] : []),
      ...(p.enableRefundBuyer ? [{ name: 'cycom_jo_pos_refund_buyer' }] : []),
      ...(p.enableCashMoveAccess ? [{ name: 'cycom_pos_cash_move_access' }] : []),
      ...(p.enablePredefinedDiscounts ? [{ name: 'pos_predefined_discounts' }] : []),
      ...(p.enablePosRounding ? [{ name: 'pos_rounding' }] : []),
      ...(p.dailyCashCloseout ? [{ name: 'pos_opening_cash_zero' }] : []),
    ], summary, warnings);

    // Ensure one pos.config per company.
    const companies = await cycomRpc<Array<{ id: number; name: string }>>(
      req, 'res.company', 'search_read', [[], ['id', 'name']], { limit: 50 },
    );
    for (const c of companies) {
      const cfg = await cycomRpc<Array<{ id: number }>>(
        req, 'pos.config', 'search_read',
        [[['company_id', '=', c.id]], ['id']], { limit: 1 },
      );
      if (!cfg.length) {
        try {
          await cycomRpc<number>(req, 'pos.config', 'create', [{
            name: `${c.name} — Main Terminal`, company_id: c.id,
          }]);
          summary.push(`Created POS terminal for "${c.name}".`);
        } catch (e) {
          warnings.push(`Could not create POS terminal for "${c.name}": ${e instanceof Error ? e.message : 'unknown'}`);
        }
      }
    }

    await setParam(req, 'cycom.pos.payment_mix', p.paymentMix);
    await setParam(req, 'cycom.pos.daily_cash_closeout', p.dailyCashCloseout ? 'true' : 'false');
    await setParam(req, 'cycom.tenant.setup.pos_done', 'true');
    summary.push(`Saved POS policy: ${p.paymentMix}, daily closeout ${p.dailyCashCloseout ? 'on' : 'off'}.`);

    return NextResponse.json({ ok: true, summary, warnings });
  } catch (e) {
    return NextResponse.json({ ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings }, { status: 500 });
  }
}
