'use client';

import React from 'react';
import { useCycomList, fmtCode, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';
import { useT } from '@/lib/i18n';

type CycomTicket = {
  id: number;
  name?: string;
  partner_id?: Many2One;
  user_id?: Many2One;
  priority?: string;
  stage_id?: Many2One;
  team_id?: Many2One;
};

type PriorityKey = 'high' | 'medium' | 'low';
type TicketStatusKey = 'new' | 'inProgress' | 'resolved';

interface HelpTicket {
  rawId: number;
  id: string;
  customerName: string;
  subject: string;
  priority: PriorityKey;
  assignedAgent: string;
  status: TicketStatusKey;
}

function priorityFromCycom(p?: string): PriorityKey {
  if (p === '3' || p === '2') return 'high';
  if (p === '1') return 'medium';
  return 'low';
}

function statusFromStage(stageName: string): TicketStatusKey {
  const s = (stageName || '').toLowerCase();
  if (s.includes('resolved') || s.includes('done') || s.includes('closed')) return 'resolved';
  if (s.includes('progress') || s.includes('working') || s.includes('open')) return 'inProgress';
  return 'new';
}

const PRIORITY_TONE: Record<PriorityKey, string> = { high: 'badge-red', medium: 'badge-yellow', low: 'badge-cyan' };
const STATUS_TONE: Record<TicketStatusKey, string> = { resolved: 'badge-green', inProgress: 'badge-cyan', new: 'badge-yellow' };

const mapTicket = (t: CycomTicket): HelpTicket => ({
  rawId: t.id,
  id: fmtCode('TKT', t.id, 3),
  customerName: m2oName(t.partner_id, '—'),
  subject: t.name || `Ticket ${t.id}`,
  priority: priorityFromCycom(t.priority),
  assignedAgent: m2oName(t.user_id, 'Unassigned'),
  status: t.stage_id ? statusFromStage(m2oName(t.stage_id)) : 'new',
});

export default function HelpdeskPage() {
  const t = useT();
  const { rows: tickets, loading, error } = useCycomList<CycomTicket, HelpTicket>(
    'helpdesk.ticket',
    [],
    ['name', 'partner_id', 'user_id', 'priority', 'stage_id', 'team_id'],
    mapTicket,
    { limit: 200, order: 'id desc' },
  );

  const statusLabel: Record<TicketStatusKey, string> = {
    new: t('helpdesk.statusNew'),
    inProgress: t('helpdesk.statusInProgress'),
    resolved: t('helpdesk.statusResolved'),
  };

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('helpdesk.title')}</h1>
          <p className="page-subtitle">{t('helpdesk.subtitle')}</p>
        </div>
      </div>

      {loading && <LoadingCard label={t('helpdesk.loading')} />}
      {error && <ErrorCard error={error} hint={t('helpdesk.errorHint')} />}
      {!loading && !error && tickets.length === 0 && <EmptyCard label={t('helpdesk.empty')} />}

      {!loading && !error && tickets.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">{t('helpdesk.openTickets')}</h2>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('helpdesk.ticket')}</th>
                  <th>{t('common.customer')}</th>
                  <th>{t('helpdesk.subject')}</th>
                  <th>{t('helpdesk.priority')}</th>
                  <th>{t('helpdesk.assigned')}</th>
                  <th>{t('common.status')}</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((tk) => (
                  <tr key={tk.rawId}>
                    <td className="font-mono text-xs font-bold text-slate-400">{tk.id}</td>
                    <td className="font-semibold text-slate-200">{tk.customerName}</td>
                    <td>{tk.subject}</td>
                    <td><span className={`badge ${PRIORITY_TONE[tk.priority]}`}>{t(`priority.${tk.priority}`)}</span></td>
                    <td className="text-slate-400">{tk.assignedAgent}</td>
                    <td><span className={`badge ${STATUS_TONE[tk.status]}`}>{statusLabel[tk.status]}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
