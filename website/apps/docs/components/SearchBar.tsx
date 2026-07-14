"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Search, X, ArrowRight, Clock, Loader2 } from "lucide-react";
import { type DocItem } from "@/lib/types";
import { ContentBadge } from "./ContentBadge";
import { cn } from "@/lib/utils";

const API_BASE = "https://api.cy-com.com/api/v1/public/documentation";

interface SearchSuggestion {
  items: DocItem[];
  total: number;
}

interface SearchBarProps {
  /** Large hero variant vs compact header variant */
  variant?: "hero" | "header" | "compact";
  placeholder?: string;
  autoFocus?: boolean;
  className?: string;
  onClose?: () => void;
}

export function SearchBar({
  variant = "header",
  placeholder = "Search documentation…",
  autoFocus = false,
  className,
  onClose,
}: SearchBarProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<SearchSuggestion | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounced live suggestions
  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.trim().length < 2) {
      setSuggestions(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/search/?q=${encodeURIComponent(q)}&limit=6`);
      if (res.ok) {
        const data: SearchSuggestion = await res.json();
        setSuggestions(data);
      }
    } catch {
      // silently fail for suggestions
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.trim().length < 2) {
      setSuggestions(null);
      setLoading(false);
      setActiveIndex(-1);
      return;
    }
    setLoading(true);
    debounceRef.current = setTimeout(() => {
      void fetchSuggestions(query);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, fetchSuggestions]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, []);

  // Auto-focus
  useEffect(() => {
    if (autoFocus) inputRef.current?.focus();
  }, [autoFocus]);

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    setQuery(e.target.value);
    setOpen(true);
    setActiveIndex(-1);
  }

  function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    if (!query.trim()) return;
    setOpen(false);
    router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    onClose?.();
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    const items = suggestions?.items ?? [];
    if (e.key === "Escape") {
      if (open) {
        setOpen(false);
      } else {
        setQuery("");
        onClose?.();
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, items.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, -1));
    } else if (e.key === "Enter") {
      if (activeIndex >= 0 && items[activeIndex]) {
        const item = items[activeIndex];
        const href = item.url ?? `/${item.section_slug ?? "docs"}/${item.slug}`;
        setOpen(false);
        router.push(href);
        onClose?.();
      } else {
        handleSubmit();
      }
    }
  }

  function clearSearch() {
    setQuery("");
    setSuggestions(null);
    setOpen(false);
    inputRef.current?.focus();
  }

  const showDropdown = open && query.trim().length >= 2;

  const isHero = variant === "hero";
  const isCompact = variant === "compact";

  return (
    <div
      ref={containerRef}
      className={cn("relative w-full", className)}
      role="search"
      aria-label="Documentation search"
    >
      <form onSubmit={handleSubmit}>
        <div
          className={cn(
            "relative flex items-center",
            isHero
              ? "rounded-2xl border border-white/[0.12] bg-white/[0.05] backdrop-blur-xl shadow-[0_0_0_1px_rgba(255,255,255,0.06),0_16px_48px_rgba(0,0,0,0.5)] focus-within:border-cy-orange/40 focus-within:shadow-[0_0_0_1px_rgba(237,108,0,0.2),0_16px_48px_rgba(0,0,0,0.5)] transition-all duration-200"
              : isCompact
              ? "rounded-lg border border-white/[0.08] bg-white/[0.04] backdrop-blur-md focus-within:border-cy-orange/40 transition-all duration-200"
              : "rounded-xl border border-white/[0.09] bg-white/[0.04] backdrop-blur-md focus-within:border-cy-orange/35 focus-within:shadow-[0_0_0_3px_rgba(237,108,0,0.09)] transition-all duration-200"
          )}
        >
          {/* Search icon */}
          <span
            className={cn(
              "flex-shrink-0 flex items-center justify-center",
              isHero ? "w-14 h-14" : isCompact ? "w-8 pl-2.5" : "w-10"
            )}
            aria-hidden="true"
          >
            {loading ? (
              <Loader2
                className={cn(
                  "animate-spin text-cy-orange",
                  isHero ? "w-5 h-5" : isCompact ? "w-3.5 h-3.5" : "w-4 h-4"
                )}
              />
            ) : (
              <Search
                className={cn(
                  "text-cy-gray-600",
                  isHero ? "w-5 h-5" : isCompact ? "w-3.5 h-3.5" : "w-4 h-4"
                )}
              />
            )}
          </span>

          {/* Input */}
          <input
            ref={inputRef}
            type="search"
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => query.trim().length >= 2 && setOpen(true)}
            placeholder={placeholder}
            aria-label={placeholder}
            aria-expanded={showDropdown}
            aria-controls="search-dropdown"
            aria-autocomplete="list"
            aria-activedescendant={
              activeIndex >= 0 ? `search-item-${activeIndex}` : undefined
            }
            role="combobox"
            autoComplete="off"
            spellCheck="false"
            className={cn(
              "flex-1 bg-transparent border-none outline-none text-white placeholder:text-cy-gray-600",
              isHero
                ? "text-base py-4 pr-4"
                : isCompact
                ? "text-sm py-1.5 pr-2"
                : "text-sm py-2.5 pr-3"
            )}
          />

          {/* Clear + Submit */}
          <div className="flex items-center gap-1 pr-2">
            {query && (
              <button
                type="button"
                onClick={clearSearch}
                aria-label="Clear search"
                className="btn-ghost !p-1.5 !rounded-md"
              >
                <X className={isHero ? "w-4 h-4" : "w-3.5 h-3.5"} />
              </button>
            )}
            {!isCompact && (
              <button
                type="submit"
                aria-label="Search"
                className={cn(
                  "flex-shrink-0 flex items-center justify-center rounded-lg bg-cy-orange text-white font-medium transition-all duration-200 hover:bg-cy-orange-light",
                  isHero ? "px-5 py-2.5 text-sm gap-1.5" : "px-3 py-1.5 text-xs gap-1"
                )}
              >
                <span className={isHero ? "block" : "hidden sm:block"}>Search</span>
                <ArrowRight className={isHero ? "w-4 h-4" : "w-3.5 h-3.5"} />
              </button>
            )}
          </div>
        </div>
      </form>

      {/* Suggestions dropdown */}
      {showDropdown && (
        <div
          id="search-dropdown"
          role="listbox"
          aria-label="Search suggestions"
          className="absolute top-full left-0 right-0 mt-2 z-50 rounded-xl border border-white/[0.10] bg-[#0f0f1a]/95 backdrop-blur-xl shadow-[0_24px_64px_rgba(0,0,0,0.6)] overflow-hidden animate-fade-in"
        >
          {suggestions && suggestions.items.length > 0 ? (
            <>
              <ul className="max-h-80 overflow-y-auto py-1.5">
                {suggestions.items.map((item, idx) => {
                  const href = item.url ?? `/${item.section_slug ?? "docs"}/${item.slug}`;
                  return (
                    <li key={item.id ?? idx} role="option" aria-selected={activeIndex === idx}>
                      <a
                        id={`search-item-${idx}`}
                        href={href}
                        onClick={() => {
                          setOpen(false);
                          onClose?.();
                        }}
                        className={cn(
                          "flex items-center gap-3 px-4 py-2.5 transition-colors duration-100",
                          activeIndex === idx
                            ? "bg-cy-orange/10 text-white"
                            : "hover:bg-white/[0.04] text-cy-gray-200"
                        )}
                      >
                        <Search className="w-3.5 h-3.5 text-cy-gray-600 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium truncate">{item.title}</span>
                            <ContentBadge type={item.content_type} />
                          </div>
                          {item.summary && (
                            <p className="text-xs text-cy-gray-600 truncate mt-0.5">
                              {item.summary}
                            </p>
                          )}
                        </div>
                        {item.section && (
                          <span className="text-xs text-cy-gray-600 flex-shrink-0">
                            {item.section}
                          </span>
                        )}
                      </a>
                    </li>
                  );
                })}
              </ul>
              <div className="px-4 py-2.5 border-t border-white/[0.07] flex items-center justify-between">
                <span className="text-xs text-cy-gray-600">
                  {suggestions.total} result{suggestions.total !== 1 ? "s" : ""}
                </span>
                <button
                  type="button"
                  onClick={() => handleSubmit()}
                  className="text-xs text-cy-orange hover:text-cy-orange-light flex items-center gap-1 transition-colors"
                >
                  See all results <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </>
          ) : !loading ? (
            <div className="px-4 py-6 text-center">
              <p className="text-sm text-cy-gray-600">No results for &ldquo;{query}&rdquo;</p>
              <p className="text-xs text-cy-gray-600 mt-1">Try different keywords</p>
            </div>
          ) : (
            <div className="px-4 py-6 text-center">
              <Loader2 className="w-5 h-5 text-cy-orange animate-spin mx-auto mb-2" />
              <p className="text-xs text-cy-gray-600">Searching…</p>
            </div>
          )}

          {/* Keyboard hints */}
          <div className="px-4 py-2 border-t border-white/[0.05] flex items-center gap-3 flex-wrap">
            {[
              { key: "↑↓", label: "navigate" },
              { key: "↵", label: "select" },
              { key: "Esc", label: "close" },
            ].map(({ key, label }) => (
              <span key={key} className="flex items-center gap-1 text-[0.625rem] text-cy-gray-600">
                <kbd className="px-1 py-0.5 rounded bg-white/[0.06] border border-white/[0.08] font-mono text-[0.625rem]">
                  {key}
                </kbd>
                {label}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
