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

    // Confirm at least one warehouse exists for the tenant. Real Warehouse
    // (products.cycom.inventory) has no per-company dimension at all --
    // unlike Odoo's stock.warehouse, there's nothing to loop "per company"
    // over, so this just ensures a single tenant-wide default exists.
    const existing = await cycomRpc<Array<{ id: number }>>(req, 'stock.warehouse', 'search_read', [[], ['id']], { limit: 1 });
    if (!existing.length) {
      try {
        await cycomRpc<number>(req, 'stock.warehouse', 'create', [{ name: 'Main Warehouse', code: 'WH-MAIN' }]);
        summary.push('Created default warehouse "Main Warehouse".');
      } catch (e) {
        warnings.push(`Could not create default warehouse: ${e instanceof Error ? e.message : 'unknown'}`);
      }
    } else {
      summary.push('A warehouse already exists for this tenant.');
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
