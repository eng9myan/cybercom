'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useT } from '@/lib/i18n';

interface BlogPost {
  id: string;
  title: string;
  slug: string;
  excerpt: string;
  cover_image_url: string | null;
  author_name: string;
  published_at: string;
}

export default function BlogIndexPage() {
  const t = useT();
  const params = useParams();
  const slug = params.slug as string;

  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/blog/${slug}/posts/`);
        if (!res.ok) throw new Error(t('blog.loadFailed'));
        const data = await res.json();
        if (!cancelled) setPosts(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t('blog.loadFailed'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [slug, t]);

  return (
    <div className="min-h-screen bg-[#030712] text-white p-4 md:p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="border-b border-white/5 pb-4">
          <h1 className="text-lg font-black text-white">{t('blog.title')}</h1>
        </header>

        {loading && <p className="text-slate-500 text-sm">{t('blog.loading')}</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}
        {!loading && !error && posts.length === 0 && (
          <p className="text-slate-500 text-sm italic">{t('blog.empty')}</p>
        )}

        {!loading && !error && posts.length > 0 && (
          <div className="space-y-5">
            {posts.map((p) => (
              <Link
                key={p.id}
                href={`/blog/${slug}/${p.slug}`}
                className="glass-card p-5 flex gap-4 hover:border-white/20 transition-colors"
              >
                {p.cover_image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={p.cover_image_url} alt={p.title} className="w-28 h-28 object-cover rounded-xl shrink-0" />
                ) : (
                  <div className="w-28 h-28 rounded-xl bg-white/5 flex items-center justify-center text-slate-600 text-xs shrink-0">
                    {t('blog.noImage')}
                  </div>
                )}
                <div className="flex-1 space-y-1">
                  <h3 className="text-sm font-bold text-white">{p.title}</h3>
                  {p.excerpt && <p className="text-xs text-slate-400 line-clamp-2">{p.excerpt}</p>}
                  {p.author_name && (
                    <p className="text-[11px] text-slate-500 pt-1">{t('blog.byAuthor', { author: p.author_name })}</p>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
