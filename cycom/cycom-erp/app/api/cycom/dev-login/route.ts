import { NextRequest } from 'next/server';
import { cycomDevLogin } from '@/lib/cycomServer';

// DEV-ONLY: GET /api/cycom/dev-login?role=<role>&name=<name> sets a fake
// session cookie for that functional role and redirects home. Enabled only
// when CYCOM_DEV_AUTH=1. See core/dev_auth.py.
export async function GET(req: NextRequest) {
  const role = req.nextUrl.searchParams.get('role') || 'gm';
  const name = req.nextUrl.searchParams.get('name') || '';
  return cycomDevLogin(role, name);
}
