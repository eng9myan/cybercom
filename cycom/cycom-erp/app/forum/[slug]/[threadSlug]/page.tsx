'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, Pin, Lock, CheckCircle2 } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface ForumReply {
  id: string;
  body: string;
  author_name: string;
  is_accepted: boolean;
  created_at: string;
}

interface ForumThreadDetail {
  id: string;
  title: string;
  slug: string;
  body: string;
  author_name: string;
  is_pinned: boolean;
  is_locked: boolean;
  replies: ForumReply[];
  created_at: string;
}

export default function ForumThreadPage() {
  const t = useT();
  const params = useParams();
  const slug = params.slug as string;
  const threadSlug = params.threadSlug as string;

  const [thread, setThread] = useState<ForumThreadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [replyBody, setReplyBody] = useState('');
  const [replyName, setReplyName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [replyError, setReplyError] = useState<string | null>(null);

  const load = async () => {
    try {
      const res = await fetch(`/api/forum/${slug}/threads/${threadSlug}/`);
      if (!res.ok) throw new Error(t('forum.threadNotFound'));
      const data = await res.json();
      setThread(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('forum.threadNotFound'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, threadSlug]);

  const submitReply = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setReplyError(null);
    try {
      const res = await fetch(`/api/forum/${slug}/threads/${threadSlug}/replies/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body: replyBody, author_name: replyName }),
      });
      if (!res.ok) throw new Error(t('forum.replyFailed'));
      setReplyBody('');
      setReplyName('');
      await load();
    } catch (e2) {
      setReplyError(e2 instanceof Error ? e2.message : t('forum.replyFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] text-white p-4 md:p-8 font-sans">
      <div className="max-w-3xl mx-auto space-y-6">
        <Link href={`/forum/${slug}`} className="inline-flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-white">
          <ArrowLeft className="w-4 h-4" /> {t('forum.backToForum')}
        </Link>

        {loading && <p className="text-slate-500 text-sm">{t('forum.loading')}</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}

        {!loading && !error && thread && (
          <>
            <article className="glass-card p-6 space-y-3">
              <div className="flex items-center gap-2">
                {thread.is_pinned && <Pin className="w-4 h-4 text-amber-400" />}
                {thread.is_locked && <Lock className="w-4 h-4 text-slate-500" />}
                <h1 className="text-xl font-black text-white">{thread.title}</h1>
              </div>
              {thread.author_name && (
                <p className="text-xs text-slate-500">{t('blog.byAuthor', { author: thread.author_name })}</p>
              )}
              <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{thread.body}</p>
            </article>

            <section className="space-y-3">
              <h2 className="text-xs font-black text-slate-400 uppercase tracking-wide">{t('forum.replies')}</h2>
              {thread.replies.length === 0 && (
                <p className="text-slate-500 text-sm italic">{t('forum.noReplies')}</p>
              )}
              {thread.replies.map((r) => (
                <div key={r.id} className="glass-card p-4 space-y-2">
                  {r.is_accepted && (
                    <div className="flex items-center gap-1.5 text-emerald-400 text-[11px] font-bold">
                      <CheckCircle2 className="w-3.5 h-3.5" /> {t('forum.accepted')}
                    </div>
                  )}
                  <p className="text-sm text-slate-300 whitespace-pre-wrap">{r.body}</p>
                  {r.author_name && (
                    <p className="text-[11px] text-slate-500">{t('blog.byAuthor', { author: r.author_name })}</p>
                  )}
                </div>
              ))}
            </section>

            {thread.is_locked ? (
              <p className="text-slate-500 text-xs italic">{t('forum.threadLockedNotice')}</p>
            ) : (
              <form onSubmit={submitReply} className="glass-card p-4 space-y-3">
                <textarea
                  value={replyBody}
                  onChange={(e) => setReplyBody(e.target.value)}
                  placeholder={t('forum.replyBodyPlaceholder')}
                  rows={3}
                  required
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30 resize-none"
                />
                <input
                  value={replyName}
                  onChange={(e) => setReplyName(e.target.value)}
                  placeholder={t('forum.namePlaceholder')}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
                />
                {replyError && <p className="text-red-400 text-xs">{replyError}</p>}
                <button type="submit" disabled={submitting} className="btn-primary py-1.5 px-4 text-xs disabled:opacity-50">
                  {submitting ? t('forum.postingReply') : t('forum.postReply')}
                </button>
              </form>
            )}
          </>
        )}
      </div>
    </div>
  );
}
