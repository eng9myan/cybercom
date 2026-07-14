import { NextRequest, NextResponse } from 'next/server';
import { installModules, setParam } from '@/lib/setup/serverHelpers';

type Payload = {
  mfgType: 'none' | 'discrete' | 'process' | 'food' | 'pharma';
  enableMrp: boolean;
  enableWorkorders: boolean;
  enableMaintenance: boolean;
  enableQuality: boolean;
  enablePlm: boolean;
};

export async function POST(req: NextRequest) {
  let p: Payload;
  try { p = (await req.json()) as Payload; } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 }); }

  const summary: string[] = [];
  const warnings: string[] = [];

  try {
    if (p.mfgType === 'none' && !p.enableMrp) {
      summary.push('Manufacturing skipped — no modules installed.');
    } else {
      await installModules(req, [
        ...(p.enableMrp ? [{ name: 'mrp' }] : []),
        ...(p.enableWorkorders ? [{ name: 'mrp_workorder' }] : []),
        ...(p.enableMaintenance ? [{ name: 'maintenance' }] : []),
        ...(p.enableQuality ? [{ name: 'quality_control' }, { name: 'quality_mrp' }] : []),
        ...(p.enablePlm ? [{ name: 'mrp_plm' }] : []),
      ], summary, warnings);
    }

    await setParam(req, 'cycom.manufacturing.type', p.mfgType);
    await setParam(req, 'cycom.tenant.setup.manufacturing_done', 'true');
    summary.push(`Saved manufacturing type: ${p.mfgType}.`);

    return NextResponse.json({ ok: true, summary, warnings });
  } catch (e) {
    return NextResponse.json({ ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings }, { status: 500 });
  }
}
