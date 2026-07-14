import { NextRequest, NextResponse } from 'next/server';
import { installModules, setParam } from '@/lib/setup/serverHelpers';

type Payload = {
  frequency: 'monthly' | 'bi_weekly' | 'weekly';
  weeklyHours: number;
  otMultiplier: number;
  latenessGraceMinutes: number;
  enableCycomOvertime: boolean;
  enableMassReconciliation: boolean;
};

export async function POST(req: NextRequest) {
  let p: Payload;
  try {
    p = (await req.json()) as Payload;
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON payload' }, { status: 400 });
  }

  const summary: string[] = [];
  const warnings: string[] = [];

  try {
    await installModules(
      req,
      [
        { name: 'hr_payroll', required: true },
        ...(p.enableCycomOvertime ? [{ name: 'cycom_payroll_overtime' }] : []),
        ...(p.enableCycomOvertime ? [{ name: 'extra_hours_enhancement' }] : []),
        ...(p.enableMassReconciliation ? [{ name: 'mass_reconciliation' }] : []),
        ...(p.enableMassReconciliation ? [{ name: 'latness_deduction' }] : []),
      ],
      summary,
      warnings,
    );

    await setParam(req, 'cycom.payroll.frequency', p.frequency);
    await setParam(req, 'cycom.payroll.weekly_hours', String(p.weeklyHours));
    await setParam(req, 'cycom.payroll.ot_multiplier', String(p.otMultiplier));
    await setParam(req, 'cycom.payroll.lateness_grace_minutes', String(p.latenessGraceMinutes));
    await setParam(req, 'cycom.tenant.setup.payroll_done', 'true');
    summary.push(`Saved payroll defaults: ${p.frequency}, ${p.weeklyHours} h/week, OT ×${p.otMultiplier}, ${p.latenessGraceMinutes} min grace.`);

    return NextResponse.json({ ok: true, summary, warnings });
  } catch (e) {
    return NextResponse.json(
      { ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings },
      { status: 500 },
    );
  }
}
