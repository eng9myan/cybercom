'use client';

import React, { useState, useEffect } from 'react';
import { FileText, Send, CheckCircle, Clock, ExternalLink } from 'lucide-react';
import Link from 'next/link';

export default function SignDashboard() {
  const [stats, setStats] = useState({
    awaiting: 0,
    completed: 0,
    sent: 0,
    templates: 0
  });
  const [recentRequests, setRecentRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const templatesRes = await fetch('/api/sign/templates');
        const templatesData = await templatesRes.json();

        const requestsRes = await fetch('/api/sign/requests');
        const requestsData = await requestsRes.json();

        const awaiting = requestsData.filter((r: any) => r.status === 'Sent' || r.status === 'Viewed').length;
        const completed = requestsData.filter((r: any) => r.status === 'Signed').length;

        setStats({
          awaiting,
          completed,
          sent: requestsData.length,
          templates: templatesData.length
        });

        // Get recent 5 requests
        const sorted = [...requestsData].sort((a: any, b: any) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        ).slice(0, 5);
        setRecentRequests(sorted);
      } catch (err) {
        console.error('Failed to fetch dashboard stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">eSign Dashboard</h1>
          <p className="page-subtitle">Manage document templates, track signature requests, and review completed contracts.</p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Awaiting Signature</span>
            <p className="text-2xl font-black text-[#F59E0B]">{loading ? '...' : stats.awaiting}</p>
          </div>
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400">
            <Clock className="w-5 h-5" />
          </div>
        </div>
        
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Completed Signatures</span>
            <p className="text-2xl font-black text-[#10B981]">{loading ? '...' : stats.completed}</p>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
            <CheckCircle className="w-5 h-5" />
          </div>
        </div>

        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Sent Requests</span>
            <p className="text-2xl font-black text-[#3B82F6]">{loading ? '...' : stats.sent}</p>
          </div>
          <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400">
            <Send className="w-5 h-5" />
          </div>
        </div>

        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Templates</span>
            <p className="text-2xl font-black text-[#8B5CF6]">{loading ? '...' : stats.templates}</p>
          </div>
          <div className="p-3 rounded-xl bg-purple-500/10 text-purple-400">
            <FileText className="w-5 h-5" />
          </div>
        </div>
      </div>
      
      {/* Recent Activity Grid */}
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-white mb-4">Recent Signature Requests</h3>
        {loading ? (
          <p className="text-slate-500 text-xs italic">Loading activities...</p>
        ) : recentRequests.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-xs italic">
            No recent signature requests found. Go to <Link href="/sign/templates" className="text-rose-400 hover:underline">Templates</Link> to send one.
          </div>
        ) : (
          <div className="space-y-3">
            {recentRequests.map((req) => {
              const signer = req.signers?.[0] || { name: 'External Signer', email: '' };
              return (
                <div key={req.id} className="p-4 rounded-xl bg-white/3 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-black text-white">REQ-{req.id}</span>
                      <span className="text-[10px] text-slate-500">{new Date(req.created_at).toLocaleDateString()}</span>
                      <span className={`badge text-[9px] ${req.status === 'Signed' ? 'badge-green' : 'badge-yellow'}`}>
                        {req.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 font-bold">Recipient: {signer.name} {signer.email && `(${signer.email})`}</p>
                  </div>
                  
                  {req.status !== 'Signed' && (
                    <Link 
                      href={`/sign/public/${req.token}`} 
                      target="_blank"
                      className="p-1.5 px-3 text-[10px] font-bold rounded bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/25 text-[#FB7185] flex items-center gap-1.5 self-start md:self-center"
                    >
                      <span>Access Signing Portal</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
