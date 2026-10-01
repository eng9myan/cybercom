"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowUp, Mic, MicOff, Sparkles } from "lucide-react";
import { useSendAgentMessage, useTodayStatus } from "@/lib/queries";
import { useSpeechRecognition, speak } from "@/lib/useSpeech";
import { ToolReceipt } from "./ToolReceipt";
import { BudgetBar } from "./BudgetBar";
import { Button } from "./ui";
import type { ChatMessage } from "@/lib/types";

const SUGGESTIONS = [
  "Something filling, high protein",
  "What's in my cart?",
  "How's my diet plan today?",
  "What am I running low on?",
];

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Tell me what you're hungry for, or ask about your plan, cart, or orders.",
    },
  ]);
  const [input, setInput] = useState("");
  const [voiceOn, setVoiceOn] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const send = useSendAgentMessage();
  const { data: today } = useTodayStatus(true);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSubmit = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || send.isPending) return;
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", text: trimmed }]);
      setInput("");
      send.mutate(trimmed, {
        onSuccess: (reply) => {
          setMessages((prev) => [
            ...prev,
            { id: crypto.randomUUID(), role: "assistant", text: reply.reply, toolCalls: reply.tool_calls },
          ]);
          if (voiceOn) speak(reply.reply);
        },
        onError: () => {
          setMessages((prev) => [
            ...prev,
            { id: crypto.randomUUID(), role: "assistant", text: "Something went wrong reaching CyMart. Try again." },
          ]);
        },
      });
    },
    [send, voiceOn],
  );

  const { listening, supported, start, stop } = useSpeechRecognition((text) => {
    setVoiceOn(true);
    handleSubmit(text);
  });

  return (
    <div className="flex flex-1 flex-col gap-3">
      {today && <BudgetBar status={today} />}

      <div ref={listRef} className="scrollbar-thin flex-1 space-y-3 overflow-y-auto py-1">
        {messages.map((m) => (
          <div key={m.id} className="animate-fade-up">
            {m.role === "user" ? (
              <div className="flex justify-end">
                <div
                  className="max-w-[85%] rounded-[16px] rounded-br-[4px] px-3.5 py-2 text-[14px]"
                  style={{ background: "var(--panel-2)", color: "var(--ink)" }}
                >
                  {m.text}
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                <div className="flex items-start gap-2">
                  <span
                    className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full"
                    style={{ background: "var(--teal-bg)", color: "var(--teal)" }}
                  >
                    <Sparkles size={12} />
                  </span>
                  <div className="max-w-[85%] rounded-[16px] rounded-tl-[4px] px-3.5 py-2 text-[14px]" style={{ background: "var(--panel)", border: "1px solid var(--line)" }}>
                    {m.text}
                  </div>
                </div>
                {m.toolCalls && m.toolCalls.length > 0 && (
                  <div className="ml-8 flex flex-col gap-2">
                    {m.toolCalls.map((tc, i) => (
                      <ToolReceipt key={i} call={tc} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {send.isPending && (
          <div className="ml-8 flex items-center gap-1.5 text-[13px]" style={{ color: "var(--ink-3)" }}>
            <span className="h-1.5 w-1.5 animate-pulse rounded-full" style={{ background: "var(--ink-3)" }} />
            CyMart is thinking…
          </div>
        )}
      </div>

      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => handleSubmit(s)}
              className="rounded-full border px-3 py-1.5 text-[12.5px] transition hover:brightness-95"
              style={{ borderColor: "var(--line-2)", color: "var(--ink-2)" }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit(input);
        }}
        className="flex items-center gap-2 rounded-[14px] border p-1.5"
        style={{ borderColor: "var(--line-2)", background: "var(--panel)" }}
      >
        {supported && (
          <Button
            type="button"
            variant="ghost"
            className={`h-9 w-9 rounded-full p-0 ${listening ? "mic-listening" : ""}`}
            onClick={() => (listening ? stop() : start())}
            aria-label={listening ? "Stop listening" : "Speak"}
            style={{
              background: listening ? "var(--teal-bg)" : "transparent",
              color: listening ? "var(--teal)" : "var(--ink-2)",
            }}
          >
            {listening ? <MicOff size={16} /> : <Mic size={16} />}
          </Button>
        )}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask CyMart to order, check your plan, or your cart…"
          className="flex-1 bg-transparent px-1 text-[14px] outline-none placeholder:text-[color:var(--ink-3)]"
        />
        <Button type="submit" variant="primary" className="h-9 w-9 rounded-full p-0" disabled={!input.trim() || send.isPending}>
          <ArrowUp size={16} />
        </Button>
      </form>
    </div>
  );
}
