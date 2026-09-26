'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft, ShieldCheck, Key, ShieldAlert, RefreshCw
} from 'lucide-react';
import { call } from '@/lib/cycom';
import { useT } from '@/lib/i18n';

interface ChainResult {
  valid: boolean;
  chain_key: string;
  checked?: number;
  errors?: unknown[];
  error?: string;
}

const SSO_ENABLED_KEY = 'cycom.security.sso_required';
const SSO_PROVIDER_KEY = 'cycom.security.sso_provider';

export default function SecuritySettings() {
  const t = useT();
  const router = useRouter();

  // SSO preference -- a real, persisted tenant preference (ir.config_parameter),
  // not a live gate. Actually enforcing SSO login requires wiring a real
  // identity provider into this tenant's Keycloak realm, which is external
  // setup, not something a toggle in this UI can do on its own.
  const [ssoRequired, setSsoRequired] = useState(false);
  const [ssoProvider, setSsoProvider] = useState('okta');
  const [ssoStatus, setSsoStatus] = useState<string | null>(null);

  // Real audit-chain verification against platform.audit's actual SHA-256
  // hash chain (products.cycom writes go through AuditService; see
  // platform/audit/services.py::AuditChainVerifier).
  const [verifying, setVerifying] = useState(false);
  const [results, setResults] = useState<ChainResult[] | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const enabled = await call<string | false>({ model: 'ir.config_parameter', method: 'get_param', args: [SSO_ENABLED_KEY, false] });
        const provider = await call<string | false>({ model: 'ir.config_parameter', method: 'get_param', args: [SSO_PROVIDER_KEY, false] });
        setSsoRequired(enabled === 'true');
        if (provider) setSsoProvider(provider);
      } catch {
        // No preference saved yet -- defaults stand.
      }
    })();
  }, []);

  const saveSso = async (nextRequired: boolean, nextProvider: string) => {
    setSsoStatus(null);
    try {
      await call({ model: 'ir.config_parameter', method: 'set_param', args: [SSO_ENABLED_KEY, String(nextRequired)] });
      await call({ model: 'ir.config_parameter', method: 'set_param', args: [SSO_PROVIDER_KEY, nextProvider] });
      setSsoStatus(t('settingsSecurity.ssoSaved'));
    } catch (err: any) {
      setSsoStatus(t('settingsSecurity.ssoSaveFailed', { msg: err.message }));
    }
  };

  const handleVerifyChain = async () => {
    setVerifying(true);
    setResults(null);
    setVerifyError(null);
    try {
      const res = await fetch('/api/cycom/rest/audit/events/verify_chain/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({}),
      });
      const data = await res.json().catch(() => ({}));
      if (res.status === 403) {
        setVerifyError(t('settingsSecurity.notAuthorized'));
      } else if (res.ok) {
        setResults(data as ChainResult[]);
      } else {
        setVerifyError(t('settingsSecurity.verifyFailed', { msg: data.detail || res.statusText }));
      }
    } catch (err: any) {
      setVerifyError(t('settingsSecurity.verifyFailed', { msg: err.message }));
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
          <ArrowLeft className="w-5 h-5 text-slate-400 rtl:-scale-x-100" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            {t('settingsSecurity.title')}
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('settingsSecurity.subtitle')}</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SSO preference */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-2">
            <Key className="w-4 h-4 text-blue-400" /> {t('settingsSecurity.ssoHeading')}
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">{t('settingsSecurity.ssoGate')}</span>
                <p className="text-[10px] text-slate-500 mt-0.5 max-w-[280px]">{t('settingsSecurity.ssoGateNote')}</p>
              </div>
              <button
                onClick={() => { const next = !ssoRequired; setSsoRequired(next); saveSso(next, ssoProvider); }}
                className={`w-11 h-6 rounded-full p-1 transition-colors duration-200 ease-in-out flex-shrink-0 ${
                  ssoRequired ? 'bg-blue-600' : 'bg-slate-800'
                }`}
              >
                <div className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-200 ease-in-out ${
                  ssoRequired ? 'translate-x-5 rtl:-translate-x-5' : 'translate-x-0'
                }`} />
              </button>
            </div>

            <div className="space-y-1 border-t border-white/5 pt-3">
              <label className="text-slate-400">{t('settingsSecurity.providerProfile')}</label>
              <select
                value={ssoProvider}
                onChange={(e) => { setSsoProvider(e.target.value); saveSso(ssoRequired, e.target.value); }}
                className="w-full bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-slate-200 outline-none"
              >
                <option value="okta">Okta Identity Cloud</option>
                <option value="azure">Microsoft Azure AD (OIDC)</option>
                <option value="google">Google Workspace Enterprise</option>
              </select>
            </div>
            {ssoStatus && <p className="text-[10px] text-slate-500">{ssoStatus}</p>}
          </div>
        </div>

        {/* Real audit hash-chain verification */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 border-b border-white/5 pb-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> {t('settingsSecurity.auditHeading')}
          </h3>
          <p className="text-xs text-slate-400">{t('settingsSecurity.auditDesc')}</p>

          <button
            onClick={handleVerifyChain}
            disabled={verifying}
            className="w-full flex items-center justify-center gap-2 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-white font-semibold transition"
          >
            <RefreshCw className={`w-4 h-4 ${verifying ? 'animate-spin' : ''}`} />
            {verifying ? t('settingsSecurity.verifying') : t('settingsSecurity.verifyChain')}
          </button>

          {verifyError && (
            <div className="p-4 rounded-xl border bg-amber-950/40 border-amber-500/20 text-amber-400 flex items-center gap-3">
              <ShieldAlert className="w-5 h-5 flex-shrink-0" />
              <p className="text-xs">{verifyError}</p>
            </div>
          )}

          {results && results.length === 0 && (
            <p className="text-xs text-slate-500 text-center py-4">{t('settingsSecurity.noChains')}</p>
          )}

          {results && results.map((r) => (
            <div key={r.chain_key} className={`p-4 rounded-xl border flex items-center gap-3 ${
              r.valid
                ? 'bg-emerald-950/40 border-emerald-500/20 text-emerald-400'
                : 'bg-rose-950/40 border-rose-500/20 text-rose-400'
            }`}>
              {r.valid ? <ShieldCheck className="w-5 h-5 flex-shrink-0" /> : <ShieldAlert className="w-5 h-5 flex-shrink-0 animate-bounce" />}
              <div className="min-w-0">
                <h5 className="font-bold truncate">{r.chain_key}</h5>
                <p className="text-[10px] mt-0.5 opacity-80">
                  {r.valid
                    ? t('settingsSecurity.chainValid', { checked: String(r.checked ?? 0) })
                    : t('settingsSecurity.chainInvalid', { errors: String((r.errors || []).length) })}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
