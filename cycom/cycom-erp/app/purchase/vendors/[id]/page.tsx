'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft, CheckCircle2, AlertTriangle, ShieldCheck, 
  Database, UserCheck, X, FileText, CreditCard, Building2, Download
} from 'lucide-react';
import { call } from '@/lib/cycom';
import { LoadingCard } from '@/components/CycomEmptyStates';

interface VendorDetails {
  id: number;
  legal_name: string;
  legal_name_ar?: string;
  trade_name?: string;
  vendor_code?: string;
  category?: string;
  cr_number?: string;
  cr_expiry?: string;
  tax_number?: string;
  bank_name?: string;
  bank_branch?: string;
  iban?: string;
  swift_code?: string;
  payment_terms_days: number;
  credit_limit?: number;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  city?: string;
  approval_status: string;
  rejection_reason?: string;
  documents: Array<{
    id: number;
    doc_type: string;
    original_filename: string;
    storage_path: string;
    file_size_bytes: number;
    uploaded_at: string;
  }>;
}

export default function VendorApprovalDetail() {
  const router = useRouter();
  const params = useParams();
  const idStr = params?.id as string;
  const vendorId = parseInt(idStr);

  const [vendor, setVendor] = useState<VendorDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [rejecting, setRejecting] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  // Fetch Vendor Profile & Documents
  useEffect(() => {
    const fetchVendorDetails = async () => {
      if (!vendorId) return;
      try {
        const vData = await call<any>({
          model: 'cy.vendor',
          method: 'read',
          args: [vendorId]
        });

        // Fetch documents
        const docs = await call<any[]>({
          model: 'cy.vendor.document',
          method: 'search_read',
          args: [[['vendor_id', '=', vendorId]]]
        });

        if (vData) {
          setVendor({ ...vData, documents: docs || [] });
        }
      } catch (err: any) {
        alert('Error fetching details: ' + err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchVendorDetails();
  }, [vendorId]);

  // Approve Vendor RPC Action
  const handleApprove = async () => {
    if (!vendorId) return;
    try {
      const success = await call<boolean>({
        model: 'cy.vendor',
        method: 'approve',
        args: [vendorId]
      });
      if (success) {
        alert('Vendor onboarding request approved successfully!');
        router.push('/purchase/vendors');
      }
    } catch (err: any) {
      alert('Error approving vendor: ' + err.message);
    }
  };

  // Reject Vendor RPC Action
  const handleReject = async () => {
    if (!vendorId || !rejectReason) return;
    try {
      const success = await call<boolean>({
        model: 'cy.vendor',
        method: 'reject',
        args: [vendorId, rejectReason]
      });
      if (success) {
        alert('Vendor onboarding request rejected.');
        router.push('/purchase/vendors');
      }
    } catch (err: any) {
      alert('Error rejecting vendor: ' + err.message);
    }
  };

  if (loading) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8"><LoadingCard label="Loading supplier details…" /></div>;
  if (!vendor) return <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-center text-slate-400">Supplier record not found.</div>;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      {/* Header */}
      <div className="max-w-5xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push('/purchase/vendors')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
              {vendor.legal_name}
              {vendor.legal_name_ar && <span className="text-sm font-normal text-slate-500 font-sans">({vendor.legal_name_ar})</span>}
            </h1>
            <p className="text-xs text-slate-400 mt-1">Supplier Code: {vendor.vendor_code || `VND-${String(vendor.id).padStart(4, '0')}`}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {vendor.approval_status === 'submitted' || vendor.approval_status === 'draft' ? (
            <>
              <button 
                onClick={() => setRejecting(true)}
                className="px-4 py-2 border border-rose-500/20 hover:bg-rose-500/10 text-rose-400 font-semibold rounded-lg transition"
              >
                Reject Onboarding
              </button>
              <button 
                onClick={handleApprove}
                className="flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-white font-semibold shadow-lg shadow-emerald-600/15 transition"
              >
                <UserCheck className="w-4 h-4" /> Approve Supplier
              </button>
            </>
          ) : (
            <span className={`px-3 py-1 font-bold uppercase rounded-md tracking-wider ${
              vendor.approval_status === 'approved' 
                ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/20' 
                : 'bg-rose-950/40 text-rose-400 border border-rose-500/20'
            }`}>
              Onboarding {vendor.approval_status.toUpperCase()}
            </span>
          )}
        </div>
      </div>

      <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card & Bank details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Identity & Legal Info */}
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-3">
              <Building2 className="w-4 h-4 text-blue-400" /> Supplier Credentials & Logistics
            </h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Brand Name</label>
                <div className="text-slate-200 font-medium mt-0.5">{vendor.trade_name || '—'}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Business Category</label>
                <div className="text-slate-200 font-semibold uppercase mt-0.5">{vendor.category || 'GOODS'}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Commercial Register (CR)</label>
                <div className="text-slate-200 mt-0.5">{vendor.cr_number || '—'}</div>
                {vendor.cr_expiry && <div className="text-[10px] text-slate-500 mt-0.5">Expires: {vendor.cr_expiry}</div>}
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Tax ID Number (TIN)</label>
                <div className="text-slate-200 mt-0.5">{vendor.tax_number || '—'}</div>
              </div>
            </div>
          </div>

          {/* Banking */}
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-3">
              <CreditCard className="w-4 h-4 text-emerald-400" /> Bank Accounts & Credit Terms
            </h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Bank Name</label>
                <div className="text-slate-200 mt-0.5">{vendor.bank_name || '—'}</div>
                {vendor.bank_branch && <div className="text-[10px] text-slate-500 mt-0.5">Branch: {vendor.bank_branch}</div>}
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">IBAN</label>
                <div className="text-slate-200 font-mono text-xs mt-0.5">{vendor.iban || '—'}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Payment Terms</label>
                <div className="text-slate-200 font-semibold mt-0.5">{vendor.payment_terms_days} Days Net</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Credit Limit</label>
                <div className="text-emerald-400 font-bold mt-0.5">
                  {vendor.credit_limit ? `${vendor.credit_limit.toLocaleString()} JOD` : '—'}
                </div>
              </div>
            </div>
          </div>

          {/* Verification documents */}
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-3">
              <FileText className="w-4 h-4 text-indigo-400" /> Uploaded Document Verification
            </h3>
            
            {vendor.documents.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-xs">No compliance certificates uploaded.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {vendor.documents.map((d) => (
                  <div key={d.id} className="p-3 bg-slate-950/40 border border-slate-850 rounded-xl flex items-center justify-between gap-4">
                    <div className="truncate">
                      <h4 className="font-semibold text-slate-300 capitalize truncate">{d.doc_type.replace('_', ' ')}</h4>
                      <p className="text-[10px] text-slate-500 mt-0.5 truncate">{d.original_filename}</p>
                    </div>
                    <a 
                      href={`http://localhost:8888${d.storage_path}`}
                      target="_blank" rel="noopener noreferrer"
                      className="p-2 bg-slate-900 hover:bg-slate-800 rounded-lg transition"
                    >
                      <Download className="w-4 h-4 text-slate-400" />
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Info - Contacts */}
        <div className="space-y-6">
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-3">
              Contact Information
            </h3>
            
            <div className="space-y-3">
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Representative</label>
                <div className="text-slate-200 font-medium mt-0.5">{vendor.contact_name || '—'}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Email Address</label>
                <div className="text-slate-200 mt-0.5">{vendor.contact_email || '—'}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Phone</label>
                <div className="text-slate-200 mt-0.5">{vendor.contact_phone || '—'}</div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Office Address</label>
                <div className="text-slate-200 mt-0.5">{vendor.address || '—'}</div>
                {vendor.city && <div className="text-[10px] text-slate-500 mt-0.5">{vendor.city}, Jordan</div>}
              </div>
            </div>
          </div>

          {vendor.approval_status === 'rejected' && vendor.rejection_reason && (
            <div className="glass-card p-6 border border-rose-500/20 bg-rose-500/5">
              <h3 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4" /> Rejection Explanation
              </h3>
              <p className="text-xs text-rose-300/80 leading-relaxed">{vendor.rejection_reason}</p>
            </div>
          )}
        </div>
      </div>

      {/* Reject Reason Modal */}
      <AnimatePresence>
        {rejecting && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <h3 className="font-bold text-slate-200">Reject Supplier Onboarding</h3>
                <button onClick={() => setRejecting(false)} className="p-1 hover:bg-slate-800 rounded-lg transition">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs text-slate-400">Please provide a reason for the rejection:</label>
                <textarea 
                  rows={4}
                  required
                  placeholder="e.g. Uploaded Commercial Registration document is expired..."
                  value={rejectReason} onChange={e => setRejectReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-850 rounded-lg p-3 text-slate-200 outline-none focus:border-rose-500/50"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button 
                  onClick={() => setRejecting(false)}
                  className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg transition text-xs font-semibold"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleReject}
                  disabled={!rejectReason}
                  className="px-5 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 rounded-lg text-white font-semibold shadow-lg shadow-rose-600/15 transition text-xs"
                >
                  Submit Rejection
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
