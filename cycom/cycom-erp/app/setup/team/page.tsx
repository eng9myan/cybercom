'use client';

import React, { useEffect, useState } from 'react';
import { Users, Loader2, Trash2, Mail, Check, Clock } from 'lucide-react';
import { useT } from '@/lib/i18n';

type Role = { id: string; name: string; description: string };
type Assignment = { id: string; user_id: string; role: string };

function isPending(userId: string) {
  return userId.startsWith('pending:');
}
function emailOf(userId: string) {
  return userId.slice('pending:'.length);
}

export default function TeamRolesPage() {
  const t = useT();
  const [roles, setRoles] = useState<Role[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRoleId, setInviteRoleId] = useState('');
  const [inviting, setInviting] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [rolesRes, assignRes] = await Promise.all([
        fetch('/api/cycom/rest/access/roles/'),
        fetch('/api/cycom/rest/access/role-assignments/'),
      ]);
      if (!rolesRes.ok || !assignRes.ok) throw new Error(t('teamRoles.loadError'));
      const rolesData = await rolesRes.json();
      const assignData = await assignRes.json();
      const roleRows: Role[] = rolesData.results ?? rolesData;
      setRoles(roleRows);
      setAssignments(assignData.results ?? assignData);
      if (!inviteRoleId && roleRows.length) setInviteRoleId(roleRows[0].id);
    } catch (e: any) {
      setError(e.message || t('teamRoles.loadError'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const roleName = (id: string) => roles.find((r) => r.id === id)?.name || id;

  async function invite() {
    const email = inviteEmail.trim().toLowerCase();
    if (!email || !inviteRoleId) return;
    setInviting(true);
    setError(null);
    try {
      const res = await fetch('/api/cycom/rest/access/role-assignments/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: `pending:${email}`, role: inviteRoleId }),
      });
      if (!res.ok) throw new Error((await res.json())?.detail || t('teamRoles.inviteError'));
      setInviteEmail('');
      await load();
    } catch (e: any) {
      setError(e.message || t('teamRoles.inviteError'));
    } finally {
      setInviting(false);
    }
  }

  async function remove(a: Assignment) {
    setRemovingId(a.id);
    setError(null);
    try {
      const res = await fetch(`/api/cycom/rest/access/role-assignments/${a.id}/`, { method: 'DELETE' });
      if (!res.ok && res.status !== 204) throw new Error(t('teamRoles.removeError'));
      await load();
    } catch (e: any) {
      setError(e.message || t('teamRoles.removeError'));
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
      <header>
        <h1 className="page-title flex items-center gap-2"><Users className="w-5 h-5 text-[var(--cy-orange)]" /> {t('teamRoles.title')}</h1>
        <p className="page-subtitle">{t('teamRoles.subtitle')}</p>
      </header>

      <div className="glass-card p-5">
        <div className="text-sm font-semibold text-white mb-3">{t('teamRoles.inviteHeading')}</div>
        <div className="flex flex-wrap gap-2">
          <input
            type="email"
            className="input-field py-2 text-sm flex-1 min-w-[200px]"
            placeholder={t('teamRoles.emailPh')}
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
          />
          <select
            className="input-field py-2 text-sm w-48"
            value={inviteRoleId}
            onChange={(e) => setInviteRoleId(e.target.value)}
          >
            {roles.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
          <button
            onClick={invite}
            disabled={inviting || !inviteEmail.trim() || !inviteRoleId}
            className="btn-primary inline-flex items-center gap-1.5 text-xs px-4 disabled:opacity-60"
          >
            {inviting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Mail className="w-3.5 h-3.5" />}
            {t('teamRoles.inviteButton')}
          </button>
        </div>
        <p className="text-[11px] text-slate-500 mt-2">{t('teamRoles.inviteNote')}</p>
      </div>

      {error && (
        <div className="glass-card p-4 border border-rose-500/30 bg-rose-500/5 text-sm text-rose-300">{error}</div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16 text-slate-400 gap-2 text-sm">
          <Loader2 className="w-5 h-5 animate-spin" /> {t('common.loading')}
        </div>
      ) : (
        <div className="glass-card divide-y divide-white/5">
          {assignments.length === 0 && (
            <div className="py-12 text-center text-slate-500 text-sm">{t('teamRoles.empty')}</div>
          )}
          {assignments.map((a) => (
            <div key={a.id} className="flex items-center gap-3 px-5 py-3.5">
              {isPending(a.user_id) ? (
                <span className="badge badge-orange inline-flex items-center gap-1"><Clock className="w-3 h-3" /> {t('teamRoles.pending')}</span>
              ) : (
                <span className="badge badge-cyan inline-flex items-center gap-1"><Check className="w-3 h-3" /> {t('teamRoles.active')}</span>
              )}
              <div className="flex-1 min-w-0">
                <div className="text-sm text-white truncate">{isPending(a.user_id) ? emailOf(a.user_id) : a.user_id}</div>
              </div>
              <span className="badge badge-purple shrink-0">{roleName(a.role)}</span>
              <button
                onClick={() => remove(a)}
                disabled={removingId === a.id}
                className="text-slate-500 hover:text-rose-400 disabled:opacity-50 p-1.5"
                title={t('teamRoles.remove')}
              >
                {removingId === a.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
