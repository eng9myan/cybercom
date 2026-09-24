import React from 'react';
import type { BlockNode } from '@/lib/cmsBlocks';

export default function PublicBlockRenderer({ block }: { block: BlockNode }) {
  const c = block.config || {};

  switch (block.block_type) {
    case 'section':
      return (
        <section style={{ background: c.background || 'transparent', padding: `${c.padding ?? 48}px 24px` }}>
          <div className="max-w-5xl mx-auto space-y-6">
            {block.children.map((child) => (
              <PublicBlockRenderer key={child.id} block={child} />
            ))}
          </div>
        </section>
      );
    case 'columns': {
      const count = Number(c.column_count) || 2;
      return (
        <div
          className="grid gap-6 max-w-5xl mx-auto px-6"
          style={{ gridTemplateColumns: `repeat(${count}, minmax(0, 1fr))` }}
        >
          {block.children.map((child) => (
            <PublicBlockRenderer key={child.id} block={child} />
          ))}
        </div>
      );
    }
    case 'heading': {
      const Tag = (`h${c.level || 2}`) as React.ElementType;
      return (
        <Tag className="font-black text-white" style={{ textAlign: c.align || 'start' }}>
          {c.text}
        </Tag>
      );
    }
    case 'text':
      return (
        <p className="text-slate-300 leading-relaxed whitespace-pre-wrap" style={{ textAlign: c.align || 'start' }}>
          {c.text}
        </p>
      );
    case 'image':
      return c.image_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={c.image_url} alt={c.alt || ''} className="w-full rounded-xl" />
      ) : null;
    case 'button':
      return (
        <a href={c.href || '#'} className="btn-primary inline-block py-2 px-5 text-sm">
          {c.label}
        </a>
      );
    case 'spacer':
      return <div style={{ height: `${c.height ?? 40}px` }} />;
    case 'video':
      return c.video_url ? (
        <div className="aspect-video w-full">
          <iframe src={c.video_url} className="w-full h-full rounded-xl" allowFullScreen />
        </div>
      ) : null;
    case 'html':
      // Custom-HTML is an authoring surface for staff only (creating/editing
      // blocks requires IsAuthenticatedViaClaims server-side) -- same trust
      // model as any CMS's "code" widget, not public input.
      return <div dangerouslySetInnerHTML={{ __html: c.html || '' }} />;
    default:
      return null;
  }
}
