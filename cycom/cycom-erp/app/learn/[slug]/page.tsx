'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { GraduationCap } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface CourseSummary {
  id: string;
  title: string;
  slug: string;
  description: string;
  lesson_count: number;
}

export default function CourseListPage() {
  const t = useT();
  const params = useParams();
  const slug = params.slug as string;

  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/learn/${slug}/courses/`);
        if (!res.ok) throw new Error(t('elearning.loadFailed'));
        const data = await res.json();
        if (!cancelled) setCourses(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t('elearning.loadFailed'));
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
          <h1 className="text-lg font-black text-white">{t('elearning.title')}</h1>
        </header>

        {loading && <p className="text-slate-500 text-sm">{t('elearning.loading')}</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}
        {!loading && !error && courses.length === 0 && (
          <p className="text-slate-500 text-sm italic">{t('elearning.empty')}</p>
        )}

        {!loading && !error && courses.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {courses.map((c) => (
              <Link
                key={c.id}
                href={`/learn/${slug}/${c.slug}`}
                className="glass-card p-5 space-y-3 hover:border-white/20 transition-colors"
              >
                <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center">
                  <GraduationCap className="w-5 h-5 text-emerald-400" />
                </div>
                <h3 className="text-sm font-bold text-white">{c.title}</h3>
                {c.description && <p className="text-xs text-slate-400 line-clamp-2">{c.description}</p>}
                <p className="text-[11px] text-slate-500 pt-1">{t('elearning.lessonCount', { count: c.lesson_count })}</p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
