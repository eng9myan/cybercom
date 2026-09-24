'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, BookOpen } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface LessonSummary {
  id: string;
  title: string;
  slug: string;
  order: number;
}

interface CourseDetail {
  id: string;
  title: string;
  slug: string;
  description: string;
  lessons: LessonSummary[];
}

function tokenKey(slug: string, courseSlug: string) {
  return `cycom_learn_token_${slug}_${courseSlug}`;
}

export default function CourseDetailPage() {
  const t = useT();
  const params = useParams();
  const slug = params.slug as string;
  const courseSlug = params.courseSlug as string;

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [token, setToken] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [enrolling, setEnrolling] = useState(false);
  const [enrollError, setEnrollError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/learn/${slug}/courses/${courseSlug}/`);
        if (!res.ok) throw new Error(t('elearning.courseNotFound'));
        const data = await res.json();
        if (!cancelled) setCourse(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t('elearning.courseNotFound'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    try {
      setToken(localStorage.getItem(tokenKey(slug, courseSlug)));
    } catch {
      /* private browsing / storage blocked — enrollment just won't persist across visits */
    }
    return () => { cancelled = true; };
  }, [slug, courseSlug, t]);

  const enroll = async (e: React.FormEvent) => {
    e.preventDefault();
    setEnrolling(true);
    setEnrollError(null);
    try {
      const res = await fetch(`/api/learn/${slug}/courses/${courseSlug}/enroll/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_name: name, student_email: email }),
      });
      if (!res.ok) throw new Error(t('elearning.enrollFailed'));
      const data = await res.json();
      setToken(data.token);
      try {
        localStorage.setItem(tokenKey(slug, courseSlug), data.token);
      } catch {
        /* non-fatal */
      }
    } catch (e2) {
      setEnrollError(e2 instanceof Error ? e2.message : t('elearning.enrollFailed'));
    } finally {
      setEnrolling(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] text-white p-4 md:p-8 font-sans">
      <div className="max-w-3xl mx-auto space-y-6">
        <Link href={`/learn/${slug}`} className="inline-flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-white">
          <ArrowLeft className="w-4 h-4 rtl:-scale-x-100" /> {t('elearning.backToCourses')}
        </Link>

        {loading && <p className="text-slate-500 text-sm">{t('elearning.loading')}</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}

        {!loading && !error && course && (
          <>
            <header className="space-y-2">
              <h1 className="text-xl font-black text-white">{course.title}</h1>
              {course.description && <p className="text-sm text-slate-400">{course.description}</p>}
            </header>

            {!token && (
              <form onSubmit={enroll} className="glass-card p-5 space-y-3">
                <h2 className="text-sm font-bold text-white">{t('elearning.enrollTitle')}</h2>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={t('elearning.namePlaceholder')}
                    className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
                  />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={t('elearning.emailPlaceholder')}
                    className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-white/30"
                  />
                </div>
                {enrollError && <p className="text-red-400 text-xs">{enrollError}</p>}
                <button type="submit" disabled={enrolling} className="btn-primary py-1.5 px-4 text-xs disabled:opacity-50">
                  {enrolling ? t('elearning.enrolling') : t('elearning.enroll')}
                </button>
              </form>
            )}
            {token && <p className="text-emerald-400 text-xs font-bold">{t('elearning.enrolled')}</p>}

            <section className="space-y-2">
              <h2 className="text-xs font-black text-slate-400 uppercase tracking-wide">{t('elearning.lessons')}</h2>
              {course.lessons.map((l) => (
                <Link
                  key={l.id}
                  href={`/learn/${slug}/${courseSlug}/${l.slug}`}
                  className="glass-card p-4 flex items-center gap-3 hover:border-white/20 transition-colors"
                >
                  <BookOpen className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span className="text-sm text-white">{l.title}</span>
                </Link>
              ))}
            </section>
          </>
        )}
      </div>
    </div>
  );
}
