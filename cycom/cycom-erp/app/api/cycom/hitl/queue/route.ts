import { NextRequest } from 'next/server';
import { cycomBackendProxy } from '@/lib/cycomServer';

// Authenticated proxy -- the HITL queue is per-user (which items the caller
// is entitled to approve), so it needs the same session -> Bearer token
// forwarding every other internal page uses, not a bare unauthenticated
// fetch (which also silently 401s in real auth once dev mode's default
// grant isn't there to paper over it).
export async function GET(req: NextRequest) {
  return cycomBackendProxy(req, '/api/hitl/queue/');
}
