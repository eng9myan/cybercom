'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowLeft, Check, HelpCircle } from 'lucide-react';

export default function PricingPage() {
  const [country, setCountry] = useState('JO');
  const [branches, setBranches] = useState(1);
  const [users, setUsers] = useState(3);
  const [calculatedPrice, setCalculatedPrice] = useState(19);
  const [selectedPlan, setSelectedPlan] = useState('Starter');

  useEffect(() => {
    let basePrice = 19;
    let plan = 'Starter';

    if (branches > 25 || users > 100) {
      plan = 'Enterprise';
      setCalculatedPrice('Custom');
      setSelectedPlan(plan);
      return;
    }

    if (branches > 5 || users > 20) {
      plan = 'Business';
      basePrice = 199;
    } else if (branches > 1 || users > 5) {
      plan = 'Growth';
      basePrice = 59;
    }

    let multiplier = 1;
    if (country === 'SA') multiplier = 5.29; 
    if (country === 'AE') multiplier = 5.18; 

    if (typeof basePrice === 'number') {
      const finalPrice = Math.round(basePrice * multiplier);
      setCalculatedPrice(finalPrice);
    }
    
    setSelectedPlan(plan);
  }, [country, branches, users]);

  return (
    <div className="min-h-screen bg-white text-brand-dark selection:bg-brand-orange/20 selection:text-brand-orange">
      {/* Header */}
      <header className="border-b border-gray-100 py-6 bg-gray-50/50">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-sm font-bold text-gray-500 hover:text-brand-orange transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to Home
          </Link>
          <span className="font-lato font-black text-lg tracking-tight">SaaS Subscription Plans</span>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center flex flex-col gap-4 mb-16">
          <span className="text-xs font-bold uppercase tracking-widest text-brand-orange">Honest, Scalable Pricing</span>
          <h1 className="font-lato font-black text-3xl sm:text-5xl text-brand-dark">Simple Plans For Every Stage</h1>
          <p className="text-gray-500 max-w-xl mx-auto">Choose a plan that fits your business scale. Dynamic currency display for Jordan, Saudi Arabia, and UAE.</p>
        </div>

        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-24">
          {[
            { name: 'Starter', price: { JO: '19 JOD', SA: '99 SAR', AE: '99 AED' }, scale: '1 Store, Up to 5 Users', features: ['Core retail POS checkout', 'Basic inventory records', 'Standard sales reports', 'CSV data importing tools', 'Community support access'] },
            { name: 'Growth', price: { JO: '59 JOD', SA: '299 SAR', AE: '299 AED' }, scale: 'Up to 5 Stores, 20 Users', features: ['Multi-branch inventory sync', 'Bakery recipe management', 'Social Security contributions', 'Wages Protection files', 'Standard email support', 'API data integrations'] },
            { name: 'Business', price: { JO: '199 JOD', SA: '999 SAR', AE: '999 AED' }, scale: 'Up to 25 Stores, 100 Users', features: ['ZATCA e-invoicing Phase 2', 'JoFotara SOAP real-time reporting', 'Multi-level factory BOM costing', 'Full warehouse operations (WMS)', 'Premium phone & chat support', 'Predictive AI Forecasting'] },
            { name: 'Enterprise', price: { JO: 'Custom', SA: 'Custom', AE: 'Custom' }, scale: 'Unlimited Scale & Branches', features: ['Dedicated database cluster', 'Custom ERP integrations', 'Level 3 hotline engineer SLA', 'Biometric SSO access tools', 'On-site user training courses', 'Dedicated customer success'] }
          ].map((plan, idx) => (
            <div key={idx} className={`border border-gray-150 rounded-2xl p-8 flex flex-col gap-6 relative bg-white shadow-sm ${plan.name === selectedPlan ? 'border-brand-orange ring-1 ring-brand-orange' : ''}`}>
              {plan.name === selectedPlan && (
                <span className="absolute top-0 right-6 -translate-y-1/2 bg-brand-orange text-white text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full">
                  Your Fit
                </span>
              )}
              <div className="flex flex-col gap-1">
                <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">{plan.name}</span>
                <span className="text-2xl font-black text-brand-dark">{plan.price[country]}</span>
                <span className="text-xs text-gray-500">{plan.scale}</span>
              </div>

              <div className="flex flex-col gap-3 pt-6 border-t border-gray-100 flex-1">
                {plan.features.map((feat, fIdx) => (
                  <div key={fIdx} className="flex items-center gap-2 text-xs text-gray-600 font-bold">
                    <Check className="w-4 h-4 text-brand-orange flex-shrink-0" /> {feat}
                  </div>
                ))}
              </div>

              <Link href="/#trial" className={`w-full py-3 rounded-xl text-center font-bold text-xs transition-all ${
                plan.name === selectedPlan 
                  ? 'bg-brand-orange text-white hover:bg-brand-orange/95 shadow-md shadow-brand-orange/10' 
                  : 'bg-brand-dark text-white hover:bg-brand-dark/95'
              }`}>
                Select Plan
              </Link>
            </div>
          ))}
        </div>

        {/* Live pricing calculator segment */}
        <div className="bg-gray-50 border border-gray-150 rounded-2xl p-8 lg:p-12">
          <h3 className="font-lato font-bold text-xl mb-8 text-brand-dark text-center">Interactive Calculator</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
            {/* Target country */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-bold text-gray-500 uppercase">Country</label>
              <select 
                value={country} 
                onChange={e => setCountry(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-3 text-sm font-semibold outline-none"
              >
                <option value="JO">Jordan</option>
                <option value="SA">Saudi Arabia</option>
                <option value="AE">UAE</option>
              </select>
            </div>
            {/* Branches count */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-bold text-gray-500 uppercase">Branches Count ({branches})</label>
              <input 
                type="range" 
                min="1" 
                max="30" 
                value={branches} 
                onChange={e => setBranches(Number(e.target.value))}
                className="w-full accent-brand-orange"
              />
            </div>
            {/* Users count */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-bold text-gray-500 uppercase">Users Count ({users})</label>
              <input 
                type="range" 
                min="1" 
                max="120" 
                value={users} 
                onChange={e => setUsers(Number(e.target.value))}
                className="w-full accent-brand-orange"
              />
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-gray-200 flex justify-between items-center">
            <div>
              <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Calculated Monthly SaaS Charge</span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-brand-orange">{typeof calculatedPrice === 'number' ? calculatedPrice.toLocaleString() : calculatedPrice}</span>
                <span className="text-xs font-bold text-gray-500">{typeof calculatedPrice === 'number' ? (country === 'JO' ? 'JOD' : country === 'SA' ? 'SAR' : 'AED') : ''}</span>
              </div>
            </div>
            <Link href="/#trial" className="px-6 py-3 rounded-lg font-bold text-xs bg-brand-dark text-white hover:bg-brand-dark/95 transition-all">
              Launch Tenant
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
