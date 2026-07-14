'use client';

import React from 'react';
import { useCycomList, fmtCode, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';

type CycomTicket = {
  id: number;
  name?: string;
  partner_id?: Many2One;
  user_id?: Many2One;
  priority?: string;
  stage_id?: Many2One;
  team_id?: Many2One;
};

interface HelpTicket {
  rawId: number;
  id: string;
  customerName: string;
  subject: string;
  priority: 'High' | 'Medium' | 'Low';
  assignedAgent: string;
  status: 'New' | 'In Progress' | 'Resolved';
}

function priorityFromCycom(p?: string): 'High' | 'Medium' | 'Low' {
  if (p === '3' || p === '2') return 'High';
  if (p === '1') return 'Medium';
  return 'Low';
}

function statusFromStage(stageName: string): 'New' | 'In Progress' | 'Resolved' {
  const s = (stageName || '').toLowerCase();
  if (s.includes('resolved') || s.includes('done') || s.includes('closed')) return 'Resolved';
  if (s.includes('progress') || s.includes('working') || s.includes('open')) return 'In Progress';
  return 'New';
}

const mapTicket = (t: CycomTicket): HelpTicket => ({
  rawId: t.id,
  id: fmtCode('TKT', t.id, 3),
  customerName: m2oName(t.partner_id, '—'),
  subject: t.name || `Ticket ${t.id}`,
  priority: priorityFromCycom(t.priority),
  assignedAgent: m2oName(t.user_id, 'Unassigned'),
  status: t.stage_id ? statusFromStage(m2oName(t.stage_id)) : 'New',
});

export default function HelpdeskPage() {
  const { rows: tickets, loading, error } = useCycomList<CycomTicket, HelpTicket>(
    'helpdesk.ticket',
    [],
    ['name', 'partner_id', 'user_id', 'priority', 'stage_id', 'team_id'],
    mapTicket,
    { limit: 200, order: 'id desc' },
  );

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Helpdesk</h1>
          <p className="page-subtitle">Customer tickets with priority, agent assignment, and stage tracking.</p>
        </div>
      </div>

      {loading && <LoadingCard label="Loading tickets…" />}
      {error && <ErrorCard error={error} hint="Helpdesk requires the helpdesk module installed in Cycom. Run the Setup Hub → Helpdesk wizard (or install helpdesk from the Apps menu)." />}
      {!loading && !error && tickets.length === 0 && <EmptyCard label="No tickets yet. Receive support requests to populate this list." />}

      {!loading && !error && tickets.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Open Tickets</h2>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Customer</th>
                  <th>Subject</th>
                  <th>Priority</th>
                  <th>Assigned</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((t) => (
                  <tr key={t.rawId}>
                    <td className="font-mono text-xs font-bold text-slate-400">{t.id}</td>
                    <td className="font-semibold text-slate-200">{t.customerName}</td>
                    <td>{t.subject}</td>
                    <td>
                      <span className={`badge ${t.priority === 'High' ? 'badge-red' : t.priority === 'Medium' ? 'badge-yellow' : 'badge-cyan'}`}>{t.priority}</span>
                    </td>
                    <td className="text-slate-400">{t.assignedAgent}</td>
                    <td>
                      <span className={`badge ${t.status === 'Resolved' ? 'badge-green' : t.status === 'In Progress' ? 'badge-cyan' : 'badge-yellow'}`}>{t.status}</span>
                    </td>
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
