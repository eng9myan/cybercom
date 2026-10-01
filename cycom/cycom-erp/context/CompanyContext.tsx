'use client';

import React, { createContext, useContext, useEffect, useMemo, useState, ReactNode } from 'react';

/**
 * The company / branch the user is working in, from real data:
 *  - companies: products.cycom.company (multi-company). Most tenants have
 *    none defined -- then the tenant itself is the one company (legal name
 *    and currency from the tenant profile / country pack).
 *  - branches: the tenant's real warehouses / store locations.
 * The selection is remembered per browser. (This used to be a hard-coded
 * list of four invented companies with invented store names.)
 */

export interface Company {
  id: string;
  name: string;
  shortName: string;
  type: 'retail' | 'commercial' | 'factory';
  currency: string;
  branches?: string[];
  color: string;
  icon: string;
}

interface CompanyContextValue {
  activeCompany: Company;
  setActiveCompany: (company: Company) => void;
  allCompanies: Company[];
  activeBranch: string | null;
  setActiveBranch: (branch: string | null) => void;
  loading: boolean;
}

const PALETTE = ['#3B82F6', '#10B981', '#EF4444', '#8B5CF6', '#E67E22', '#06B6D4'];
const STORE_KEY = 'cycom.activeCompany';
const BRANCH_KEY = 'cycom.activeBranch';

const PLACEHOLDER: Company = { id: 'tenant', name: '', shortName: '', type: 'commercial', currency: '', color: PALETTE[0], icon: '🏢' };

function shortName(name: string): string {
  const words = name.replace(/\b(LLC|Ltd\.?|S\.?r\.?l\.?|S\.?A\.?|GmbH|AS|Inc\.?|Co\.?)\b/gi, '').trim().split(/\s+/);
  return words.slice(0, 2).join(' ') || name;
}

async function getJson(url: string) {
  try {
    const r = await fetch(url, { credentials: 'include' });
    return r.ok ? await r.json() : null;
  } catch {
    return null;
  }
}

function read(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}

function write(key: string, value: string | null) {
  try {
    if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value);
  } catch { /* storage blocked -- selection lasts for this page only */ }
}

const CompanyContext = createContext<CompanyContextValue | undefined>(undefined);

export function CompanyProvider({ children }: { children: ReactNode }) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [activeBranch, setActiveBranchState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [status, companyData, warehouseData] = await Promise.all([
        getJson('/api/cycom/rest/common/system-status/'),
        getJson('/api/cycom/rest/company/companies/'),
        getJson('/api/cycom/rest/inventory/warehouses/'),
      ]);
      const warehouses: { name: string; is_active?: boolean }[] =
        (Array.isArray(warehouseData) ? warehouseData : warehouseData?.results) || [];
      const branches = warehouses.filter((w) => w.is_active !== false).map((w) => w.name);
      const rows: { id: string; name: string; currency: string; is_active?: boolean }[] =
        ((Array.isArray(companyData) ? companyData : companyData?.results) || []).filter((c: { is_active?: boolean }) => c.is_active !== false);

      const list: Company[] = rows.length
        ? rows.map((c, i) => ({
            id: c.id, name: c.name, shortName: shortName(c.name), type: 'commercial', currency: c.currency,
            branches, color: PALETTE[i % PALETTE.length], icon: '🏢',
          }))
        : [{
            id: 'tenant', name: status?.company?.name || '', shortName: shortName(status?.company?.name || ''),
            type: 'commercial', currency: status?.company?.currency || '', branches, color: PALETTE[0], icon: '🏢',
          }];
      setCompanies(list);
      const saved = read(STORE_KEY);
      setActiveId(list.some((c) => c.id === saved) ? saved : list[0].id);
      const savedBranch = read(BRANCH_KEY);
      setActiveBranchState(savedBranch && branches.includes(savedBranch) ? savedBranch : null);
      setLoading(false);
    })();
  }, []);

  const activeCompany = useMemo(
    () => companies.find((c) => c.id === activeId) || companies[0] || PLACEHOLDER,
    [companies, activeId],
  );

  const value: CompanyContextValue = {
    activeCompany,
    setActiveCompany: (c) => { setActiveId(c.id); write(STORE_KEY, c.id); },
    allCompanies: companies,
    activeBranch,
    setActiveBranch: (b) => { setActiveBranchState(b); write(BRANCH_KEY, b); },
    loading,
  };
  return <CompanyContext.Provider value={value}>{children}</CompanyContext.Provider>;
}

export function useCompany() {
  const ctx = useContext(CompanyContext);
  if (!ctx) {
    throw new Error('useCompany must be used within CompanyProvider');
  }
  return ctx;
}
