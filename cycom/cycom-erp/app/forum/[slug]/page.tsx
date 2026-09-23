'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { Pin, Lock, Plus } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface ForumThread {
  id: string;
  title: string;
  slug: string;
  author_name: string;
  is_pinned: boolean;
  is_locked: boolean;
  reply_count: number;
  created_at: string;
}

export default function ForumIndexPage() {
  const t = useT();
  const params = useParams();
  const slug = params.slug as string;

  const [threads, setThreads] = useState<ForumThread[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/forum/${slug}/threads/`);
        if (!res.ok) throw new Error(t('forum.loadFailed'));
        const data = await res.json();
        if (!cancelled) setThreads(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t('forum.loadFailed'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [slug, t]);

  return (
    <div className="min-h-screen bg-[#030712] text-white p-4 md:p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="flex items-center justify-between border-b border-white/5 pb-4">
          <h1 className="text-lg font-black text-white">{t('forum.title')}</h1>
          <Link
            href={`/forum/${slug}/new`}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:border-white/20 text-xs font-bold"
          >
            <Plus className="w-4 h-4" /> {t('forum.newThread')}
          </Link>
        </header>

        {loading && <p className="text-slate-500 text-sm">{t('forum.loading')}</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}
        {!loading && !error && threads.length === 0 && (
          <p className="text-slate-500 text-sm italic">{t('forum.empty')}</p>
        )}

        {!loading && !error && threads.length > 0 && (
          <div className="space-y-3">
            {threads.map((th) => (
              <Link
                key={th.id}
                href={`/forum/${slug}/${th.slug}`}
                className="glass-card p-4 flex items-center justify-between gap-4 hover:border-white/20 transition-colors"
              >
                <div className="min-w-0 space-y-1">
                  <div className="flex items-center gap-2">
                    {th.is_pinned && <Pin className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                    {th.is_locked && <Lock className="w-3.5 h-3.5 text-slate-500 shrink-0" />}
                    <h3 className="text-sm font-bold text-white truncate">{th.title}</h3>
                  </div>
                  {th.author_name && (
                    <p className="text-[11px] text-slate-500">{t('blog.byAuthor', { author: th.author_name })}</p>
                  )}
                </div>
                <span className="text-xs text-slate-400 shrink-0 whitespace-nowrap">
                  {t('forum.replyCount', { count: th.reply_count })}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
