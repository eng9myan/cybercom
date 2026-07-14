import { NextRequest, NextResponse } from 'next/server';

const CYCOM_BACKEND_URL = process.env.CYCOM_BACKEND_URL || 'http://localhost:8000';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const upstream = await fetch(`${CYCOM_BACKEND_URL}/api/setup/bootstrap`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err: any) {
    return NextResponse.json({ error: err.message || 'Connection failure' }, { status: 500 });
  }
}
