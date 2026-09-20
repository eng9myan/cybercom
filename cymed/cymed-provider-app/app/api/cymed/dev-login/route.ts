import { cymedDevLogin } from '@/lib/cymedServer';

// DEV-ONLY: GET /api/cymed/dev-login sets a fake session cookie for the
// fixed dev provider identity and redirects home. Enabled only when
// CYMED_DEV_AUTH=1. See core/dev_auth.py.
export async function GET() {
  return cymedDevLogin();
}
