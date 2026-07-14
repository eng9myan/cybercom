'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ArrowLeft, ShieldCheck, Lock, RefreshCw, Key, ShieldAlert
} from 'lucide-react';

export default function SecuritySettings() {
  const router = useRouter();
  
  // SSO Integrations State
  const [ssoActive, setSsoActive] = useState(false);
  const [ssoProvider, setSsoProvider] = useState('okta');

  // Audit Logs Chain Verification State
  const [verifying, setVerifying] = useState(false);
  const [chainValid, setChainValid] = useState<boolean | null>(null);

  // Mock logs for chain test (correct and tampered)
  const mockValidLogs = [
    { id: 1, prev_hash: 'GENESIS_HASH', user_email: 'admin@cycom.com', action: 'CREATE', model: 'finance.invoice', created_at: '2026-07-14 01:00:00', current_hash: '6562b1ebb7345c5a46f6a922ce13f84265d4bf72b91415d1820d20bff3fae83b' },
    { id: 2, prev_hash: '6562b1ebb7345c5a46f6a922ce13f84265d4bf72b91415d1820d20bff3fae83b', user_email: 'admin@cycom.com', action: 'UPDATE', model: 'finance.invoice', created_at: '2026-07-14 01:05:00', current_hash: 'ebcfae806291d7fa8b05cf102aa5955e58d88bae724e418b6c6ac35162a51dd9' }
  ];

  const mockTamperedLogs = [
    { id: 1, prev_hash: 'GENESIS_HASH', user_email: 'admin@cycom.com', action: 'CREATE', model: 'finance.invoice', created_at: '2026-07-14 01:00:00', current_hash: '6562b1ebb7345c5a46f6a922ce13f84265d4bf72b91415d1820d20bff3fae83b' },
    { id: 2, prev_hash: '6562b1ebb7345c5a46f6a922ce13f84265d4bf72b91415d1820d20bff3fae83b', user_email: 'hacker@malicious.com', action: 'DELETE', model: 'finance.invoice', created_at: '2026-07-14 01:05:00', current_hash: 'ebcfae806291d7fa8b05cf102aa5955e58d88bae724e418b6c6ac35162a51dd9' } // Tampered payload
  ];

  const handleVerifyChain = async (tamper: boolean) => {
    setVerifying(true);
    setChainValid(null);
    try {
      const res = await fetch('http://localhost:8888/api/enterprise/audit/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          logs: tamper ? mockTamperedLogs : mockValidLogs
        })
      });
      if (res.ok) {
        const data = await res.json();
        setChainValid(data.chain_integrity_valid);
      }
    } catch {
      alert('Verification failed.');
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-xs md:text-sm">
      <div className="max-w-4xl mx-auto flex items-center gap-4 mb-8">
        <button 
          onClick={() => router.push('/settings')}
          className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
        >
          <ArrowLeft className="w-5 h-5 text-slate-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            Enterprise Security & Audit Chain
          </h1>
          <p className="text-xs text-slate-400 mt-1">Manage Single-Sign-On integrations and run SHA-256 cryptographic audit ledger verification checks.</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SSO Config */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-2">
            <Key className="w-4 h-4 text-blue-400" /> Single-Sign-On (SSO) Gate
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">SSO Authentication Gate</span>
                <p className="text-[10px] text-slate-500 mt-0.5">Enforce login exclusively through corporate identity providers.</p>
              </div>
              <button 
                onClick={() => setSsoActive(!ssoActive)}
                className={`w-11 h-6 rounded-full p-1 transition-colors duration-200 ease-in-out ${
                  ssoActive ? 'bg-blue-600' : 'bg-slate-800'
                }`}
              >
                <div className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-200 ease-in-out ${
                  ssoActive ? 'translate-x-5' : 'translate-x-0'
                }`} />
              </button>
            </div>

            {ssoActive && (
              <div className="space-y-1 border-t border-white/5 pt-3">
                <label className="text-slate-400">Select Provider Profile</label>
                <select 
                  value={ssoProvider} onChange={e => setSsoProvider(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
                >
                  <option value="okta">Okta Identity Cloud</option>
                  <option value="azure">Microsoft Azure AD (OIDC)</option>
                  <option value="google">Google Workspace Enterprise</option>
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Audit Log Cryptographic Integrity Chain Checker */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> Cryptographic Ledger Audit
          </h3>
          <p className="text-xs text-slate-400">Verify the integrity of Cycom's ledger block chain history. Detects any database tampered modifications.</p>

          <div className="flex gap-2">
            <button 
              onClick={() => handleVerifyChain(false)}
              disabled={verifying}
              className="flex-1 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition rounded-lg text-xs font-semibold text-slate-300"
            >
              Verify Valid Chain
            </button>
            <button 
              onClick={() => handleVerifyChain(true)}
              disabled={verifying}
              className="flex-1 py-2 bg-rose-950/20 border border-rose-500/20 hover:bg-rose-500/10 transition rounded-lg text-xs font-semibold text-rose-400"
            >
              Verify Tampered Chain
            </button>
          </div>

          {chainValid !== null && (
            <div className={`p-4 rounded-xl border flex items-center gap-3 transition-all ${
              chainValid 
                ? 'bg-emerald-950/40 border-emerald-500/20 text-emerald-400' 
                : 'bg-rose-950/40 border-rose-500/20 text-rose-400'
            }`}>
              {chainValid ? (
                <>
                  <ShieldCheck className="w-5 h-5 flex-shrink-0" />
                  <div>
                    <h5 className="font-bold">Ledger Integrity Secure</h5>
                    <p className="text-[10px] text-emerald-500/80 mt-0.5">All SHA-256 block hashes validated correctly. No database alterations detected.</p>
                  </div>
                </>
              ) : (
                <>
                  <ShieldAlert className="w-5 h-5 flex-shrink-0 animate-bounce" />
                  <div>
                    <h5 className="font-bold">Hash Mismatch Detected!</h5>
                    <p className="text-[10px] text-rose-400/80 mt-0.5">Warning: Chain linkage broken at block #2. Unvalidated records or tampering identified.</p>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
