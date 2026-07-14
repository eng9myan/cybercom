'use client';

import React, { useState, useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Search, Terminal, Settings, Users, FolderKanban } from 'lucide-react';
import { useRouter } from 'next/navigation';

export function CyCommandBar() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const navigateTo = (path: string) => {
    setOpen(false);
    router.push(path);
  };

  const COMMANDS = [
    { label: 'Run Smart Setup Wizard', path: '/setup', icon: Settings, color: 'text-purple-400' },
    { label: 'Open Employee Directory', path: '/hr/employees', icon: Users, color: 'text-cyan-400' },
    { label: 'View Project Kanban', path: '/project', icon: FolderKanban, color: 'text-emerald-400' },
  ];

  const filtered = COMMANDS.filter((cmd) =>
    cmd.label.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-md z-50" />
        <Dialog.Content
          className="
            fixed top-[20%] left-[50%] translate-x-[-50%] w-full max-w-lg
            bg-[#0C0F1A]/95 border border-white/10 rounded-2xl p-4 shadow-2xl z-50
            text-slate-200 focus:outline-none
          "
        >
          <div className="flex items-center gap-3 border-b border-white/10 pb-3 mb-3">
            <Search className="w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search menus, apps, and actions..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="bg-transparent border-none outline-none w-full text-sm text-white placeholder-slate-500"
              autoFocus
            />
            <kbd className="text-[10px] bg-white/5 border border-white/10 px-2 py-0.5 rounded text-slate-400 font-mono">ESC</kbd>
          </div>

          <div className="space-y-1">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">
              Actions
            </h3>
            {filtered.map((cmd, idx) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={idx}
                  onClick={() => navigateTo(cmd.path)}
                  className="
                    w-full text-left text-xs p-2.5 rounded-xl hover:bg-white/5
                    flex items-center gap-3 transition-all hover:translate-x-0.5
                  "
                >
                  <Icon className={`w-4 h-4 ${cmd.color}`} />
                  <span>{cmd.label}</span>
                </button>
              );
            })}
            {filtered.length === 0 && (
              <p className="text-xs text-slate-500 p-2 text-center">No commands match your query.</p>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
