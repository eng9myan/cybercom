'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { useT } from '@/lib/i18n';

export default function NewThreadPage() {
  const t = useT();
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;

  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [authorName, setAuthorName] = useState('');
  const [authorEmail, setAuthorEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/forum/${slug}/threads/create/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, body, author_name: authorName, author_email: authorEmail }),
      });
      if (!res.ok) throw new Error(t('forum.submitFailed'));
      const data = await res.json();
      router.push(`/forum/${slug}/${data.slug}`);
    } catch (e2) {
      setError(e2 instanceof Error ? e2.message : t('forum.submitFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] text-white p-4 md:p-8 font-sans">
      <div className="max-w-xl mx-auto space-y-6">
        <Link href={`/forum/${slug}`} className="inline-flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-white">
          <ArrowLeft className="w-4 h-4" /> {t('forum.backToForum')}
        </Link>

        <form onSubmit={submit} className="glass-card p-6 space-y-4">
          <h1 className="text-lg font-black text-white">{t('forum.newThread')}</h1>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-400">{t('forum.threadTitleLabel')}</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t('forum.threadTitlePlaceholder')}
              required
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-400">{t('forum.bodyLabel')}</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder={t('forum.bodyPlaceholder')}
              rows={5}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400">{t('forum.nameLabel')}</label>
              <input
                value={authorName}
                onChange={(e) => setAuthorName(e.target.value)}
                placeholder={t('forum.namePlaceholder')}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400">{t('forum.emailLabel')}</label>
              <input
                type="email"
                value={authorEmail}
                onChange={(e) => setAuthorEmail(e.target.value)}
                placeholder={t('forum.emailPlaceholder')}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
              />
            </div>
          </div>

          {error && <p className="text-red-400 text-xs">{error}</p>}

          <button type="submit" disabled={submitting} className="btn-primary w-full py-2 text-sm disabled:opacity-50">
            {submitting ? t('forum.submitting') : t('forum.submit')}
          </button>
        </form>
      </div>
    </div>
  );
}
