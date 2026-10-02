'use client';

import React, { Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { MessageSquare, Send, UserCheck, X, Plus } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useT } from '@/lib/i18n';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/ProviderPortalEmptyStates';

type ThreadStatus = 'open' | 'closed';
type ThreadCategory = 'general' | 'prescription' | 'results' | 'appointment' | 'billing';

type Thread = {
  id: string;
  patient: string;
  subject: string;
  category: ThreadCategory;
  status: ThreadStatus;
  assigned_to: string;
  last_message_at: string;
  unread: number;
  created_at: string;
};

type MessageRow = {
  id: string;
  sender_type: 'patient' | 'staff';
  sender: string;
  body: string;
  read_at: string | null;
  created_at: string;
};

type ThreadDetail = Thread & { messages: MessageRow[] };

type Page<T> = { results: T[]; next: string | null };

const CATEGORIES: ThreadCategory[] = ['general', 'prescription', 'results', 'appointment', 'billing'];

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

async function fetchAll<T>(url: string): Promise<T[]> {
  const all: T[] = [];
  let next: string | null = url;
  while (next) {
    const res = await fetch(next, { credentials: 'include' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const json = (await res.json()) as Page<T>;
    all.push(...json.results);
    next = json.next;
  }
  return all;
}

export default function MessagesPage() {
  return (
    <Suspense fallback={null}>
      <MessagesPageInner />
    </Suspense>
  );
}

function MessagesPageInner() {
  const t = useT();
  const { user, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();

  const [threads, setThreads] = useState<Thread[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<ThreadStatus | 'all'>('open');

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ThreadDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [replyBody, setReplyBody] = useState('');
  const [sending, setSending] = useState(false);
  const [assignInput, setAssignInput] = useState('');

  const [composing, setComposing] = useState(false);
  const [composePatient, setComposePatient] = useState('');
  const [composeSubject, setComposeSubject] = useState('');
  const [composeCategory, setComposeCategory] = useState<ThreadCategory>('general');
  const [composeBody, setComposeBody] = useState('');
  const [composeError, setComposeError] = useState<string | null>(null);
  const [composeSaving, setComposeSaving] = useState(false);

  const loadThreads = useCallback(() => {
    setLoading(true);
    setError(null);
    const qs = statusFilter === 'all' ? '' : `?status=${statusFilter}`;
    fetchAll<Thread>(`/api/cymed/rest/messages/threads/${qs}`)
      .then((rows) => setThreads(rows))
      .catch((e) => setError(e instanceof Error ? e.message : t('messages.loadFailed')))
      .finally(() => setLoading(false));
  }, [statusFilter, t]);

  useEffect(() => {
    if (!authLoading && user) loadThreads();
  }, [authLoading, user, loadThreads]);

  useEffect(() => {
    const newPatient = searchParams.get('new');
    if (newPatient) {
      setComposePatient(newPatient);
      setComposing(true);
    }
  }, [searchParams]);

  const loadDetail = useCallback((id: string) => {
    setDetailLoading(true);
    setAssignInput('');
    fetch(`/api/cymed/rest/messages/threads/${id}/`, { credentials: 'include' })
      .then(async (res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then((json: ThreadDetail) => {
        setDetail(json);
        setAssignInput(json.assigned_to || '');
      })
      .catch((e) => setError(e instanceof Error ? e.message : t('messages.loadFailed')))
      .finally(() => setDetailLoading(false));
  }, [t]);

  const openThread = (id: string) => {
    setSelectedId(id);
    loadDetail(id);
  };

  const sendReply = async () => {
    if (!selectedId || !replyBody.trim()) return;
    setSending(true);
    try {
      const res = await fetch(`/api/cymed/rest/messages/threads/${selectedId}/reply/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ body: replyBody }),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      setReplyBody('');
      loadDetail(selectedId);
      loadThreads();
    } catch (e) {
      setError(e instanceof Error ? e.message : t('messages.sendFailed'));
    } finally {
      setSending(false);
    }
  };

  const assignThread = async () => {
    if (!selectedId) return;
    try {
      const res = await fetch(`/api/cymed/rest/messages/threads/${selectedId}/assign/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ assigned_to: assignInput }),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      loadDetail(selectedId);
      loadThreads();
    } catch (e) {
      setError(e instanceof Error ? e.message : t('messages.assignFailed'));
    }
  };

  const closeThread = async () => {
    if (!selectedId) return;
    try {
      const res = await fetch(`/api/cymed/rest/messages/threads/${selectedId}/close/`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      loadDetail(selectedId);
      loadThreads();
    } catch (e) {
      setError(e instanceof Error ? e.message : t('messages.closeFailed'));
    }
  };

  const submitCompose = async () => {
    setComposeError(null);
    if (!composePatient.trim() || !composeSubject.trim() || !composeBody.trim()) {
      setComposeError(t('messages.composeValidation'));
      return;
    }
    setComposeSaving(true);
    try {
      const res = await fetch('/api/cymed/rest/messages/threads/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          patient: composePatient,
          subject: composeSubject,
          category: composeCategory,
          body: composeBody,
        }),
      });
      if (res.status === 404) {
        setComposeError(t('messages.patientNotFound'));
        return;
      }
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const created = (await res.json()) as Thread;
      setComposing(false);
      setComposeSubject('');
      setComposeBody('');
      setComposeCategory('general');
      loadThreads();
      openThread(created.id);
    } catch (e) {
      setComposeError(e instanceof Error ? e.message : t('messages.sendFailed'));
    } finally {
      setComposeSaving(false);
    }
  };

  const categoryLabel: Record<ThreadCategory, string> = useMemo(() => ({
    general: t('messages.categoryGeneral'),
    prescription: t('messages.categoryPrescription'),
    results: t('messages.categoryResults'),
    appointment: t('messages.categoryAppointment'),
    billing: t('messages.categoryBilling'),
  }), [t]);

  if (authLoading) {
    return <LoadingCard label={t('common.loading')} />;
  }

  if (!user) {
    return (
      <div className="glass-card p-10 text-center max-w-md mx-auto mt-16">
        <h2 className="text-lg font-bold mb-2">{t('auth.signInTitle')}</h2>
        <p className="text-sm text-slate-400 mb-5">{t('auth.signInDetail')}</p>
        <a href="/login" className="btn-primary inline-block">{t('auth.signIn')}</a>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('messages.title')}</h1>
          <p className="page-subtitle">{t('messages.subtitle')}</p>
        </div>
        <div className="flex items-center gap-1.5">
          {(['open', 'closed', 'all'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={statusFilter === s ? 'btn-primary text-xs px-3 py-1.5' : 'btn-secondary text-xs px-3 py-1.5'}
            >
              {s === 'open' ? t('messages.filterOpen') : s === 'closed' ? t('messages.filterClosed') : t('messages.filterAll')}
            </button>
          ))}
          <button
            onClick={() => { setComposing(true); setComposeError(null); }}
            className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1"
          >
            <Plus className="w-3.5 h-3.5" />
            {t('messages.newThread')}
          </button>
        </div>
      </div>

      {loading ? (
        <LoadingCard label={t('common.loading')} />
      ) : error && !threads ? (
        <ErrorCard error={error} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-4">
          <div className="glass-card p-2">
            <div className="flex items-center gap-2 px-3 py-2 text-xs text-slate-500">
              <MessageSquare className="w-3.5 h-3.5" />
              {t('messages.count', { n: (threads || []).length })}
            </div>
            {(threads || []).length === 0 ? (
              <EmptyCard label={t('messages.empty')} />
            ) : (
              <div className="divide-y divide-white/5">
                {(threads || []).map((th) => (
                  <button
                    key={th.id}
                    onClick={() => openThread(th.id)}
                    className={`w-full text-start px-3 py-3 hover:bg-white/5 transition-colors ${selectedId === th.id ? 'bg-white/5' : ''}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-sm text-white truncate">{th.subject}</span>
                      {th.unread > 0 && (
                        <span className="badge badge-teal shrink-0">{th.unread}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                      <span className="badge badge-blue">{categoryLabel[th.category]}</span>
                      <span className={`badge ${th.status === 'open' ? 'badge-green' : 'badge-red'}`}>
                        {th.status === 'open' ? t('messages.filterOpen') : t('messages.filterClosed')}
                      </span>
                      <span>{formatDateTime(th.last_message_at)}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="glass-card p-4 min-h-[300px]">
            {!selectedId ? (
              <EmptyCard label={t('messages.selectThread')} />
            ) : detailLoading || !detail ? (
              <LoadingCard label={t('common.loading')} />
            ) : (
              <div className="flex flex-col h-full">
                <div className="flex items-start justify-between gap-2 pb-3 border-b border-white/5">
                  <div>
                    <h3 className="font-bold text-white">{detail.subject}</h3>
                    <p className="text-xs text-slate-500">{categoryLabel[detail.category]}</p>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className={`badge ${detail.status === 'open' ? 'badge-green' : 'badge-red'}`}>
                      {detail.status === 'open' ? t('messages.filterOpen') : t('messages.filterClosed')}
                    </span>
                    {detail.status === 'open' && (
                      <button onClick={closeThread} className="btn-secondary text-xs px-2 py-1 flex items-center gap-1">
                        <X className="w-3 h-3" />
                        {t('messages.close')}
                      </button>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 py-2 border-b border-white/5">
                  <UserCheck className="w-3.5 h-3.5 text-slate-500" />
                  <input
                    type="text"
                    value={assignInput}
                    onChange={(e) => setAssignInput(e.target.value)}
                    placeholder={t('messages.assignPlaceholder')}
                    className="bg-transparent border border-white/8 rounded-lg px-2 py-1 text-xs text-white placeholder-slate-500 flex-1"
                  />
                  <button onClick={assignThread} className="btn-secondary text-xs px-2 py-1">
                    {t('messages.assign')}
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto py-3 space-y-3 max-h-[320px]">
                  {detail.messages.map((m) => (
                    <div
                      key={m.id}
                      className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                        m.sender_type === 'staff' ? 'ms-auto bg-[var(--cy-teal)]/10 border border-[var(--cy-teal)]/20' : 'bg-white/5 border border-white/8'
                      }`}
                    >
                      <p className="text-slate-200 whitespace-pre-wrap">{m.body}</p>
                      <p className="text-[10px] text-slate-500 mt-1">{m.sender} · {formatDateTime(m.created_at)}</p>
                    </div>
                  ))}
                </div>

                {detail.status === 'open' && (
                  <div className="flex items-end gap-2 pt-2 border-t border-white/5">
                    <textarea
                      value={replyBody}
                      onChange={(e) => setReplyBody(e.target.value)}
                      placeholder={t('messages.replyPlaceholder')}
                      rows={2}
                      className="bg-transparent border border-white/8 rounded-lg px-2 py-1.5 text-xs text-white placeholder-slate-500 flex-1 resize-none"
                    />
                    <button
                      onClick={sendReply}
                      disabled={sending || !replyBody.trim()}
                      className="btn-primary text-xs px-3 py-2 flex items-center gap-1"
                    >
                      <Send className="w-3.5 h-3.5" />
                      {t('messages.send')}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {composing && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-5 w-full max-w-md space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white">{t('messages.newThread')}</h3>
              <button onClick={() => setComposing(false)} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2">
              <input
                type="text"
                value={composePatient}
                onChange={(e) => setComposePatient(e.target.value)}
                placeholder={t('messages.patientIdPlaceholder')}
                className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500"
              />
              <input
                type="text"
                value={composeSubject}
                onChange={(e) => setComposeSubject(e.target.value)}
                placeholder={t('messages.subjectPlaceholder')}
                className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500"
              />
              <select
                value={composeCategory}
                onChange={(e) => setComposeCategory(e.target.value as ThreadCategory)}
                className="w-full bg-[#0a0f1e] border border-white/8 rounded-lg px-3 py-2 text-xs text-white"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{categoryLabel[c]}</option>
                ))}
              </select>
              <textarea
                value={composeBody}
                onChange={(e) => setComposeBody(e.target.value)}
                placeholder={t('messages.bodyPlaceholder')}
                rows={4}
                className="w-full bg-transparent border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 resize-none"
              />
              {composeError && <p className="text-xs text-rose-400">{composeError}</p>}
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => setComposing(false)} className="btn-secondary text-xs px-3 py-1.5">
                {t('common.cancel')}
              </button>
              <button
                onClick={submitCompose}
                disabled={composeSaving}
                className="btn-primary text-xs px-3 py-1.5"
              >
                {t('messages.send')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
