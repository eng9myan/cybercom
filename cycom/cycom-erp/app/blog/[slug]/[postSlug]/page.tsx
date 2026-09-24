'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface BlogPostDetail {
  id: string;
  title: string;
  slug: string;
  content: string;
  cover_image_url: string | null;
  author_name: string;
  published_at: string;
}

export default function BlogPostPage() {
  const t = useT();
  const params = useParams();
  const slug = params.slug as string;
  const postSlug = params.postSlug as string;

  const [post, setPost] = useState<BlogPostDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/blog/${slug}/posts/${postSlug}/`);
        if (!res.ok) throw new Error(t('blog.postNotFound'));
        const data = await res.json();
        if (!cancelled) setPost(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t('blog.postNotFound'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [slug, postSlug, t]);

  return (
    <div className="min-h-screen bg-[#030712] text-white p-4 md:p-8 font-sans">
      <div className="max-w-3xl mx-auto space-y-6">
        <Link href={`/blog/${slug}`} className="inline-flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-white">
          <ArrowLeft className="w-4 h-4 rtl:-scale-x-100" /> {t('blog.backToBlog')}
        </Link>

        {loading && <p className="text-slate-500 text-sm">{t('blog.loading')}</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}

        {!loading && !error && post && (
          <article className="space-y-4">
            {post.cover_image_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={post.cover_image_url} alt={post.title} className="w-full h-64 object-cover rounded-xl" />
            )}
            <h1 className="text-2xl font-black text-white">{post.title}</h1>
            {post.author_name && (
              <p className="text-xs text-slate-500">{t('blog.byAuthor', { author: post.author_name })}</p>
            )}
            <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{post.content}</div>
          </article>
        )}
      </div>
    </div>
  );
}
