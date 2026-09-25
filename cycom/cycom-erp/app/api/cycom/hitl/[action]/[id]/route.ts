import { NextRequest, NextResponse } from 'next/server';
import { cycomBackendProxy } from '@/lib/cycomServer';

const ALLOWED_ACTIONS = new Set(['approve', 'reject']);

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ action: string; id: string }> }
) {
  const { action, id } = await params;
  if (!ALLOWED_ACTIONS.has(action)) {
    return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
  }
  return cycomBackendProxy(req, `/api/hitl/${action}/${id}/`);
}
