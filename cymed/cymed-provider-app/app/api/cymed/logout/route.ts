import { cymedLogout } from '@/lib/cymedServer';

export async function POST() {
  return cymedLogout();
}
