'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, ChefHat, Store, Truck, ShoppingBag, Sparkles, Check } from 'lucide-react';

export default function IndustriesPage() {
  const [selectedIndustry, setSelectedIndustry] = useState('sweets');

  const industriesList = {
    sweets: {
      title: 'Sweets & Bakery Manufacturing',
      icon: <ChefHat className="w-8 h-8 text-brand-orange" />,
      desc: 'Formulated for multi-level Sweets (Pistachio Cake, Maamoul, Baklava) recipes. Connects raw ingredient yields in the factory with real-time cashier checkouts at retail branches.',
      features: [
        'Multi-level phantom recipe bills of materials',
        'Automatic ingredient deduction on POS sale write',
        'Batch tracking with shelf-life/expiry limits',
        'Raw material wastage analysis logs',
        'Actual costing tracking vs standard recipe estimates'
      ]
    },
    restaurants: {
      title: 'Restaurants & Fast Food',
      icon: <ShoppingBag className="w-8 h-8 text-brand-blue" />,
      desc: 'Optimized for high-concurrency order taking, integrated delivery marketplace sync loops (Talabat, Careem), and live KDS monitors in the kitchen.',
      features: [
        'Live kitchen display ticketing sync loops',
        'Talabat, Careem, and Jahez normalized order routing',
        'Table layouts configuration and order split checkouts',
        'Dynamic modifiers and ingredient cost allocations',
        'Loyalty wallets integration'
      ]
    },
    retail: {
      title: 'Retail Stores & Franchises',
      icon: <Store className="w-8 h-8 text-purple-600" />,
      desc: 'Keep thousands of products aligned. Designed for multi-branch retail networks requiring central master catalogs, barcodes scanners, and localized payments.',
      features: [
        'Central product catalog metadata sync',
        'Fast barcode generation and scanner compatibility',
        'Mada, STC Pay, CliQ, and HyperPay checkout integrations',
        'Multi-branch promotions matching systems',
        'Inventory reorder point alerts'
      ]
    },
    distribution: {
      title: 'Distribution & Warehouse Logistics',
      icon: <Truck className="w-8 h-8 text-green-600" />,
      desc: 'Scale bulk shipping and warehouse pickups. Track stock locations (pick, pack, ship) and driver tasks from a single dashboard.',
      features: [
        'Bin location mappings and stock transfers',
        'Landed cost calculations for foreign purchase receipts',
        'Driver proof of delivery checks on mobile apps',
        'GS1-128 barcode check-ins',
        'Reconciliation with double-entry ledgers'
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
          <span className="font-lato font-black text-lg tracking-tight">Industry Packs</span>
        </div>
      </header>

      {/* Main section */}
      <main className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center flex flex-col gap-4 mb-16">
          <span className="text-xs font-bold uppercase tracking-widest text-brand-orange">Tailored Industry Packs</span>
          <h1 className="font-lato font-black text-3xl sm:text-5xl text-brand-dark">Built For Your Specific Vertical</h1>
          <p className="text-gray-500 max-w-xl mx-auto">No generic workflows. Load specialized configurations containing specific DDL profiles, tax rules, and user roles.</p>
        </div>

        {/* Tab Selection */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-12">
          {Object.keys(industriesList).map(key => (
            <button
              key={key}
              onClick={() => setSelectedIndustry(key)}
              className={`px-6 py-3 rounded-xl text-sm font-bold transition-all ${
                selectedIndustry === key 
                  ? 'bg-brand-orange text-white shadow-md shadow-brand-orange/15' 
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
              }`}
            >
              {industriesList[key].title.split(' & ')[0]}
            </button>
          ))}
        </div>

        {/* Selected Industry Detail */}
        <div className="max-w-4xl mx-auto bg-white border border-gray-150 rounded-3xl p-8 md:p-12 shadow-sm grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
          <div className="md:col-span-4 flex flex-col items-center md:items-start text-center md:text-left gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center shadow-inner">
              {industriesList[selectedIndustry].icon}
            </div>
            <h2 className="font-lato font-black text-xl text-brand-dark leading-tight">
              {industriesList[selectedIndustry].title}
            </h2>
          </div>

          <div className="md:col-span-8 flex flex-col gap-6 border-t md:border-t-0 md:border-l border-gray-100 pt-6 md:pt-0 md:pl-8">
            <p className="text-gray-600 text-sm leading-relaxed">
              {industriesList[selectedIndustry].desc}
            </p>

            <div className="flex flex-col gap-3">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Features Included:</span>
              <div className="grid grid-cols-1 gap-2.5">
                {industriesList[selectedIndustry].features.map((feat, idx) => (
                  <div key={idx} className="flex items-center gap-3 text-xs font-bold text-gray-700">
                    <Check className="w-4 h-4 text-brand-orange flex-shrink-0" /> {feat}
                  </div>
                ))}
              </div>
            </div>

            <Link href="/#trial" className="self-start px-6 py-3 bg-brand-dark text-white hover:bg-brand-dark/95 rounded-xl font-bold text-xs mt-2 transition-all">
              Try Sweets Pack Live
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
