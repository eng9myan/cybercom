'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCycomList, m2oName, fmtDate, type Many2One } from '@/lib/cycomModels';
import { create } from '@/lib/cycom';
import {
  BarChart2, Plus, X
} from 'lucide-react';
import { useT } from '@/lib/i18n';

interface Campaign {
  id: string;
  name: string;
  type: 'Email Blast' | 'SMS Alert' | 'Newsletter';
  target: string;
  status: 'Sent' | 'Scheduled' | 'Draft';
  sentCount: number;
  openRate: number;
  clickRate: number;
  date: string;
}

type CycomMailing = {
  id: number;
  name?: string;
  mailing_model_id?: Many2One;
  state?: string;
  sent?: number;
  failed?: number;
  scheduled_date?: string;
};

const MAILING_STATE_MAP: Record<string, Campaign['status']> = {
  done: 'Sent', sending: 'Sent', in_queue: 'Scheduled', draft: 'Draft',
};

const mapMailing = (r: CycomMailing): Campaign => ({
  id: `CMP-${r.id}`,
  name: r.name || '—',
  type: 'Email Blast',
  target: m2oName(r.mailing_model_id, '—'),
  status: MAILING_STATE_MAP[r.state ?? ''] ?? 'Draft',
  sentCount: r.sent ?? 0,
  openRate: 0,
  clickRate: 0,
  date: fmtDate(r.scheduled_date),
});

const STATUS_KEY: Record<Campaign['status'], string> = {
  Sent: 'status.sent',
  Scheduled: 'status.scheduled',
  Draft: 'status.draft',
};

const TEMPLATES = [
  { id: 'promo', title: 'Summer Sale Template', desc: 'Bold grid, product discounts, JOD checkout buttons.', color: '#E67E22' },
  { id: 'points', title: 'Loyalty Statement', desc: 'Minimal text, QR code slot, dynamic points balance.', color: '#5DADE2' },
  { id: 'newsletter', title: 'Corporate Digest', desc: 'Multi-column layout, CEO greeting, financial brief.', color: '#A855F7' }
];

