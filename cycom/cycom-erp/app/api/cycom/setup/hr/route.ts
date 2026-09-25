import { NextRequest, NextResponse } from 'next/server';
import { installModules, setParam } from '@/lib/setup/serverHelpers';

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

    // Real Employee.department (products.cycom.hr) is a plain free-text
    // field, not a separate entity with its own id/hierarchy/manager (that
    // richer concept -- what app/hr/departments/page.tsx's tree view
    // actually wants -- doesn't exist in the backend yet; a real one is a
    // separate feature, not onboarding plumbing). Nothing needs pre-
    // creating: an employee just gets typed into a department directly.
    // Persist the chosen names as a preference so the employee-creation
    // UI can offer them as suggestions.
    const departmentNames = [...new Set(p.departments.map((d) => d.trim()).filter(Boolean))];
    await setParam(req, 'cycom.hr.department_names', JSON.stringify(departmentNames));

    await setParam(req, 'cycom.hr.org_size', p.orgSize);
    await setParam(req, 'cycom.tenant.setup.hr_done', 'true');
    summary.push(`Saved HR org size: ${p.orgSize}. Saved ${departmentNames.length} department name(s) as a preference.`);

    return NextResponse.json({ ok: true, summary, warnings, departmentNames });
  } catch (e) {
    return NextResponse.json({ ok: false, error: e instanceof Error ? e.message : 'Setup failed', warnings }, { status: 500 });
  }
}
