import { NextRequest, NextResponse } from 'next/server';
import { installModules, cycomRpc, setParam } from '@/lib/setup/serverHelpers';

type Payload = {
  orgSize: 'small' | 'medium' | 'large';
  departments: string[];
  enableBiometricZk: boolean;
  enableSingleDeviceBinding: boolean;
  enableGeofence: boolean;
  enableHealthInsurance: boolean;
  enableEmployeeCode: boolean;
  enableEmployeeSpouse: boolean;
  enableAutoPortal: boolean;
  enableDocumentExpiry: boolean;
  enableEmployeeRequest: boolean;
};

export async function POST(req: NextRequest) {
  let p: Payload;
  try { p = (await req.json()) as Payload; } catch { return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 }); }

  const summary: string[] = [];
  const warnings: string[] = [];

  try {
    await installModules(req, [
      { name: 'hr', required: true },
      { name: 'hr_attendance' },
      ...(p.enableBiometricZk ? [
        { name: 'hs_zk_attendance' },
        { name: 'hs_zk_attendance_bridge' },
        { name: 'cycom_biometric_attendance' },
        { name: 'sttl_face_attendance' },
        { name: 'hr_attendance_overtime_approval_bridge' },
        { name: 'hr_attendance_schedule_normalization' },
        { name: 'hr_attendance_weekly_overtime_eligibility' },
      ] : []),
      ...(p.enableSingleDeviceBinding ? [{ name: 'cycom_mobile_single_device' }] : []),
      ...(p.enableGeofence ? [{ name: 'hr_attendance_geofence_config' }] : []),
      ...(p.enableHealthInsurance ? [{ name: 'hr_health_insurance' }] : []),
      ...(p.enableEmployeeCode ? [{ name: 'hr_employee_code' }] : []),
      ...(p.enableEmployeeSpouse ? [{ name: 'hr_employee_spouse' }] : []),
      ...(p.enableAutoPortal ? [{ name: 'hr_employee_auto_portal' }] : []),
      ...(p.enableDocumentExpiry ? [{ name: 'employee_document_expiry' }] : []),
      ...(p.enableEmployeeRequest ? [{ name: 'employee_request' }] : []),
      { name: 'hr_enhancement' },
      { name: 'hr_enhancement_plan' },
      { name: 'hr_leave_fallback' },
      { name: 'cycom_employee_profile' },
    ], summary, warnings);

    // Create the chosen departments as real top-level units (idempotent:
    // re-running the wizard doesn't duplicate an existing name).
    const departmentNames = [...new Set(p.departments.map((d) => d.trim()).filter(Boolean))];
    const existing = await cycomRpc<Array<{ id: string; name: string; parent_id: unknown }>>(
      req, 'hr.department', 'search_read', [[], ['id', 'name', 'parent_id']]);
    const topLevel = new Set(existing.filter((d) => !d.parent_id).map((d) => d.name));
    let created = 0;
    for (const name of departmentNames) {
      if (topLevel.has(name)) continue;
      await cycomRpc<string>(req, 'hr.department', 'create', [{ name }]);
      created += 1;
    }

    await setParam(req, 'cycom.hr.org_size', p.orgSize);
    await setParam(req, 'cycom.tenant.setup.hr_done', 'true');
    summary.push(`Saved HR org size: ${p.orgSize}. Created ${created} department(s) (${departmentNames.length - created} already existed).`);

    return NextResponse.json({ ok: true, summary, warnings, departmentNames });
  } catch (e) {
    return NextResponse.json({ ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings }, { status: 500 });
  }
}
