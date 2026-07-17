'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, X, Send, Loader2 } from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant' | 'error';
  content: string;
}

const STARTER_QUESTIONS = [
  'What are total sales this month?',
  'How many overdue invoices exist?',
  'Which employees were late today?',
];

export default function CyaiChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el && typeof el.scrollTo === 'function') {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, open]);

  const ask = async (question: string) => {
    if (!question.trim() || loading) return;
    setMessages((prev) => [...prev, { role: 'user', content: question }]);
    setInput('');
    setLoading(true);
    try {
      const res = await fetch('/api/cycom/cyai/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
        credentials: 'include',
      });
      const data = await res.json();
      if (!res.ok || data.error) {
        setMessages((prev) => [...prev, { role: 'error', content: data.error?.message || 'Something went wrong.' }]);
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }]);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'error', content: 'Could not reach the Cycom backend.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    ask(input);
  };

  return (
    <>
      {/* Floating launcher */}
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? 'Close CyAI assistant' : 'Open CyAI assistant'}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-[#E67E22] to-[#D35400] shadow-lg shadow-orange-500/30 flex items-center justify-center hover:scale-105 transition-transform"
      >
        {open ? <X className="w-6 h-6 text-white" /> : <Sparkles className="w-6 h-6 text-white" />}
      </button>

      {open && (
        <div
          className="fixed bottom-24 right-6 z-50 w-96 max-w-[calc(100vw-3rem)] h-[520px] max-h-[70vh] rounded-2xl border border-white/10 flex flex-col overflow-hidden shadow-2xl"
          style={{ background: 'rgba(15,15,26,0.98)', backdropFilter: 'blur(20px)' }}
        >
          {/* Header */}
          <div className="flex items-center gap-2.5 px-4 h-14 shrink-0 border-b border-white/5">
            <div className="w-8 h-8 rounded-lg bg-orange-500/15 border border-orange-500/30 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-orange-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white leading-none">CyAI Assistant</p>
              <p className="text-[10px] text-slate-500 mt-0.5">Local Memory Agent — grounded in real Cycom data</p>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="space-y-2">
                <p className="text-xs text-slate-500">Try asking:</p>
                {STARTER_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => ask(q)}
                    className="block w-full text-left text-xs px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`text-xs px-3 py-2 rounded-xl max-w-[85%] ${
                  m.role === 'user'
                    ? 'ml-auto bg-orange-500/20 text-orange-100'
                    : m.role === 'error'
                      ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                      : 'bg-white/5 text-slate-200'
                }`}
              >
                {m.content}
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Thinking…
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="flex items-center gap-2 p-3 border-t border-white/5 shrink-0">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about sales, invoices, stock, attendance…"
              className="flex-1 bg-white/5 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 outline-none focus:ring-1 focus:ring-orange-500/50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="w-9 h-9 rounded-lg bg-orange-600 hover:bg-orange-500 disabled:opacity-40 flex items-center justify-center shrink-0 transition-colors"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
