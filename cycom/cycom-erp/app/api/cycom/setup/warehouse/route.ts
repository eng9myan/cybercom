import { NextRequest, NextResponse } from 'next/server';
import { installModules, cycomRpc, setParam } from '@/lib/setup/serverHelpers';

type Payload = {
  costingMethod: 'standard' | 'fifo' | 'average';
  negativeStockGuard: boolean;
  lowStockThreshold: number;
  enableWarehouseRestriction: boolean;
  enableDiscrepancyWorkflow: boolean;
};

export async function POST(req: NextRequest) {
  let p: Payload;
  try { p = (await req.json()) as Payload; } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 }); }

  const summary: string[] = [];
  const warnings: string[] = [];

  try {
    await installModules(req, [
      { name: 'stock', required: true },
      ...(p.negativeStockGuard ? [{ name: 'stock_qty_guard' }] : []),
      ...(p.negativeStockGuard ? [{ name: 'stock_location_negative_block' }] : []),
      ...(p.enableWarehouseRestriction ? [{ name: 'warehouse_restriction_for_user' }] : []),
      ...(p.enableDiscrepancyWorkflow ? [{ name: 'stock_transfer_discrepancy_new' }] : []),
    ], summary, warnings);

    // Confirm a warehouse exists per company (stock auto-creates one on install).
    const companies = await cycomRpc<Array<{ id: number; name: string }>>(
      req, 'res.company', 'search_read', [[], ['id', 'name']], { limit: 50 },
    );
    for (const c of companies) {
      const wh = await cycomRpc<Array<{ id: number }>>(
        req, 'stock.warehouse', 'search_read',
        [[['company_id', '=', c.id]], ['id']], { limit: 1 },
      );
      if (!wh.length) {
        try {
          await cycomRpc<number>(req, 'stock.warehouse', 'create', [{
            name: c.name, code: `WH${c.id}`, company_id: c.id,
          }]);
          summary.push(`Created warehouse for "${c.name}".`);
        } catch (e) {
          warnings.push(`Could not create warehouse for "${c.name}": ${e instanceof Error ? e.message : 'unknown'}`);
        }
      }
    }

    await setParam(req, 'cycom.warehouse.costing_method', p.costingMethod);
    await setParam(req, 'cycom.warehouse.negative_stock_guard', p.negativeStockGuard ? 'true' : 'false');
    await setParam(req, 'cycom.warehouse.low_stock_threshold', String(p.lowStockThreshold));
    await setParam(req, 'cycom.tenant.setup.warehouse_done', 'true');
    summary.push(`Saved warehouse policy: ${p.costingMethod} costing, low-stock threshold ${p.lowStockThreshold}, negative-stock ${p.negativeStockGuard ? 'blocked' : 'allowed'}.`);

    return NextResponse.json({ ok: true, summary, warnings });
  } catch (e) {
    return NextResponse.json({ ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings }, { status: 500 });
  }
}
