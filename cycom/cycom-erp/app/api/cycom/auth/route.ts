import { NextRequest } from 'next/server';
import { cycomAuthenticate } from '@/lib/cycomServer';

export async function POST(req: NextRequest) {
  const { login, password } = (await req.json()) as { login: string; password: string };
  const { res } = await cycomAuthenticate(login, password);
  return res;
}
