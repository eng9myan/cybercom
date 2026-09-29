'use client';

/**
 * Global command palette (Ctrl/Cmd+K).
 *
 * With ~56 modules, "where is that screen" is the real usability problem in
 * this product -- menu depth grows faster than anyone's memory. A palette
 * turns navigation into one keystroke plus a few letters, which beats
 * hunting through a sidebar every time.
 *
 * Matching is subsequence-based ("por" matches "Purchase ORders") with a
 * scoring bias toward prefix and word-start hits, so short queries land on
 * the obvious thing rather than something buried.
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, CornerDownLeft, ArrowUp, ArrowDown, Command } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface Entry {
  href: string;
  label: string;
  group: string;
  keywords?: string;
}

const RECENT_KEY = 'cycom.palette.recent';
const MAX_RECENT = 5;

/** Subsequence match with a score; null when it doesn't match at all.
 *  Exported for tests -- the ranking is the part that decides whether a
 *  two-letter query lands on the right screen. */
export function score(query: string, text: string): number | null {
  const q = query.toLowerCase().trim();
  const s = text.toLowerCase();
  if (!q) return 0;
  if (s.startsWith(q)) return 1000 - s.length;
  const wordStart = s.split(/[\s/&—-]+/).some((w) => w.startsWith(q));
  if (s.includes(q)) return (wordStart ? 700 : 500) - s.length;

  let si = 0;
  let hits = 0;
  for (const ch of q) {
    const found = s.indexOf(ch, si);
    if (found === -1) return null;
    if (found === si) hits += 1;
    si = found + 1;
  }
  return 200 + hits - s.length;
}

