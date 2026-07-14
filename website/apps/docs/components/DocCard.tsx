"use client";

import Link from "next/link";
import { Calendar, Tag, ArrowRight } from "lucide-react";
import { type DocItem } from "@/lib/types";
import { formatDate, truncate } from "@/lib/utils";
import { ContentBadge } from "./ContentBadge";

interface DocCardProps {
  item: DocItem;
  /**
   * If true the card fills the full row (list view).
   * If false it occupies a grid cell.
   */
  variant?: "grid" | "list";
}

export function DocCard({ item, variant = "grid" }: DocCardProps) {
  const href = item.url ?? `/${item.section_slug ?? "docs"}/${item.slug}`;
  const summary = truncate(item.summary ?? "", 160);
  const date = item.last_updated ? formatDate(item.last_updated) : null;

  if (variant === "list") {
    return (
      <Link
        href={href}
        className="group flex items-start gap-4 p-4 rounded-xl border border-white/[0.07] bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/[0.12] transition-all duration-200"
        aria-label={item.title}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <ContentBadge type={item.content_type} />
            {item.section && (
              <span className="text-[0.6875rem] text-cy-gray-600">{item.section}</span>
            )}
          </div>
          <h3 className="text-sm font-semibold text-white group-hover:text-cy-orange transition-colors leading-snug mb-1 truncate">
            {item.title}
          </h3>
          {summary && (
            <p className="text-xs text-cy-gray-400 leading-relaxed line-clamp-2">{summary}</p>
          )}
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            {date && (
              <span className="flex items-center gap-1 text-[0.6875rem] text-cy-gray-600">
                <Calendar className="w-3 h-3" />
                {date}
              </span>
            )}
            {item.tags && item.tags.length > 0 && (
              <span className="flex items-center gap-1 text-[0.6875rem] text-cy-gray-600">
                <Tag className="w-3 h-3" />
                {item.tags.slice(0, 3).join(", ")}
              </span>
            )}
          </div>
        </div>
        <ArrowRight className="w-4 h-4 text-cy-gray-600 group-hover:text-cy-orange transition-colors flex-shrink-0 mt-1" />
      </Link>
    );
  }

  return (
    <Link
      href={href}
      className="group glass-card p-5 flex flex-col gap-3 h-full hover:border-white/[0.14]"
      aria-label={item.title}
    >
      <div className="flex items-start justify-between gap-2">
        <ContentBadge type={item.content_type} />
        <ArrowRight className="w-4 h-4 text-cy-gray-600 group-hover:text-cy-orange transition-colors flex-shrink-0 mt-0.5" />
      </div>

      <div className="flex-1">
        <h3 className="text-sm font-semibold text-white group-hover:text-cy-orange transition-colors leading-snug mb-2">
          {item.title}
        </h3>
        {summary && (
          <p className="text-xs text-cy-gray-400 leading-relaxed line-clamp-3">{summary}</p>
        )}
      </div>

      <div className="flex items-center gap-3 flex-wrap pt-1 border-t border-white/[0.05]">
        {date && (
          <span className="flex items-center gap-1 text-[0.6875rem] text-cy-gray-600">
            <Calendar className="w-3 h-3" />
            {date}
          </span>
        )}
        {item.tags && item.tags.length > 0 && (
          <div className="flex items-center gap-1 flex-wrap">
            {item.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="text-[0.625rem] px-1.5 py-0.5 rounded bg-white/[0.05] text-cy-gray-600 border border-white/[0.06]"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
