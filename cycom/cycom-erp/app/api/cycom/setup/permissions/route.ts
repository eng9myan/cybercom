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
  let groupId: string | null = null;

  try {
    // Warehouse-user restriction lives in the Cycom module — install if any restriction is on
    // and the user hasn't already installed it via the Warehouse wizard.
    if (p.inventoryRestricted) {
      await installModules(req, [{ name: 'warehouse_restriction_for_user' }], summary, warnings);
    }

    if (p.createCycomManagerGroup) {
      // res.groups -> the real, much simpler Role (name + description, no
      // category concept). Role has a real unique_together(tenant_id, name)
      // too, but the adapter has no server-side name filter, so check
      // client-side first the same way company/route.ts does for res.company.
      const allRoles = await cycomRpc<Array<{ id: string; name: string }>>(req, 'res.groups', 'search_read', [[], ['id', 'name']]);
      const existing = allRoles.find((r) => r.name === 'Cycom Manager');
      if (existing) {
        groupId = existing.id;
        summary.push('Role "Cycom Manager" already exists.');
      } else {
        try {
          groupId = await cycomRpc<string>(req, 'res.groups', 'create', [
            { name: 'Cycom Manager', description: 'Created by the Permissions setup wizard.' },
          ]);
          summary.push('Created role "Cycom Manager".');
        } catch (e) {
          warnings.push(`Could not create role: ${e instanceof Error ? e.message : 'unknown'}`);
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