export default function CommandPalette() {
  const t = useT();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [active, setActive] = useState(0);
  const [recent, setRecent] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const ENTRIES: Entry[] = useMemo(() => [
    // Operations
    { href: '/sales', label: t('appLauncher.modSales'), group: t('palette.groupOperations'), keywords: 'orders quotes customers revenue' },
    { href: '/pos', label: t('appLauncher.modPos'), group: t('palette.groupOperations'), keywords: 'till checkout register cashier' },
    { href: '/purchase', label: t('appLauncher.modPurchase'), group: t('palette.groupOperations'), keywords: 'vendors suppliers procurement po' },
    { href: '/purchase/vendors', label: t('palette.vendors'), group: t('palette.groupOperations'), keywords: 'suppliers onboarding' },
    { href: '/inventory', label: t('appLauncher.modInventory'), group: t('palette.groupOperations'), keywords: 'stock warehouse products' },
    { href: '/inventory/warehouse-map', label: t('warehouseMap.title'), group: t('palette.groupOperations'), keywords: 'bins zones aisles racks layout' },
    { href: '/inventory/transfers', label: t('palette.transfers'), group: t('palette.groupOperations'), keywords: 'stock move between warehouses' },
    { href: '/project', label: t('appLauncher.modProject'), group: t('palette.groupOperations'), keywords: 'tasks kanban board' },
    { href: '/project/gantt', label: t('gantt.title'), group: t('palette.groupOperations'), keywords: 'schedule critical path timeline' },
    { href: '/helpdesk', label: t('appLauncher.modHelpdesk'), group: t('palette.groupOperations'), keywords: 'tickets support sla' },
    { href: '/fleet', label: t('appLauncher.modFleet'), group: t('palette.groupOperations'), keywords: 'vehicles maintenance fuel' },
    { href: '/plm', label: t('appLauncher.modPlm'), group: t('palette.groupOperations'), keywords: 'engineering change eco' },

    // Finance
    { href: '/accounting', label: t('appLauncher.modAccounting'), group: t('palette.groupFinance'), keywords: 'ledger journals gl' },
    { href: '/accounting/journals', label: t('palette.journals'), group: t('palette.groupFinance'), keywords: 'entries posting' },
    { href: '/accounting/invoices', label: t('invoices.title'), group: t('palette.groupFinance'), keywords: 'bills ar ap vendor customer receivable payable' },
    { href: '/accounting/vat-mtd', label: t('vatMtd.title'), group: t('palette.groupFinance'), keywords: 'hmrc mtd vat return uk making tax digital' },
    { href: '/accounting/saft', label: t('saft.title'), group: t('palette.groupFinance'), keywords: 'saf-t audit file norway skatteetaten export' },
    { href: '/accounting/reconciliation', label: t('accountingReconciliation.title'), group: t('palette.groupFinance'), keywords: 'bank statement match' },
    { href: '/payroll', label: t('appLauncher.modPayroll'), group: t('palette.groupFinance'), keywords: 'salary payslip wages' },
    { href: '/payroll/deductions', label: t('palette.deductions'), group: t('palette.groupFinance'), keywords: 'lateness absence' },
    { href: '/custom-reports', label: t('palette.customReports'), group: t('palette.groupFinance'), keywords: 'bi analytics pivot chart' },

    // People
    { href: '/hr', label: t('appLauncher.modHr'), group: t('palette.groupPeople'), keywords: 'employees staff' },
    { href: '/hr/documents', label: t('palette.hrDocuments'), group: t('palette.groupPeople'), keywords: 'passport iqama expiry' },
    { href: '/hr/insurance', label: t('palette.hrInsurance'), group: t('palette.groupPeople'), keywords: 'medical health cover' },
    { href: '/attendance', label: t('appLauncher.modAttendance'), group: t('palette.groupPeople'), keywords: 'clock in out biometric' },
    { href: '/recruitment', label: t('appLauncher.modRecruitment'), group: t('palette.groupPeople'), keywords: 'hiring applicants jobs' },

    // Growth
    { href: '/crm', label: t('palette.crm'), group: t('palette.groupGrowth'), keywords: 'leads pipeline deals' },
    { href: '/marketing', label: t('appLauncher.modMarketing'), group: t('palette.groupGrowth'), keywords: 'campaigns email sms' },
    { href: '/cms', label: t('palette.cms'), group: t('palette.groupGrowth'), keywords: 'website builder pages' },

    // Workspace
    { href: '/discuss', label: t('appLauncher.modDiscuss'), group: t('palette.groupWorkspace'), keywords: 'chat channels messages' },
    { href: '/documents', label: t('appLauncher.modDocuments'), group: t('palette.groupWorkspace'), keywords: 'files attachments' },
    { href: '/documents/ai-parse', label: t('documentsPage.aiParseLink'), group: t('palette.groupWorkspace'), keywords: 'ai document parse invoice ocr extract' },
    { href: '/sign', label: t('appLauncher.modSign'), group: t('palette.groupWorkspace'), keywords: 'esignature signature' },
    { href: '/approvals', label: t('palette.approvals'), group: t('palette.groupWorkspace'), keywords: 'hitl review queue authorise' },

    // Configure
    { href: '/automation', label: t('automation.title'), group: t('palette.groupConfigure'), keywords: 'rules triggers workflow no-code' },
    { href: '/setup', label: t('appLauncher.modSetup'), group: t('palette.groupConfigure'), keywords: 'wizard onboarding' },
    { href: '/settings', label: t('appLauncher.modSettings'), group: t('palette.groupConfigure'), keywords: 'preferences configuration' },
    { href: '/settings/security', label: t('settingsSecurity.title'), group: t('palette.groupConfigure'), keywords: 'sso audit chain' },
    { href: '/settings/modules', label: t('settingsModules.title'), group: t('palette.groupConfigure'), keywords: 'apps installed' },
    { href: '/settings/tax', label: t('settingsTax.title'), group: t('palette.groupConfigure'), keywords: 'vat wht calculator' },
  ], [t]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(RECENT_KEY);
      if (raw) setRecent(JSON.parse(raw));
    } catch {
      // private mode / blocked storage -- recents are a convenience, not state
    }
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
        setQuery('');
        setActive(0);
      } else if (e.key === 'Escape') {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 10);
  }, [open]);

  const results = useMemo(() => {
    if (!query.trim()) {
      const recentEntries = recent
        .map((href) => ENTRIES.find((e) => e.href === href))
        .filter((e): e is Entry => Boolean(e))
        .map((e) => ({ ...e, group: t('palette.groupRecent') }));
      const rest = ENTRIES.filter((e) => !recent.includes(e.href));
      return [...recentEntries, ...rest].slice(0, 40);
    }
    return ENTRIES
      .map((e) => {
        const best = Math.max(
          score(query, e.label) ?? -Infinity,
          (score(query, e.keywords || '') ?? -Infinity) - 100,
          (score(query, e.group) ?? -Infinity) - 200,
        );
        return { entry: e, s: best };
      })
      .filter((r) => r.s > -Infinity)
      .sort((a, b) => b.s - a.s)
      .slice(0, 30)
      .map((r) => r.entry);
  }, [query, ENTRIES, recent, t]);

  useEffect(() => { setActive(0); }, [query]);

  const go = useCallback((entry: Entry) => {
    const next = [entry.href, ...recent.filter((h) => h !== entry.href)].slice(0, MAX_RECENT);
    setRecent(next);
    try {
      localStorage.setItem(RECENT_KEY, JSON.stringify(next));
    } catch {
      // ignore -- see above
    }
    setOpen(false);
    router.push(entry.href);
  }, [recent, router]);

  const onInputKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && results[active]) {
      e.preventDefault();
      go(results[active]);
    }
  };

  useEffect(() => {
    listRef.current?.querySelector('[data-active="true"]')?.scrollIntoView({ block: 'nearest' });
  }, [active]);

  if (!open) return null;

  let lastGroup = '';

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[12vh] bg-slate-950/70 backdrop-blur-sm"
      onClick={() => setOpen(false)}
    >
      <div
        className="w-full max-w-xl mx-4 bg-slate-900 border border-slate-700/60 rounded-2xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={t('palette.title')}
      >
        <div className="flex items-center gap-3 px-4 py-3 border-b border-white/5">
          <Search className="w-4 h-4 text-slate-500 flex-shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onInputKey}
            placeholder={t('palette.placeholder')}
            className="flex-1 bg-transparent outline-none text-slate-100 placeholder:text-slate-600 text-sm"
          />
          <kbd className="text-[10px] text-slate-500 border border-slate-700 rounded px-1.5 py-0.5">esc</kbd>
        </div>

        <div ref={listRef} className="max-h-[50vh] overflow-y-auto py-2">
          {results.length === 0 && (
            <div className="px-4 py-8 text-center text-slate-500 text-xs">
              {t('palette.noResults', { q: query })}
            </div>
          )}
          {results.map((entry, i) => {
            const showGroup = entry.group !== lastGroup;
            lastGroup = entry.group;
            return (
              <React.Fragment key={`${entry.href}-${i}`}>
                {showGroup && (
                  <div className="px-4 pt-3 pb-1 text-[10px] uppercase tracking-widest text-slate-600 font-bold">
                    {entry.group}
                  </div>
                )}
                <button
                  data-active={i === active}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => go(entry)}
                  className={`w-full text-start px-4 py-2 flex items-center justify-between gap-3 transition ${
                    i === active ? 'bg-blue-600/20 text-white' : 'text-slate-300 hover:bg-white/5'
                  }`}
                >
                  <span className="truncate">{entry.label}</span>
                  <span className="text-[10px] text-slate-600 font-mono truncate flex-shrink-0" dir="ltr">
                    {entry.href}
                  </span>
                </button>
              </React.Fragment>
            );
          })}
        </div>

        <div className="flex items-center gap-4 px-4 py-2 border-t border-white/5 text-[10px] text-slate-600">
          <span className="flex items-center gap-1"><ArrowUp className="w-3 h-3" /><ArrowDown className="w-3 h-3" /> {t('palette.hintNavigate')}</span>
          <span className="flex items-center gap-1"><CornerDownLeft className="w-3 h-3" /> {t('palette.hintOpen')}</span>
          <span className="flex items-center gap-1 ms-auto"><Command className="w-3 h-3" /> {t('palette.hintToggle')}</span>
        </div>
      </div>
    </div>
  );
}
