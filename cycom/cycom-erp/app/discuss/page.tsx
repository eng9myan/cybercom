'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCycomList, m2oName, type Many2One } from '@/lib/cycomModels';
import { MessageSquare, Send, Hash, Users, Search, Bell, Sparkles, Smile, ShieldAlert } from 'lucide-react';

interface Message {
  id: string;
  sender: string;
  avatar: string;
  content: string;
  time: string;
  isSelf: boolean;
}

interface Channel {
  id: string;
  name: string;
  unread: boolean;
  topic: string;
}

interface DM {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'away';
  role: string;
}

type CycomMailChannel = {
  id: number;
  name?: string;
  channel_type?: string;
  member_count?: number;
  last_interest_dt?: string;
};

const mapMailChannel = (r: CycomMailChannel): Channel => ({
  id: String(r.id),
  name: r.name || '—',
  unread: false,
  topic: r.channel_type || '',
});

const INITIAL_DMS: DM[] = [
  { id: 'sara', name: 'Sara Haddad', status: 'online', role: 'HR & Planning Lead' },
  { id: 'noor', name: 'Noor Al-Fayegh', status: 'away', role: 'Inventory Controller' },
  { id: 'lina', name: 'Lina Qudah', status: 'online', role: 'Finance Specialist' },
  { id: 'ahmad', name: 'Ahmad Masri', status: 'offline', role: 'POS Cashier Lead' }
];

const INITIAL_MESSAGES: Record<string, Message[]> = {
  general: [
    { id: '1', sender: 'Sara Haddad', avatar: 'SH', content: 'Welcome to the new Cycom ERP communication hub! ZK Biometric logs are fully active.', time: '09:15 AM', isSelf: false },
    { id: '2', sender: 'Lina Qudah', avatar: 'LQ', content: 'Indeed, accounting drafts look correct, we are auto-matching invoices successfully.', time: '09:20 AM', isSelf: false },
    { id: '3', sender: 'Admin User', avatar: 'AU', content: 'Awesome progress. Let me know if anyone notices any sync discrepancies.', time: '09:22 AM', isSelf: true }
  ],
  announcements: [
    { id: '1', sender: 'Admin User', avatar: 'AU', content: 'ANNOUNCEMENT: System upgrade to v19.4 stable successfully deployed. Branding remains strictly Cycom ERP.', time: 'Yesterday', isSelf: true },
    { id: '2', sender: 'Sara Haddad', avatar: 'SH', content: 'Understood. We are rolling out the employee portal GPS check-in parameters to everyone today.', time: 'Yesterday', isSelf: false }
  ],
  'supply-chain': [
    { id: '1', sender: 'Noor Al-Fayegh', avatar: 'NA', content: 'Discrepancy checker found a minor mismatch in Warehouse B inventory transfer. Resolving now.', time: '10:05 AM', isSelf: false }
  ],
  'hr-payroll': [
    { id: '1', sender: 'Sara Haddad', avatar: 'SH', content: 'Please review the attendance correction queue for ZK readers so we can run the payroll generator.', time: '08:30 AM', isSelf: false }
  ],
  'finance-ledger': [
    { id: '1', sender: 'Lina Qudah', avatar: 'LQ', content: 'Confirming we have enabled the safety margin limit checks on POS advance orders.', time: '11:10 AM', isSelf: false }
  ]
};

const BOT_REPLIES: string[] = [
  "Noted. I am checking the current Cycom core bridge status on Cycom ERP.",
  "Understood. The biometric logs are updating automatically.",
  "Let me coordinate with the Finance team regarding the JOD rounding calculations.",
  "Got it! I will check the inventory discrepancies dashboard.",
  "Acknowledged. Let's schedule a review session for this."
];

