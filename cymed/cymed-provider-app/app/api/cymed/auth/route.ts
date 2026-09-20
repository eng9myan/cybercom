import { NextRequest } from 'next/server';
import { cymedAuthenticate } from '@/lib/cymedServer';

export async function POST(req: NextRequest) {
  const { login, password } = (await req.json()) as { login: string; password: string };
  const { res } = await cymedAuthenticate(login, password);
  return res;
}
