'use client';

import React, { useState, useEffect } from 'react';
import { Send, CheckCircle, Copy, ExternalLink, RefreshCw } from 'lucide-react';
import Link from 'next/link';
import { useT } from '@/lib/i18n';

const STATUS_KEY: Record<string, string> = {
  Sent: 'status.sent',
  Viewed: 'status.viewed',
  Signed: 'status.signed',
};

export default function SignRequests() {
  const t = useT();
  const [requests, setRequests] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const templatesRes = await fetch('http://localhost:8000/api/sign/templates');
      const templatesData = await templatesRes.json();
      setTemplates(templatesData);

      const requestsRes = await fetch('http://localhost:8000/api/sign/requests');
      const requestsData = await requestsRes.json();
      setRequests(requestsData);
    } catch (err) {
      console.error("Failed to fetch signature requests:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCopyLink = (token: string) => {
    const url = `${window.location.origin}/sign/public/${token}`;
    navigator.clipboard.writeText(url);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2000);
  };

  const getTemplateName = (templateId: number) => {
    const template = templates.find(t2 => t2.id === templateId);
    return template ? template.name : t('signRequests.templateFallback', { id: templateId });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">{t('signRequests.title')}</h2>
          <p className="text-xs text-slate-400">{t('signRequests.subtitle')}</p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-1.5 bg-white/5 border border-white/10 hover:bg-white/10 text-slate-300 hover:text-white rounded-xl text-xs font-bold transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          {t('signRequests.refresh')}
        </button>
      </div>

      <div className="glass-card p-6 min-h-[400px]">
        {loading ? (
          <div className="flex justify-center items-center h-[300px] text-slate-400">{t('signRequests.loading')}</div>
        ) : requests.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 border border-white/10">
              <Send className="w-8 h-8 text-slate-500" />
            </div>
            <h3 className="text-white font-bold mb-2">{t('signRequests.emptyTitle')}</h3>
            <p className="text-sm text-slate-400 max-w-sm">
              {t('signRequests.emptyBodyPrefix')}{' '}
              <Link href="/sign/templates" className="text-rose-400 hover:underline">{t('signRequests.templatesLink')}</Link>
              {' '}{t('signRequests.emptyBodySuffix')}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('signRequests.colRequestId')}</th>
                  <th>{t('signRequests.colDocName')}</th>
                  <th>{t('signRequests.colSignerName')}</th>
                  <th>{t('signRequests.colSignerEmail')}</th>
                  <th>{t('signRequests.colDateSent')}</th>
                  <th>{t('signRequests.colStatus')}</th>
                  <th className="text-end">{t('signRequests.colActions')}</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((req) => {
                  const signer = req.signers?.[0] || { name: t('signDash.externalSigner'), email: '' };
                  return (
                    <tr key={req.id}>
                      <td className="font-mono text-xs text-slate-400">REQ-{req.id}</td>
                      <td className="font-bold text-white">{getTemplateName(req.template_id)}</td>
                      <td className="text-slate-300 font-semibold">{signer.name}</td>
                      <td className="text-slate-400">{signer.email}</td>
                      <td className="font-mono text-xs text-slate-500">
                        {new Date(req.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <span className={`badge text-[9px] ${
                          req.status === 'Signed' ? 'badge-green' : 'badge-yellow'
                        }`}>
                          {STATUS_KEY[req.status] ? t(STATUS_KEY[req.status]) : req.status}
                        </span>
                      </td>
                      <td className="text-end">
                        <div className="flex items-center justify-end gap-2">
                          {req.status !== 'Signed' ? (
                            <>
                              <button
                                onClick={() => handleCopyLink(req.token)}
                                className="p-1.5 rounded bg-white/4 border border-white/8 hover:border-white/12 text-slate-300 hover:text-white text-[10px] font-bold flex items-center gap-1.5"
                                title={t('signRequests.copyLink')}
                              >
                                <Copy className="w-3 h-3" />
                                <span>{copiedToken === req.token ? t('signRequests.copied') : t('signRequests.copyLinkBtn')}</span>
                              </button>
                              <a
                                href={`/sign/public/${req.token}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-1.5 rounded bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/25 text-[#FB7185] text-[10px] font-bold flex items-center gap-1"
                                title={t('signRequests.openPortal')}
                              >
                                <span>{t('signRequests.sign')}</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            </>
                          ) : (
                            <span className="text-[10px] text-emerald-400 font-bold flex items-center gap-1">
                              <CheckCircle className="w-3.5 h-3.5" /> {t('signRequests.completed')}
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