export default function MarketingPage() {
  const t = useT();
  const { rows: liveCampaigns, loading } = useCycomList<CycomMailing, Campaign>(
    'mass.mailing', [], ['name', 'mailing_model_id', 'state', 'sent', 'failed', 'scheduled_date'],
    mapMailing,
  );
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (!loading) setCampaigns(liveCampaigns); }, [loading]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTemplate, setActiveTemplate] = useState('promo');

  // Form variables
  const [campName, setCampName] = useState('');
  const [campType, setCampType] = useState<'Email Blast' | 'SMS Alert' | 'Newsletter'>('Email Blast');
  const [campTarget, setCampTarget] = useState('All retail customers');

  // Math stats
  const totalSent = campaigns.reduce((sum, c) => sum + c.sentCount, 0);
  const avgOpenRate = parseFloat((campaigns.filter(c => c.sentCount > 0).reduce((sum, c) => sum + c.openRate, 0) / campaigns.filter(c => c.sentCount > 0).length).toFixed(1));
  const avgClickRate = parseFloat((campaigns.filter(c => c.sentCount > 0).reduce((sum, c) => sum + c.clickRate, 0) / campaigns.filter(c => c.sentCount > 0).length).toFixed(1));

  const TYPE_TO_BACKEND: Record<Campaign['type'], string> = {
    'Email Blast': 'email', 'SMS Alert': 'sms', 'Newsletter': 'newsletter',
  };

  const TYPE_LABEL: Record<Campaign['type'], string> = {
    'Email Blast': t('marketingDash.typeEmail'),
    'SMS Alert': t('marketingDash.typeSms'),
    'Newsletter': t('marketingDash.typeNewsletter'),
  };

  const handleLaunchCampaign = async (status: 'Sent' | 'Scheduled') => {
    if (!campName.trim()) return;

    const backendState = status === 'Sent' ? 'done' : 'in_queue';
    try {
      const id = await create('mass.mailing', {
        name: campName,
        campaign_type: TYPE_TO_BACKEND[campType],
        target: campTarget,
        state: backendState,
      });
      const newCamp: Campaign = {
        id: `CMP-${id}`,
        name: campName,
        type: campType,
        target: campTarget,
        status,
        sentCount: 0,
        openRate: 0,
        clickRate: 0,
        date: fmtDate(new Date().toISOString()),
      };
      setCampaigns(prev => [newCamp, ...prev]);
    } catch {
      // leave modal open on failure so the user can retry
      return;
    }
    setIsModalOpen(false);
    setCampName('');
    setCampType('Email Blast');
    setCampTarget('All retail customers');
  };

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>{t('marketingDash.loading')}</div>;

  return (
    <div className="space-y-6 max-w-[1200px] mx-auto">
      {/* Page Header */}
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title text-white">{t('marketingDash.title')}</h1>
          <p className="page-subtitle">{t('marketingDash.subtitle')}</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#E67E22] hover:bg-orange-600 text-white text-xs font-semibold transition-all shadow-md shadow-orange-500/10"
        >
          <Plus className="w-4 h-4" />
          {t('marketingDash.createCampaign')}
        </button>
      </div>

      {/* KPI Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 space-y-1 relative overflow-hidden">
          <div className="absolute top-0 start-0 w-full h-0.5 bg-gradient-to-r from-transparent via-[#E67E22]/30 to-transparent" />
          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">{t('marketingDash.delivered')}</span>
          <p className="text-xl font-black text-white">{totalSent.toLocaleString()}</p>
          <span className="text-[10px] text-slate-400">{t('marketingDash.deliveredNote')}</span>
        </div>

        <div className="glass-card p-4 space-y-1">
          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">{t('marketingDash.avgOpenRate')}</span>
          <p className="text-xl font-black text-white">{avgOpenRate}%</p>
          <span className="text-[10px] text-emerald-400 font-bold inline-flex items-center gap-0.5">
            <BarChart2 className="w-3 h-3" /> {t('marketingDash.industryStandard')}
          </span>
        </div>

        <div className="glass-card p-4 space-y-1">
          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">{t('marketingDash.ctr')}</span>
          <p className="text-xl font-black text-[#5DADE2]">{avgClickRate}%</p>
          <span className="text-[10px] text-emerald-400 font-bold">{t('marketingDash.ctrNote')}</span>
        </div>

        <div className="glass-card p-4 space-y-1">
          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">{t('marketingDash.activePipelines')}</span>
          <p className="text-xl font-black text-[#A855F7]">{campaigns.filter(c => c.status === 'Sent').length}</p>
          <span className="text-[10px] text-slate-500">{t('marketingDash.activePipelinesNote')}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">

        {/* Campaign Lists */}
        <div className="glass-card p-5 lg:col-span-2 space-y-4">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider pb-2 border-b border-white/5">{t('marketingDash.logsHeading')}</h2>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-start border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-slate-500 uppercase tracking-widest text-[9px] font-bold">
                  <th className="py-2.5 px-3">{t('marketingDash.colName')}</th>
                  <th className="py-2.5 px-3">{t('marketingDash.colType')}</th>
                  <th className="py-2.5 px-3">{t('marketingDash.colTarget')}</th>
                  <th className="py-2.5 px-3 text-end">{t('marketingDash.colMailsSent')}</th>
                  <th className="py-2.5 px-3 text-end">{t('marketingDash.colOpenPct')}</th>
                  <th className="py-2.5 px-3 text-end">{t('marketingDash.colClickPct')}</th>
                  <th className="py-2.5 px-3 text-center">{t('marketingDash.colStatus')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-sans">
                {campaigns.map(c => (
                  <tr key={c.id} className="hover:bg-white/2 transition-colors">
                    <td className="py-2.5 px-3">
                      <div>
                        <p className="font-semibold text-slate-200">{c.name}</p>
                        <p className="text-[9px] text-slate-500 font-mono">{c.date}</p>
                      </div>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="text-slate-400 font-semibold">{TYPE_LABEL[c.type]}</span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">{c.target}</td>
                    <td className="py-2.5 px-3 text-end font-mono font-bold text-slate-300">
                      {c.sentCount > 0 ? c.sentCount.toLocaleString() : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-end font-mono text-slate-400">
                      {c.sentCount > 0 ? `${c.openRate}%` : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-end font-mono text-slate-400">
                      {c.sentCount > 0 ? `${c.clickRate}%` : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${
                        c.status === 'Sent'
                          ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                          : c.status === 'Scheduled'
                            ? 'bg-[#5DADE2]/10 border-[#5DADE2]/20 text-[#5DADE2]'
                            : 'bg-slate-500/10 border-white/5 text-slate-400'
                      }`}>
                        {t(STATUS_KEY[c.status])}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Templates Directory */}
        <div className="glass-card p-5 space-y-4">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider pb-2 border-b border-white/5">{t('marketingDash.templatesHeading')}</h2>

          <div className="space-y-3">
            {TEMPLATES.map(tp => (
              <button
                key={tp.id}
                onClick={() => setActiveTemplate(tp.id)}
                className={`w-full p-3.5 rounded-xl border text-start transition-all relative overflow-hidden ${
                  activeTemplate === tp.id
                    ? 'bg-gradient-to-br from-white/3 to-transparent'
                    : 'bg-transparent border-white/5'
                }`}
                style={{ borderColor: activeTemplate === tp.id ? `${tp.color}40` : '' }}
              >
                {activeTemplate === tp.id && (
                  <div className="absolute top-0 start-0 w-1 h-full" style={{ backgroundColor: tp.color }} />
                )}
                <h3 className="text-xs font-bold text-white mb-1">{tp.title}</h3>
                <p className="text-[10px] text-slate-400 leading-relaxed">{tp.desc}</p>
              </button>
            ))}
          </div>
        </div>

      </div>

      {/* Campaign Creation Dialog Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card max-w-md w-full p-6 space-y-4 relative"
            >
              <button
                onClick={() => setIsModalOpen(false)}
                className="absolute top-4 end-4 text-slate-500 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="space-y-1">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">{t('marketingDash.modalTitle')}</h2>
                <p className="text-[10px] text-slate-500">{t('marketingDash.modalSubtitle')}</p>
              </div>

              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">{t('marketingDash.campaignTitle')}</label>
                  <input
                    type="text"
                    placeholder={t('marketingDash.campaignTitlePh')}
                    value={campName}
                    onChange={(e) => setCampName(e.target.value)}
                    className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-orange-500/50"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">{t('marketingDash.broadcastType')}</label>
                  <select
                    value={campType}
                    onChange={(e) => setCampType(e.target.value as any)}
                    className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-orange-500/50"
                  >
                    <option value="Email Blast" className="bg-[#0a0f1e]">{t('marketingDash.typeEmail')}</option>
                    <option value="SMS Alert" className="bg-[#0a0f1e]">{t('marketingDash.typeSms')}</option>
                    <option value="Newsletter" className="bg-[#0a0f1e]">{t('marketingDash.typeNewsletter')}</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">{t('marketingDash.targetSegment')}</label>
                  <select
                    value={campTarget}
                    onChange={(e) => setCampTarget(e.target.value)}
                    className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-orange-500/50"
                  >
                    <option value="All retail customers" className="bg-[#0a0f1e]">All retail customers</option>
                    <option value="POS members (>100 points)" className="bg-[#0a0f1e]">POS Members ({'>'}100 points)</option>
                    <option value="B2B Partners" className="bg-[#0a0f1e]">B2B Partners</option>
                    <option value="Portal users" className="bg-[#0a0f1e]">Employee Portal users</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <button
                  onClick={() => handleLaunchCampaign('Scheduled')}
                  className="flex-1 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-semibold transition-colors border border-white/10"
                >
                  {t('marketingDash.scheduleLater')}
                </button>
                <button
                  onClick={() => handleLaunchCampaign('Sent')}
                  disabled={!campName.trim()}
                  className="flex-1 py-2 rounded-xl bg-[#E67E22] hover:bg-orange-600 disabled:opacity-40 text-white text-xs font-semibold transition-colors shadow-md shadow-orange-500/10"
                >
                  {t('marketingDash.launchNow')}
                </button>
              </div>

            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
