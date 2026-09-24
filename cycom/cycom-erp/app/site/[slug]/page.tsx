'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import PublicBlockRenderer from '@/components/cms/PublicBlockRenderer';
import type { BlockNode } from '@/lib/cmsBlocks';
import { useT } from '@/lib/i18n';

interface PageData {
  title: string;
  meta_description: string;
  blocks: BlockNode[];
}

export default function SiteHomepage() {
  const t = useT();
  const params = useParams();
  const slug = params.slug as string;

  const [page, setPage] = useState<PageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/site/${slug}/`);
        if (!res.ok) throw new Error(t('cmsPublic.notFound'));
        const data = await res.json();
        if (!cancelled) setPage(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t('cmsPublic.notFound'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [slug, t]);

  return (
    <div className="min-h-screen bg-[#030712] text-white font-sans">
      {loading && <p className="text-slate-500 text-sm p-8">{t('cmsPublic.loading')}</p>}
      {error && <p className="text-red-400 text-sm p-8">{error}</p>}
      {!loading && !error && page && (
        <div className="space-y-6 py-8">
          {page.blocks.map((block) => (
            <PublicBlockRenderer key={block.id} block={block} />
          ))}
        </div>
      )}
    </div>
  );
}
