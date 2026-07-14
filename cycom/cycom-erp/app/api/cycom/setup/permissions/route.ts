import { NextRequest, NextResponse } from 'next/server';
import { installModules, cycomRpc, setParam } from '@/lib/setup/serverHelpers';

type Payload = {
  roleTemplate: 'strict' | 'standard' | 'open';
  financeRestricted: boolean;
  payrollRestricted: boolean;
  inventoryRestricted: boolean;
  posRestricted: boolean;
  createCycomManagerGroup: boolean;
};

export async function POST(req: NextRequest) {
  let p: Payload;
  try { p = (await req.json()) as Payload; } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 }); }

  const summary: string[] = [];
  const warnings: string[] = [];
  let groupId: number | null = null;

  try {
    // Warehouse-user restriction lives in the Cycom module — install if any restriction is on
    // and the user hasn't already installed it via the Warehouse wizard.
    if (p.inventoryRestricted) {
      await installModules(req, [{ name: 'warehouse_restriction_for_user' }], summary, warnings);
    }

    if (p.createCycomManagerGroup) {
      // Idempotent: only create if one with the same name doesn't exist.
      const existing = await cycomRpc<Array<{ id: number }>>(
        req, 'res.groups', 'search_read',
        [[['name', '=', 'Cycom Manager']], ['id']], { limit: 1 },
      );
      if (existing.length) {
        groupId = existing[0].id;
        summary.push('Group "Cycom Manager" already exists.');
      } else {
        // Try to find a sensible category (Administration) — fallback to null
        const cat = await cycomRpc<Array<{ id: number }>>(
          req, 'ir.module.category', 'search_read',
          [[['name', '=', 'Administration']], ['id']], { limit: 1 },
        );
        try {
          const vals: Record<string, unknown> = { name: 'Cycom Manager' };
          if (cat.length) vals.category_id = cat[0].id;
          groupId = await cycomRpc<number>(req, 'res.groups', 'create', [vals]);
          summary.push('Created group "Cycom Manager".');
        } catch (e) {
          warnings.push(`Could not create group: ${e instanceof Error ? e.message : 'unknown'}`);
        }
      }
    }

    await setParam(req, 'cycom.permissions.role_template', p.roleTemplate);
    await setParam(req, 'cycom.permissions.finance_restricted', p.financeRestricted ? 'true' : 'false');
    await setParam(req, 'cycom.permissions.payroll_restricted', p.payrollRestricted ? 'true' : 'false');
    await setParam(req, 'cycom.permissions.inventory_restricted', p.inventoryRestricted ? 'true' : 'false');
    await setParam(req, 'cycom.permissions.pos_restricted', p.posRestricted ? 'true' : 'false');
    await setParam(req, 'cycom.tenant.setup.permissions_done', 'true');
    summary.push(`Saved permission policy: ${p.roleTemplate} template, finance ${p.financeRestricted ? 'restricted' : 'open'}, payroll ${p.payrollRestricted ? 'restricted' : 'open'}.`);

    return NextResponse.json({ ok: true, summary, warnings, groupId });
  } catch (e) {
    return NextResponse.json({ ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings }, { status: 500 });
  }
}
