'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

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

export const COMPANIES: Company[] = [
  {
    id: 'COM-001',
    name: 'Cycom Retail Co.',
    shortName: 'Retail',
    type: 'retail',
    currency: 'JOD',
    branches: [
      'Store 01 — Abdali Mall', 'Store 02 — Mecca Mall', 'Store 03 — City Mall',
      'Store 04 — Taj Mall', 'Store 05 — Galleria', 'Store 06 — Al-Baraka',
      'Store 07 — Zarqa Central', 'Store 08 — Irbid Branch', 'Store 09 — Aqaba Branch',
      'Store 10 — Salt Branch', 'Store 11 — Madaba Branch', 'Store 12 — Karak Branch',
      'Store 13 — Mafraq Branch', 'Store 14 — Jerash Branch', 'Store 15 — Ajloun Branch',
      'Store 16 — Tafila Branch', 'Store 17 — Maan Branch', 'Store 18 — Al-Balqa',
      'Store 19 — Sweileh Branch', 'Store 20 — Marj Al-Hamam', 'Store 21 — Abu Nseir',
      'Store 22 — Tabarbour', 'Store 23 — Al-Hashmi'
    ],
    color: '#EF4444',
    icon: '🏪'
  },
  {
    id: 'COM-002',
    name: 'Cycom Commercial & HQ',
    shortName: 'Head Office',
    type: 'commercial',
    currency: 'JOD',
    color: '#3B82F6',
    icon: '🏢'
  },
  {
    id: 'COM-003',
    name: 'Cycom Manufacturing Co.',
    shortName: 'Factory',
    type: 'factory',
    currency: 'JOD',
    color: '#10B981',
    icon: '🏭'
  },
  {
    id: 'COM-004',
    name: 'CyberCom Group (HQ)',
    shortName: 'CyberCom',
    type: 'retail',
    currency: 'JOD',
    branches: [
      'Amman Showroom — Car Terminal',
      'Amman Showroom — Café POS',
      'Amman Showroom — Restaurant POS',
      'Amman Showroom — Supermarket POS',
      'Dubai Showroom — Car Terminal',
      'Dubai Showroom — Café POS',
      'Dubai Showroom — Restaurant POS',
      'Dubai Showroom — Supermarket POS',
      'Riyadh Showroom — Car Terminal',
      'Riyadh Showroom — Café POS',
      'Riyadh Showroom — Restaurant POS',
      'Riyadh Showroom — Supermarket POS',
      'Factory — CyberCom Car Factory',
      'Distributor 01 — Germany HQ',
      'Distributor 02 — USA East',
      'Distributor 03 — UK Logistics',
      'Distributor 04 — Japan Hub',
      'Distributor 05 — Canada Warehouse',
      'Distributor 06 — France Center',
      'Distributor 07 — Australia Depot',
      'Distributor 08 — China Hub',
      'Distributor 09 — Saudi Logistics',
      'Distributor 10 — Egypt Warehouse'
    ],
    color: '#8B5CF6',
    icon: '🚗'
  }
];

interface CompanyContextValue {
  activeCompany: Company;
  setActiveCompany: (company: Company) => void;
  allCompanies: Company[];
  activeBranch: string | null;
  setActiveBranch: (branch: string | null) => void;
}

const CompanyContext = createContext<CompanyContextValue | undefined>(undefined);

export function CompanyProvider({ children }: { children: ReactNode }) {
  const [activeCompany, setActiveCompany] = useState<Company>(COMPANIES[1]); // Default to HQ
  const [activeBranch, setActiveBranch] = useState<string | null>(null);

  return (
    <CompanyContext.Provider value={{
      activeCompany,
      setActiveCompany,
      allCompanies: COMPANIES,
      activeBranch,
      setActiveBranch,
    }}>
      {children}
    </CompanyContext.Provider>
  );
}

export function useCompany() {
  const ctx = useContext(CompanyContext);
  if (!ctx) {
    throw new Error('useCompany must be used within CompanyProvider');
  }
  return ctx;
}
