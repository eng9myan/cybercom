import { NextRequest } from 'next/server';
import { cycomGetSession } from '@/lib/cycomServer';

export async function POST(req: NextRequest) {
  return cycomGetSession(req);
}
