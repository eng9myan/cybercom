import { NextRequest, NextResponse } from 'next/server';

const CYCOM_BACKEND_URL = process.env.CYCOM_BACKEND_URL || 'http://localhost:8000';

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ action: string; id: string }> | { action: string; id: string } }
) {
  try {
    // Await params since Next.js 16/App Router treats them as dynamic promises
    const resolvedParams = await (params as any);
    const { action, id } = resolvedParams;

    if (!['approve', 'reject'].includes(action)) {
      return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
    }

    const upstream = await fetch(`${CYCOM_BACKEND_URL}/api/hitl/${action}/${id}`, {
      method: 'POST',
    });

    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err: any) {
    return NextResponse.json({ error: err.message || 'Action proxy execution failed' }, { status: 500 });
  }
}
