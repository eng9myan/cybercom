import { NextRequest } from 'next/server';
import { cymedGetSession } from '@/lib/cymedServer';

export async function POST(req: NextRequest) {
  return cymedGetSession(req);
}
