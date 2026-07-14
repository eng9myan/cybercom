'use client';

import React, { useState, useRef, UIEvent } from 'react';

export interface ColumnDefinition<T> {
  key: string;
  header: string;
  width?: string;
  render?: (row: T) => React.ReactNode;
}

interface CyDataGridProps<T> {
  data: T[];
  columns: ColumnDefinition<T>[];
  rowHeight?: number;
  viewportHeight?: number;
}

export function CyDataGrid<T extends { id: any }>({
  data,
  columns,
  rowHeight = 50,
  viewportHeight = 450,
}: CyDataGridProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const totalHeight = data.length * rowHeight;

  // Calculate visible range index with 3 buffer rows top and bottom
  const startIndex = Math.max(0, Math.floor(scrollTop / rowHeight) - 3);
  const endIndex = Math.min(data.length, Math.ceil((scrollTop + viewportHeight) / rowHeight) + 3);

  const visibleData = data.slice(startIndex, endIndex);

  const handleScroll = (e: UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  return (
    <div
      onScroll={handleScroll}
      className="overflow-y-auto border border-white/10 rounded-xl bg-black/40 backdrop-blur-md relative"
      style={{ height: viewportHeight }}
    >
      <div style={{ height: totalHeight, width: '100%', position: 'relative' }}>
        {/* Virtualized Table Container */}
        <table className="w-full text-left text-xs border-collapse" style={{ tableLayout: 'fixed' }}>
          <thead className="sticky top-0 bg-[#0A0D16] border-b border-white/10 text-slate-400 font-bold z-10">
            <tr style={{ height: rowHeight }}>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-4 py-3 font-semibold text-slate-300"
                  style={{ width: col.width || 'auto' }}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              transform: `translate3d(0, ${startIndex * rowHeight}px, 0)`,
            }}
          >
            {visibleData.map((row, rowIdx) => (
              <tr
                key={row.id ?? rowIdx}
                className="border-b border-white/5 hover:bg-white/5 transition-colors text-slate-200"
                style={{ height: rowHeight }}
              >
                {columns.map((col, colIdx) => (
                  <td key={colIdx} className="px-4 py-2 truncate">
                    {col.render ? col.render(row) : String(row[col.key as keyof T] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
