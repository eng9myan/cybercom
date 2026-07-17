import { NextRequest } from 'next/server';
import { cycomAskLocalMemory } from '@/lib/cycomServer';

export async function POST(req: NextRequest) {
  const { question } = (await req.json()) as { question: string };
  return cycomAskLocalMemory(req, question);
}
