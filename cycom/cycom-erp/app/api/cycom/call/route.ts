import { NextRequest } from 'next/server';
import { cycomCallKw } from '@/lib/cycomServer';

export async function POST(req: NextRequest) {
  const body = (await req.json()) as { model: string; method: string; args?: unknown[]; kwargs?: Record<string, unknown> };
  return cycomCallKw(req, body);
}
