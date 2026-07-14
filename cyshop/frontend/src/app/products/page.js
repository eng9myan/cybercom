'use client';

import { useState } from 'react';
import Link from 'next/link';
import { 
  ArrowLeft, ShoppingBag, Package, ChefHat, ReceiptText, Users, 
  BarChart3, ShieldCheck, Heart, Truck, Check, HelpCircle
} from 'lucide-react';

export default function ProductsPage() {
  const [selectedModule, setSelectedModule] = useState('pos');

  const modules = {
    pos: {
      title: 'POS & Retail Checkout',
      tagline: 'Fast, Offline-First Checkouts',
      desc: 'The CYShop POS is designed for high-volume sweeps and bakery shops. Running on touchscreens, tablets, or mobiles, it guarantees uptime even during internet outages.',
      features: [
        'Offline transaction caching using IndexedDB',
        'Automatic synchronization on network restore',
        'Dual-language Arabic/English receipts format',
        'Integrated barcode scanners & card readers (CliQ, MEPS)',
        'Kitchen Display System (KDS) live sync'
      ]
    },
    inventory: {
      title: 'Inventory & Warehousing',
      tagline: 'Multi-Branch Batch Scoping',
      desc: 'Keep track of ingredients, raw materials, and finished goods across all warehouses and retail shelves. Automatically matches barcodes and flags expiry dates.',
      features: [
        'Batch tracking & expiry control rules',
        'First-Expired-First-Out (FEFO) automated picking',
        'Dynamic minimum reorder points alerts',
        'Inter-branch stock transfers validation',
        'GS1 barcode generation and scanning'
      ]
    },
    manufacturing: {
      title: 'Manufacturing & Recipes',
      tagline: 'Multi-Level BOM Yield Optimizations',
      desc: 'Designed for sweets and bakery production. Turn raw ingredients into packaged items with exact costing, waste calculations, and batch yields tracking.',
      features: [
        'Multi-level and Phantom Bills of Materials (BOM)',
        'Batch actual costing vs standard recipe cost',
        'Automated yield & scrap loss ratio tracking',
        'Work center capacity & scheduling (OEE)',
        'Biometric raw materials release validation'
      ]
    },
    accounting: {
      title: 'Accounting & Finance',
      tagline: 'Double-Entry Compliance Ledger',
      desc: 'Automatically generate income statements, balance sheets, and tax reports from everyday checkout sales and procurement purchases.',
      features: [
        'Double-entry bookkeeping balancing validations',
        'JoFotara SOAP/WSDL instant tax reporting',
        'ZATCA Phase 2 cryptographically signed e-invoices',
        'Automated bank feed reconciliations',
        'Accounts receivable/payable ageing trackers'
      ]
    },
    hr: {
      title: 'HR & Payroll Withholding',
      tagline: 'Localized Social Security & Wages Protection',
      desc: 'Manage employee shifts, attendance geofencing, and automated salary structures built for Jordan (SSC), Saudi Arabia (GOSI), and UAE (WPS).',
      features: [
        'Biometric shift attendance validation',
        'Wages Protection System (WPS) SIF file generator',
        'Localized payroll calculations for SSC/GOSI contributions',
        'Geofenced mobile check-in/out options',
        'Automated vacation and leave tracking engine'
      ]
    }
  };

  return (
    <div className="min-h-screen bg-white text-brand-dark selection:bg-brand-orange/20 selection:text-brand-orange">
      {/* Header */}
      <header className="border-b border-gray-100 py-6 bg-gray-50/50">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-sm font-bold text-gray-500 hover:text-brand-orange transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to Home
          </Link>
          <span className="font-lato font-black text-lg tracking-tight">CYShop Modules</span>
        </div>
      </header>

      {/* Main Grid */}
      <main className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center flex flex-col gap-4 mb-16">
          <span className="text-xs font-bold uppercase tracking-widest text-brand-orange">Platform Features</span>
          <h1 className="font-lato font-black text-3xl sm:text-5xl text-brand-dark">Detailed Product Features</h1>
          <p className="text-gray-500 max-w-xl mx-auto">Explore the tools built to streamline your business from raw materials manufacturing to POS retail checkout.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          {/* Left Navigation */}
          <div className="lg:col-span-4 bg-gray-50 border border-gray-100 rounded-2xl p-4 flex flex-col gap-2">
            {[
              { id: 'pos', icon: <ShoppingBag className="w-4 h-4" />, name: 'POS & Retail' },
              { id: 'inventory', icon: <Package className="w-4 h-4" />, name: 'Inventory & Warehousing' },
              { id: 'manufacturing', icon: <ChefHat className="w-4 h-4" />, name: 'Manufacturing & Recipes' },
              { id: 'accounting', icon: <ReceiptText className="w-4 h-4" />, name: 'Accounting & Finance' },
              { id: 'hr', icon: <Users className="w-4 h-4" />, name: 'HR & Payroll' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setSelectedModule(tab.id)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold text-left transition-all ${
                  selectedModule === tab.id 
                    ? 'bg-brand-dark text-white shadow-md' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {tab.icon} {tab.name}
              </button>
            ))}
          </div>

          {/* Right Detail Box */}
          <div className="lg:col-span-8 bg-white border border-gray-150 rounded-2xl p-8 shadow-sm flex flex-col gap-6">
            <div className="flex flex-col gap-1">
              <span className="text-xs font-bold text-brand-orange uppercase tracking-wider">
                {modules[selectedModule].tagline}
              </span>
              <h2 className="font-lato font-black text-2xl text-brand-dark">
                {modules[selectedModule].title}
              </h2>
            </div>
            
            <p className="text-gray-600 text-sm leading-relaxed">
              {modules[selectedModule].desc}
            </p>

            <div className="flex flex-col gap-3 pt-4 border-t border-gray-100">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Core Capabilities Include:</span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {modules[selectedModule].features.map((feat, idx) => (
                  <div key={idx} className="flex items-center gap-3 text-xs font-bold text-gray-700">
                    <Check className="w-4 h-4 text-brand-orange flex-shrink-0" /> {feat}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer banner */}
      <section className="bg-brand-dark text-white py-16 text-center">
        <div className="max-w-2xl mx-auto flex flex-col gap-6 px-6">
          <h2 className="font-lato font-black text-2xl sm:text-3xl">Ready to test these features?</h2>
          <p className="text-gray-400 text-sm">Provision a free sandbox environment and try all core capabilities live.</p>
          <Link href="/#trial" className="self-center px-8 py-3.5 rounded-xl font-bold bg-brand-orange text-white hover:bg-brand-orange/95 transition-all">
            Launch Tenant Sandbox
          </Link>
        </div>
      </section>
    </div>
  );
}
