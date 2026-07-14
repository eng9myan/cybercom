'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, Save, Building, ShieldCheck, CreditCard, 
  Phone, Upload, FileText, CheckCircle2, AlertCircle
} from 'lucide-react';
import { create } from '@/lib/cycom';

export default function RegisterVendor() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [step, setStep] = useState(1); // 1: Form, 2: Document Upload, 3: Success
  const [vendorId, setVendorId] = useState<number | null>(null);

  // Form Fields
  const [legalName, setLegalName] = useState('');
  const [legalNameAr, setLegalNameAr] = useState('');
  const [tradeName, setTradeName] = useState('');
  const [category, setCategory] = useState('goods'); // goods | services | both
  const [crNumber, setCrNumber] = useState('');
  const [crExpiry, setCrExpiry] = useState('');
  const [taxNumber, setTaxNumber] = useState('');
  
  // Bank Fields
  const [bankName, setBankName] = useState('');
  const [bankBranch, setBankBranch] = useState('');
  const [iban, setIban] = useState('');
  const [swiftCode, setSwiftCode] = useState('');
  const [creditLimit, setCreditLimit] = useState('');
  const [paymentTerms, setPaymentTerms] = useState(30);

  // Contact Fields
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');

  // Document Uploads State
  const [docs, setDocs] = useState<Record<string, File | null>>({
    cr: null,
    tax_certificate: null,
    bank_letter: null
  });
  const [uploadProgress, setUploadProgress] = useState<Record<string, string>>({});

  const handleFileChange = (type: string, file: File | null) => {
    setDocs({ ...docs, [type]: file });
  };

  // Submit vendor profile
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!legalName) {
      alert('Legal Name is required.');
      return;
    }
    setSaving(true);
    try {
      const newId = await create('cy.vendor', {
        legal_name: legalName,
        legal_name_ar: legalNameAr || null,
        trade_name: tradeName || null,
        category,
        cr_number: crNumber || null,
        cr_expiry: crExpiry || null,
        tax_number: taxNumber || null,
        bank_name: bankName || null,
        bank_branch: bankBranch || null,
        iban: iban || null,
        swift_code: swiftCode || null,
        credit_limit: creditLimit ? parseFloat(creditLimit) : null,
        payment_terms_days: paymentTerms,
        contact_name: contactName || null,
        contact_email: contactEmail || null,
        contact_phone: contactPhone || null,
        address: address || null,
        city: city || null,
        approval_status: 'draft'
      });

      if (newId) {
        setVendorId(newId);
        setStep(2);
      }
    } catch (err: any) {
      alert('Error registering supplier: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  // Upload CR/Tax files
  const handleUploadDocuments = async () => {
    if (!vendorId) return;
    setSaving(true);
    try {
      for (const [docType, file] of Object.entries(docs)) {
        if (!file) continue;
        setUploadProgress(prev => ({ ...prev, [docType]: 'Uploading...' }));
        
        const formData = new FormData();
        formData.append('vendor_id', vendorId.toString());
        formData.append('doc_type', docType);
        formData.append('file', file);

        const res = await fetch('http://localhost:8888/api/vendors/upload', {
          method: 'POST',
          body: formData,
        });

        if (res.ok) {
          setUploadProgress(prev => ({ ...prev, [docType]: 'Completed' }));
        } else {
          const detail = await res.text();
          setUploadProgress(prev => ({ ...prev, [docType]: 'Failed: ' + detail }));
        }
      }

      // Submit for review after document uploads
      const submitRes = await fetch('http://localhost:8888/api/rpc/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'cy.vendor',
          method: 'submit_for_review',
          args: [vendorId]
        })
      });
      if (submitRes.ok) {
        setStep(3);
      } else {
        alert('Supplier metadata saved, but failed to submit for manager review.');
      }
    } catch (err: any) {
      alert('Error uploading onboarding files: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      {/* Header */}
      <div className="max-w-4xl mx-auto flex items-center gap-4 mb-8">
        <button 
          onClick={() => router.push('/purchase/vendors')}
          className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
        >
          <ArrowLeft className="w-5 h-5 text-slate-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            Supplier Registration Wizard
          </h1>
          <p className="text-sm text-slate-400">Onboard a new supplier profile with legal and compliance credentials</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto bg-slate-900/40 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl">
        {/* Step Indicator */}
        <div className="flex justify-between items-center mb-8 border-b border-slate-800/60 pb-6">
          {[
            { step: 1, label: 'Profile Details' },
            { step: 2, label: 'Upload Credentials' },
            { step: 3, label: 'Verification Submitted' }
          ].map((s) => (
            <div key={s.step} className="flex items-center gap-2">
              <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                step === s.step 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' 
                  : step > s.step 
                    ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30' 
                    : 'bg-slate-800 text-slate-500 border border-slate-700/50'
              }`}>
                {step > s.step ? '✓' : s.step}
              </span>
              <span className={`text-sm ${step === s.step ? 'text-slate-100 font-medium' : 'text-slate-500'}`}>{s.label}</span>
            </div>
          ))}
        </div>

        {/* Step 1: Form details */}
        {step === 1 && (
          <form onSubmit={handleSaveProfile} className="space-y-6 text-sm">
            {/* Identity */}
            <div className="space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-blue-400 flex items-center gap-2">
                <Building className="w-4 h-4" /> Company Identity
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Legal Business Name (English)*</label>
                  <input 
                    type="text" required placeholder="e.g. Cycom Food Distributors" 
                    value={legalName} onChange={e => setLegalName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Legal Business Name (Arabic)</label>
                  <input 
                    type="text" placeholder="الاسم القانوني للشركة" 
                    value={legalNameAr} onChange={e => setLegalNameAr(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Brand / Trade Name</label>
                  <input 
                    type="text" placeholder="e.g. Cycom Group" 
                    value={tradeName} onChange={e => setTradeName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Business Category</label>
                  <select 
                    value={category} onChange={e => setCategory(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  >
                    <option value="goods">Goods & Supply</option>
                    <option value="services">Operational Services</option>
                    <option value="both">Both Goods & Services</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Legal Credentials */}
            <div className="space-y-4 pt-4 border-t border-slate-800/40">
              <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4" /> Registration & Tax Compliance
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">CR Number (Commercial Register)</label>
                  <input 
                    type="text" placeholder="CR-XXXXXX" 
                    value={crNumber} onChange={e => setCrNumber(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">CR Expiry Date</label>
                  <input 
                    type="date" 
                    value={crExpiry} onChange={e => setCrExpiry(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Tax Identification Number (TIN)</label>
                  <input 
                    type="text" placeholder="TIN-XXXXXXXXX" 
                    value={taxNumber} onChange={e => setTaxNumber(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Financials */}
            <div className="space-y-4 pt-4 border-t border-slate-800/40">
              <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-2">
                <CreditCard className="w-4 h-4" /> Payment Terms & Banking
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Bank Name</label>
                  <input 
                    type="text" placeholder="Arab Bank" 
                    value={bankName} onChange={e => setBankName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">IBAN Number</label>
                  <input 
                    type="text" placeholder="JO85ARAB..." 
                    value={iban} onChange={e => setIban(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none col-span-2"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Credit Limit (JOD)</label>
                  <input 
                    type="number" placeholder="50000" 
                    value={creditLimit} onChange={e => setCreditLimit(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Payment Terms</label>
                  <select 
                    value={paymentTerms} onChange={e => setPaymentTerms(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  >
                    <option value={0}>Cash on Delivery</option>
                    <option value={15}>15 Days</option>
                    <option value={30}>30 Days</option>
                    <option value={60}>60 Days</option>
                    <option value={90}>90 Days</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Contacts & Operations */}
            <div className="space-y-4 pt-4 border-t border-slate-800/40">
              <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-2">
                <Phone className="w-4 h-4" /> Operational Contacts
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Contact Person Name</label>
                  <input 
                    type="text" placeholder="Samih Masri" 
                    value={contactName} onChange={e => setContactName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Work Email</label>
                  <input 
                    type="email" placeholder="samih@supplier.com" 
                    value={contactEmail} onChange={e => setContactEmail(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Work Phone</label>
                  <input 
                    type="text" placeholder="+96279..." 
                    value={contactPhone} onChange={e => setContactPhone(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500/50 outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 border-t border-slate-800/60 pt-6">
              <button 
                type="button" onClick={() => router.push('/purchase/vendors')}
                className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition"
              >
                Cancel
              </button>
              <button 
                type="submit" disabled={saving}
                className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium shadow-lg shadow-blue-600/15 transition disabled:opacity-50"
              >
                <Save className="w-4 h-4" /> Save & Continue
              </button>
            </div>
          </form>
        )}

        {/* Step 2: Document Upload */}
        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-lg font-bold mb-2 flex items-center gap-2">
              <Upload className="w-5 h-5 text-blue-400" /> Onboarding Attachment Files
            </h2>
            <p className="text-sm text-slate-400 mb-6">Attach compliance certificates to submit the supplier for review.</p>

            <div className="space-y-4">
              {[
                { type: 'cr', label: 'Commercial Register (CR)*' },
                { type: 'tax_certificate', label: 'Tax Registration Certificate*' },
                { type: 'bank_letter', label: 'IBAN Confirmation Letter from Bank*' }
              ].map((d) => (
                <div key={d.type} className="p-4 bg-slate-950/40 border border-slate-850 rounded-xl flex items-center justify-between gap-4">
                  <div>
                    <h4 className="font-semibold text-slate-200">{d.label}</h4>
                    <p className="text-xs text-slate-500 mt-0.5">PDF or image format, max size 5MB</p>
                    {uploadProgress[d.type] && (
                      <span className={`inline-block text-xs font-semibold mt-2 ${
                        uploadProgress[d.type] === 'Completed' ? 'text-emerald-400' : 'text-amber-400'
                      }`}>
                        {uploadProgress[d.type]}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {docs[d.type] && (
                      <span className="text-xs text-slate-400 truncate max-w-xs">{docs[d.type]?.name}</span>
                    )}
                    <label className="p-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition rounded-lg cursor-pointer flex items-center justify-center">
                      <FileText className="w-4 h-4 text-slate-400" />
                      <input 
                        type="file" accept=".pdf,.png,.jpg,.jpeg"
                        onChange={e => handleFileChange(d.type, e.target.files?.[0] || null)}
                        className="hidden"
                      />
                    </label>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 border-t border-slate-800/60 pt-6">
              <button 
                onClick={() => setStep(1)}
                disabled={saving}
                className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition"
              >
                Back
              </button>
              <button 
                onClick={handleUploadDocuments}
                disabled={saving || !docs.cr || !docs.tax_certificate || !docs.bank_letter}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white font-medium shadow-lg shadow-emerald-600/15 transition"
              >
                Upload & Onboard Supplier
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Success Screen */}
        {step === 3 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Onboarding Request Submitted</h2>
            <p className="text-sm text-slate-400 max-w-md mx-auto mb-8">
              The supplier profile and credential documents have been uploaded and queued for compliance and manager approvals.
            </p>
            <button 
              onClick={() => router.push('/purchase/vendors')}
              className="px-6 py-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition rounded-xl text-sm font-semibold"
            >
              Return to Directory
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
