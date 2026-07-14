import { NextRequest } from 'next/server';
import { cycomAuthenticate } from '@/lib/cycomServer';

export async function POST(req: NextRequest) {
  const { db, login, password } = (await req.json()) as { db?: string; login: string; password: string };
  const { res } = await cycomAuthenticate(login, password, db);
  return res;
}
