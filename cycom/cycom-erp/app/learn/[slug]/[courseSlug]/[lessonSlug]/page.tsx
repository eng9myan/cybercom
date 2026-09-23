'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface LessonDetail {
  id: string;
  title: string;
  slug: string;
  content: string;
  order: number;
}

function tokenKey(slug: string, courseSlug: string) {
  return `cycom_learn_token_${slug}_${courseSlug}`;
}

export default function LessonPage() {
  const t = useT();
  const params = useParams();
  const slug = params.slug as string;
  const courseSlug = params.courseSlug as string;
  const lessonSlug = params.lessonSlug as string;

  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [token, setToken] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);
  const [progressPercent, setProgressPercent] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let tok: string | null = null;
    try {
      tok = localStorage.getItem(tokenKey(slug, courseSlug));
    } catch {
      /* private browsing / storage blocked */
    }
    setToken(tok);

    (async () => {
      try {
        const res = await fetch(`/api/learn/${slug}/courses/${courseSlug}/lessons/${lessonSlug}/`);
        if (!res.ok) throw new Error(t('elearning.lessonNotFound'));
        const data = await res.json();
        if (cancelled) return;
        setLesson(data);

        if (tok) {
          const progRes = await fetch(
            `/api/learn/${slug}/courses/${courseSlug}/lessons/${lessonSlug}/progress/?token=${encodeURIComponent(tok)}`
          );
          if (progRes.ok && !cancelled) {
            const progData = await progRes.json();
            setCompleted(progData.completed);
            setProgressPercent(progData.progress_percent);
          }
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t('elearning.lessonNotFound'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [slug, courseSlug, lessonSlug, t]);

  const markComplete = async () => {
    if (!token) return;
    setSaving(true);
    setSaveError(null);
    try {
      const res = await fetch(`/api/learn/${slug}/courses/${courseSlug}/lessons/${lessonSlug}/progress/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });
      if (!res.ok) throw new Error(t('elearning.completeFailed'));
      const data = await res.json();
      setCompleted(data.completed);
      setProgressPercent(data.progress_percent);
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : t('elearning.completeFailed'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] text-white p-4 md:p-8 font-sans">
      <div className="max-w-3xl mx-auto space-y-6">
        <Link href={`/learn/${slug}/${courseSlug}`} className="inline-flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-white">
          <ArrowLeft className="w-4 h-4" /> {t('elearning.backToCourse')}
        </Link>

        {loading && <p className="text-slate-500 text-sm">{t('elearning.loading')}</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}

        {!loading && !error && lesson && (
          <article className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <h1 className="text-xl font-black text-white">{lesson.title}</h1>
              {progressPercent !== null && (
                <span className="text-[11px] text-slate-500 shrink-0">
                  {t('elearning.progressLabel', { percent: progressPercent })}
                </span>
              )}
            </div>
            <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{lesson.content}</div>

            {token ? (
              <div className="pt-2">
                {completed ? (
                  <div className="inline-flex items-center gap-2 text-emerald-400 text-xs font-bold">
                    <CheckCircle2 className="w-4 h-4" /> {t('elearning.completed')}
                  </div>
                ) : (
                  <button onClick={markComplete} disabled={saving} className="btn-primary py-1.5 px-4 text-xs disabled:opacity-50">
                    {saving ? t('elearning.completing') : t('elearning.markComplete')}
                  </button>
                )}
                {saveError && <p className="text-red-400 text-xs mt-2">{saveError}</p>}
              </div>
            ) : (
              <p className="text-slate-500 text-xs italic">{t('elearning.enrollToTrack')}</p>
            )}
          </article>
        )}
      </div>
    </div>
  );
}
