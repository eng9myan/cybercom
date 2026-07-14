import { NextRequest } from 'next/server';
import { cycomLogout } from '@/lib/cycomServer';

export async function POST(req: NextRequest) {
  return cycomLogout(req);
}
