import { NextRequest, NextResponse } from 'next/server';

const CYCOM_BACKEND_URL = process.env.CYCOM_BACKEND_URL || 'http://localhost:8000';

export async function GET(req: NextRequest) {
  try {
    const upstream = await fetch(`${CYCOM_BACKEND_URL}/api/hitl/queue`, {
      cache: 'no-store',
    });
    const data = await upstream.json();
    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json({ error: err.message || 'Failed to fetch queue' }, { status: 500 });
  }
}
