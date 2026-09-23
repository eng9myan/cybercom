'use client';

import React, { useEffect, useRef, useState } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface ChatMsg {
  id: string;
  sender: 'visitor' | 'agent';
  body: string;
  created_at: string;
}

const POLL_INTERVAL_MS = 3000;

function tokenKey(slug: string) {
  return `cycom_chat_token_${slug}`;
}

export default function PublicChatWidget({ slug }: { slug: string }) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [status, setStatus] = useState<'open' | 'closed'>('open');
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const cursorRef = useRef<string | null>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el && typeof el.scrollTo === 'function') {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, open]);

  const ensureSession = async (): Promise<string> => {
    let existing: string | null = null;
    try {
      existing = localStorage.getItem(tokenKey(slug));
    } catch {
      /* private browsing / storage blocked — fall through to a fresh session */
    }
    if (existing) return existing;

    const res = await fetch(`/api/chat/${slug}/sessions/`, { method: 'POST' });
    const data = await res.json();
    try {
      localStorage.setItem(tokenKey(slug), data.token);
    } catch {
      /* non-fatal — chat still works for this page view */
    }
    return data.token;
  };

  const poll = async (tok: string) => {
    const url = cursorRef.current
      ? `/api/chat/${slug}/sessions/${tok}/messages/?since=${encodeURIComponent(cursorRef.current)}`
      : `/api/chat/${slug}/sessions/${tok}/messages/`;
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();
    setStatus(data.status);
    if (data.messages.length > 0) {
      cursorRef.current = data.messages[data.messages.length - 1].created_at;
      setMessages((prev) => [...prev, ...data.messages]);
    }
  };

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    let interval: ReturnType<typeof setInterval> | undefined;

    (async () => {
      const tok = await ensureSession();
      if (cancelled) return;
      setToken(tok);
      await poll(tok);
      interval = setInterval(() => poll(tok), POLL_INTERVAL_MS);
    })();

    return () => {
      cancelled = true;
      if (interval) clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, slug]);

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !input.trim() || sending) return;
    setSending(true);
    const body = input;
    setInput('');
    try {
      const res = await fetch(`/api/chat/${slug}/sessions/${token}/messages/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body }),
      });
      if (res.ok) {
        const msg = await res.json();
        cursorRef.current = msg.created_at;
        setMessages((prev) => [...prev, msg]);
      }
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? t('liveChat.close') : t('liveChat.open')}
        className="fixed bottom-6 end-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-sky-500 to-blue-600 shadow-lg shadow-blue-500/30 flex items-center justify-center hover:scale-105 transition-transform"
      >
        {open ? <X className="w-6 h-6 text-white" /> : <MessageCircle className="w-6 h-6 text-white" />}
      </button>

      {open && (
        <div
          className="fixed bottom-24 end-6 z-50 w-96 max-w-[calc(100vw-3rem)] h-[480px] max-h-[70vh] rounded-2xl border border-white/10 flex flex-col overflow-hidden shadow-2xl"
          style={{ background: 'rgba(15,15,26,0.98)', backdropFilter: 'blur(20px)' }}
        >
          <div className="flex items-center gap-2.5 px-4 h-14 shrink-0 border-b border-white/5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
              <MessageCircle className="w-4 h-4 text-blue-400" />
            </div>
            <p className="text-sm font-semibold text-white leading-none">{t('liveChat.title')}</p>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-2">
            {messages.length === 0 && <p className="text-xs text-slate-500">{t('liveChat.greeting')}</p>}
            {messages.map((m) => (
              <div
                key={m.id}
                className={`text-xs px-3 py-2 rounded-xl max-w-[85%] ${
                  m.sender === 'visitor' ? 'ms-auto bg-blue-500/20 text-blue-100' : 'bg-white/5 text-slate-200'
                }`}
              >
                {m.body}
              </div>
            ))}
          </div>

          {status === 'closed' ? (
            <p className="text-xs text-slate-500 italic p-3 border-t border-white/5">{t('liveChat.closedNotice')}</p>
          ) : (
            <form onSubmit={send} className="flex items-center gap-2 p-3 border-t border-white/5 shrink-0">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={t('liveChat.inputPlaceholder')}
                className="flex-1 bg-white/5 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 outline-none focus:ring-1 focus:ring-blue-500/50"
              />
              <button
                type="submit"
                disabled={sending || !input.trim()}
                className="w-9 h-9 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 flex items-center justify-center shrink-0 transition-colors"
              >
                <Send className="w-4 h-4 text-white" />
              </button>
            </form>
          )}
        </div>
      )}
    </>
  );
}