export default function DiscussPage() {
  const { rows: liveChannels, loading } = useCycomList<CycomMailChannel, Channel>(
    'mail.channel', [], ['name', 'channel_type', 'member_count', 'last_interest_dt'],
    mapMailChannel,
  );
  const [channels, setChannels] = useState<Channel[]>([]);
  const [dms, setDms] = useState<DM[]>(INITIAL_DMS);
  const [activeTab, setActiveTab] = useState<'channel' | 'dm'>('channel');
  const [activeId, setActiveId] = useState<string>('general');
  const [messages, setMessages] = useState<Record<string, Message[]>>(INITIAL_MESSAGES);
  const [inputText, setInputText] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Seed channels from live Backend data
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (!loading) setChannels(liveChannels); }, [loading]);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeId]);

  const activeChannel = channels.find(c => c.id === activeId);
  const activeDm = dms.find(d => d.id === activeId);
  const currentMessages = messages[activeId] || [];

  const handleSendMessage = () => {
    if (!inputText.trim()) return;

    const newMsg: Message = {
      id: Date.now().toString(),
      sender: 'Admin User',
      avatar: 'AU',
      content: inputText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isSelf: true
    };

    setMessages(prev => ({
      ...prev,
      [activeId]: [...(prev[activeId] || []), newMsg]
    }));

    setInputText('');

    // Simulate agent auto-reply
    setTimeout(() => {
      const randomReply = BOT_REPLIES[Math.floor(Math.random() * BOT_REPLIES.length)];
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: activeTab === 'channel' ? 'Cycom AI Bot' : activeDm?.name || 'User',
        avatar: activeTab === 'channel' ? 'AI' : (activeDm?.name.split(' ').map(n => n[0]).join('') || 'U'),
        content: randomReply,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isSelf: false
      };

      setMessages(prev => ({
        ...prev,
        [activeId]: [...(prev[activeId] || []), botMsg]
      }));
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const selectChannel = (id: string) => {
    setActiveTab('channel');
    setActiveId(id);
    setChannels(prev => prev.map(c => c.id === id ? { ...c, unread: false } : c));
  };

  const selectDM = (id: string) => {
    setActiveTab('dm');
    setActiveId(id);
  };

  const filteredChannels = channels.filter(c => c.name.toLowerCase().includes(searchQuery.toLowerCase()));
  const filteredDms = dms.filter(d => d.name.toLowerCase().includes(searchQuery.toLowerCase()));

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>Loading...</div>;

  return (
    <div className="space-y-6 max-w-[1200px] mx-auto">
      {/* Module Header */}
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title text-white">Discuss & Communication Hub</h1>
          <p className="page-subtitle">Internal channels, announcements, and direct messaging for Cycom operations.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-orange-500/10 border border-orange-500/20 text-[#E67E22]">
          <Sparkles className="w-3.5 h-3.5 animate-pulse" />
          <span className="text-[11px] font-bold">Cycom Sync Active</span>
        </div>
      </div>

      {/* Main Grid Container */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 h-[600px] items-stretch">
        
        {/* Left Sidebar (channels & direct messages list) */}
        <div className="glass-card flex flex-col p-4 md:col-span-1 border-r border-white/5 space-y-4 h-full overflow-hidden">
          {/* Search bar */}
          <div className="flex items-center gap-2 bg-white/3 border border-white/8 rounded-xl px-2.5 py-1.5 w-full">
            <Search className="w-3.5 h-3.5 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search chat or user..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent border-none outline-none text-xs text-white placeholder-slate-500 w-full"
            />
          </div>

          <div className="flex-1 overflow-y-auto space-y-5 pr-1">
            {/* Channels Section */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase block px-2">CHANNELS</span>
              <div className="space-y-0.5">
                {filteredChannels.map(ch => (
                  <button
                    key={ch.id}
                    onClick={() => selectChannel(ch.id)}
                    className={`w-full flex items-center justify-between px-2.5 py-2 rounded-xl text-xs transition-all border ${
                      activeTab === 'channel' && activeId === ch.id
                        ? 'bg-gradient-to-br from-orange-500/12 to-blue-500/8 border-orange-500/25 text-white'
                        : 'border-transparent text-slate-400 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Hash className={`w-3.5 h-3.5 ${activeTab === 'channel' && activeId === ch.id ? 'text-[#E67E22]' : 'text-slate-500'}`} />
                      <span className="truncate">{ch.name}</span>
                    </div>
                    {ch.unread && (
                      <span className="w-1.5 h-1.5 bg-[#E67E22] rounded-full animate-ping" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Direct Messages Section */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase block px-2">DIRECT MESSAGES</span>
              <div className="space-y-0.5">
                {filteredDms.map(dm => (
                  <button
                    key={dm.id}
                    onClick={() => selectDM(dm.id)}
                    className={`w-full flex items-center justify-between px-2.5 py-2 rounded-xl text-xs transition-all border ${
                      activeTab === 'dm' && activeId === dm.id
                        ? 'bg-gradient-to-br from-orange-500/12 to-blue-500/8 border-orange-500/25 text-white'
                        : 'border-transparent text-slate-400 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <div className="relative flex-shrink-0">
                        <div className="w-5 h-5 rounded bg-white/10 flex items-center justify-center text-[9px] font-black text-slate-300">
                          {dm.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <span className={`absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border border-black ${
                          dm.status === 'online' ? 'bg-[#10B981]' : dm.status === 'away' ? 'bg-[#F59E0B]' : 'bg-slate-600'
                        }`} />
                      </div>
                      <div className="text-left truncate">
                        <p className="font-semibold truncate">{dm.name}</p>
                        <p className="text-[8px] text-slate-500 truncate">{dm.role}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Active Chat Pane */}
        <div className="glass-card md:col-span-3 flex flex-col p-4 h-full overflow-hidden relative">
          
          {/* Active Header */}
          <div className="flex items-center justify-between border-b border-white/5 pb-3 mb-4">
            <div className="flex items-center gap-2.5">
              {activeTab === 'channel' ? (
                <>
                  <div className="p-1.5 rounded-lg bg-orange-500/10 border border-orange-500/25 text-[#E67E22]">
                    <Hash className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-white">#{activeChannel?.name}</h2>
                    <p className="text-[10px] text-slate-400 mt-0.5">{activeChannel?.topic}</p>
                  </div>
                </>
              ) : (
                <>
                  <div className="w-8 h-8 rounded bg-gradient-to-br from-[#E67E22] to-[#5DADE2] flex items-center justify-center text-xs font-bold text-white">
                    {activeDm?.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-white">{activeDm?.name}</h2>
                    <p className="text-[10px] text-slate-400 mt-0.5">{activeDm?.role} • Status: <span className="capitalize text-slate-300 font-semibold">{activeDm?.status}</span></p>
                  </div>
                </>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-[10px] bg-white/5 px-2.5 py-1 rounded-full text-slate-400 border border-white/5 font-mono">
                ZK Log Matcher Active
              </span>
            </div>
          </div>

          {/* Message History */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4 select-text">
            <AnimatePresence initial={false}>
              {currentMessages.map((msg, i) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 max-w-[80%] ${msg.isSelf ? 'ml-auto flex-row-reverse' : ''}`}
                >
                  <div className={`w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center text-[10px] font-black text-white ${
                    msg.isSelf 
                      ? 'bg-gradient-to-br from-[#E67E22] to-orange-600' 
                      : msg.sender === 'Cycom AI Bot' 
                        ? 'bg-gradient-to-br from-purple-500 to-indigo-600' 
                        : 'bg-white/10'
                  }`}>
                    {msg.avatar}
                  </div>
                  <div>
                    <div className={`flex items-baseline gap-2 mb-0.5 ${msg.isSelf ? 'justify-end' : ''}`}>
                      <span className="text-[10px] font-bold text-slate-300">{msg.sender}</span>
                      <span className="text-[8px] text-slate-500">{msg.time}</span>
                    </div>
                    <div className={`p-3 rounded-2xl text-xs leading-relaxed border ${
                      msg.isSelf 
                        ? 'bg-gradient-to-br from-orange-500/15 to-orange-500/5 border-orange-500/20 text-slate-200 rounded-tr-none' 
                        : msg.sender === 'Cycom AI Bot'
                          ? 'bg-gradient-to-br from-purple-500/15 to-indigo-500/5 border-purple-500/20 text-slate-200 rounded-tl-none'
                          : 'bg-white/3 border-white/5 text-slate-300 rounded-tl-none'
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input Panel */}
          <div className="mt-auto border-t border-white/5 pt-3 flex items-center gap-2 bg-[#090d19]">
            <button className="p-2 rounded-xl hover:bg-white/5 transition-colors text-slate-400 hover:text-white">
              <Smile className="w-4 h-4" />
            </button>
            <input
              type="text"
              placeholder={`Send message to ${activeTab === 'channel' ? '#' + activeChannel?.name : activeDm?.name}...`}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyPress}
              className="bg-transparent flex-1 border-none outline-none text-xs text-white placeholder-slate-500 py-2"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim()}
              className="p-2.5 rounded-xl bg-[#E67E22] hover:bg-orange-600 text-white disabled:opacity-40 disabled:hover:bg-[#E67E22] transition-all"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}
