'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useCycomList, m2oName, fmtDate, type Many2One } from '@/lib/cycomModels';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FolderOpen, Folder, Plus, Trash2, Download, Search, 
  FileText, ShieldCheck, Tag, Info, CheckCircle, PenTool,
  Send, Sparkles, Mail, Users, FileSignature, ShieldAlert, Award, RefreshCw, X
} from 'lucide-react';

interface DocFile {
  id: string;
  name: string;
  size: string;
  tag: 'Invoice' | 'Contract' | 'ID' | 'Report' | 'Other';
  workspace: 'Finance' | 'HR' | 'Operations' | 'Legal';
  dateUploaded: string;
}

interface ESignRequest {
  id: string;
  fileName: string;
  signerName: string;
  signerEmail: string;
  role: 'Contractor' | 'Customer' | 'Employee' | 'Witness';
  status: 'Pending Signature' | 'Fully Signed';
  dateRequested: string;
  dateSigned?: string;
  sha256?: string;
}

type CycomDocument = {
  id: number;
  name?: string;
  type?: string;
  owner_id?: Many2One;
  folder_id?: Many2One;
  create_date?: string;
};

const VALID_WORKSPACES: DocFile['workspace'][] = ['Finance', 'HR', 'Operations', 'Legal'];

const mapDocument = (r: CycomDocument): DocFile => {
  const folderName = m2oName(r.folder_id);
  return {
    id: `DOC-${r.id}`,
    name: r.name || '—',
    size: '—',
    tag: 'Other',
    workspace: (VALID_WORKSPACES.includes(folderName as DocFile['workspace']) ? folderName as DocFile['workspace'] : 'Finance'),
    dateUploaded: fmtDate(r.create_date),
  };
};

const INITIAL_ESIGN_REQUESTS: ESignRequest[] = [
  { id: 'SIG-901', fileName: 'Zaid_Food_Contract_2026.pdf', signerName: 'Zaid Al-Fayegh', signerEmail: 'zaid@fayeghfoods.jo', role: 'Contractor', status: 'Pending Signature', dateRequested: '2026-06-14' },
  { id: 'SIG-902', fileName: 'Sales_Lease_HQ_Amman.pdf', signerName: 'Sara Haddad', signerEmail: 'sara.h@cycom.jo', role: 'Witness', status: 'Fully Signed', dateRequested: '2026-06-10', dateSigned: '2026-06-11', sha256: 'a98f12c19e5d482c91a03e1f0e4b859e21054a86cd75e9b891ab0f1b2c48d90e' },
  { id: 'SIG-903', fileName: 'Warehouse_Operator_Agreement.pdf', signerName: 'Khaled Jaber', signerEmail: 'khaled@cycom.jo', role: 'Employee', status: 'Fully Signed', dateRequested: '2026-06-12', dateSigned: '2026-06-12', sha256: '7ff12ea39c4a8bb1e247cf73b9e4a7d6d1b26f59013c77d48386376c7cde9a3e' },
];

const WORKSPACES: Array<'Finance' | 'HR' | 'Operations' | 'Legal'> = ['Finance', 'HR', 'Operations', 'Legal'];
const TAGS: Array<'Invoice' | 'Contract' | 'ID' | 'Report' | 'Other'> = ['Invoice', 'Contract', 'ID', 'Report', 'Other'];

export default function DocumentsPage() {
  const { rows: liveDocs, loading } = useCycomList<CycomDocument, DocFile>(
    'documents.document', [], ['name', 'type', 'owner_id', 'folder_id', 'create_date'],
    mapDocument,
  );
  const [activeTab, setActiveTab] = useState<'dms' | 'esign'>('dms');
  const [files, setFiles] = useState<DocFile[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<'Finance' | 'HR' | 'Operations' | 'Legal'>('Finance');
  const [tagFilter, setTagFilter] = useState<string>('All');
  const [search, setSearch] = useState('');

  // eSign States
  const [esignRequests, setESignRequests] = useState<ESignRequest[]>(INITIAL_ESIGN_REQUESTS);
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [isSignModalOpen, setIsSignModalOpen] = useState(false);
  const [isCertificateModalOpen, setIsCertificateModalOpen] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<ESignRequest | null>(null);

  // New Request Form States
  const [reqFileName, setReqFileName] = useState('');
  const [reqSignerName, setReqSignerName] = useState('');
  const [reqSignerEmail, setReqSignerEmail] = useState('');
  const [reqRole, setReqRole] = useState<'Contractor' | 'Customer' | 'Employee' | 'Witness'>('Customer');

  // Interactive Sign Drawer States
  const [signMethod, setSignMethod] = useState<'draw' | 'type'>('draw');
  const [typedName, setTypedName] = useState('');
  const [signCompleted, setSignCompleted] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);

  // DMS Upload Form states
  const [fileName, setFileName] = useState('');
  const [fileSize, setFileSize] = useState('1.2 MB');
  const [fileTag, setFileTag] = useState<'Invoice' | 'Contract' | 'ID' | 'Report' | 'Other'>('Invoice');
  const [fileSuccess, setFileSuccess] = useState(false);

  // Canvas drawing handlers
  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Clear drawing pad instruction text on first click/drag
    ctx.beginPath();
    const rect = canvas.getBoundingClientRect();
    ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
    setIsDrawing(true);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
    ctx.strokeStyle = '#5DADE2'; // Blue signature ink
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  // Seed files from live Backend data
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (!loading) setFiles(liveDocs); }, [loading]);

  // Pre-initialize canvas styling when modal opens
  useEffect(() => {
    if (isSignModalOpen && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
  }, [isSignModalOpen]);

  // DMS upload
  const handleUploadFile = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileName) return;

    const newFile: DocFile = {
      id: `DOC-${Math.floor(505 + Math.random() * 200)}`,
      name: fileName.endsWith('.pdf') || fileName.endsWith('.docx') || fileName.endsWith('.xlsx') || fileName.endsWith('.jpg') ? fileName : `${fileName}.pdf`,
      size: fileSize,
      tag: fileTag,
      workspace: selectedWorkspace,
      dateUploaded: new Date().toISOString().split('T')[0]
    };

    setFiles([newFile, ...files]);
    setFileName('');
    setFileSuccess(true);
    setTimeout(() => setFileSuccess(false), 2500);
  };

  const handleDeleteFile = (id: string) => {
    setFiles(files.filter(f => f.id !== id));
  };

  const filteredFiles = files.filter(f => 
    f.workspace === selectedWorkspace &&
    (tagFilter === 'All' || f.tag === tagFilter) &&
    f.name.toLowerCase().includes(search.toLowerCase())
  );

  // eSign dispatch
  const handleRequestSign = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reqFileName || !reqSignerName || !reqSignerEmail) return;

    const newReq: ESignRequest = {
      id: `SIG-9${esignRequests.length + 1}`,
      fileName: reqFileName,
      signerName: reqSignerName,
      signerEmail: reqSignerEmail,
      role: reqRole,
      status: 'Pending Signature',
      dateRequested: new Date().toISOString().split('T')[0]
    };

    setESignRequests([newReq, ...esignRequests]);
    setIsRequestModalOpen(false);

    // Reset Form
    setReqFileName('');
    setReqSignerName('');
    setReqSignerEmail('');
  };

  // Complete signature
  const handleSubmitSignature = () => {
    if (!selectedRequest) return;

    const randomHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
    
    setESignRequests(prev => prev.map(req => {
      if (req.id === selectedRequest.id) {
        return {
          ...req,
          status: 'Fully Signed',
          dateSigned: new Date().toISOString().split('T')[0],
          sha256: randomHash
        };
      }
      return req;
    }));

    setSignCompleted(true);
    setTimeout(() => {
      setIsSignModalOpen(false);
      setSignCompleted(false);
      setSelectedRequest(null);
      setTypedName('');
    }, 1500);
  };

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="page-title text-white">Documents DMS & eSign</h1>
          <p className="page-subtitle">Categorize files, manage secure document lockers, and request/simulate legally-binding signatures.</p>
        </div>
        
        {/* Module Switcher Tabs */}
        <div className="flex bg-black/25 p-1 border border-white/5 rounded-xl text-xs font-semibold text-slate-400">
          <button
            onClick={() => setActiveTab('dms')}
            className={`px-4 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'dms' ? 'bg-[#E67E22] text-white shadow' : 'hover:text-white'
            }`}
          >
            <FolderOpen className="w-3.5 h-3.5" />
            DMS Explorer
          </button>
          <button
            onClick={() => setActiveTab('esign')}
            className={`px-4 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'esign' ? 'bg-[#E67E22] text-white shadow' : 'hover:text-white'
            }`}
          >
            <FileSignature className="w-3.5 h-3.5" />
            eSign Workflows
          </button>
        </div>
      </div>

      {/* DMS TAB VIEW */}
      {activeTab === 'dms' && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column - Workspaces Folders */}
          <div className="space-y-4">
            <div className="glass-card p-5 space-y-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-2.5 flex items-center gap-1.5">
                <FolderOpen className="w-4 h-4 text-cyan-400" /> DMS Workspaces
              </h2>
              <div className="space-y-1">
                {WORKSPACES.map(ws => (
                  <div
                    key={ws}
                    onClick={() => { setSelectedWorkspace(ws); setTagFilter('All'); }}
                    className={`p-3 rounded-xl flex items-center gap-3 cursor-pointer border transition-all ${
                      selectedWorkspace === ws 
                        ? 'bg-gradient-to-br from-orange-500/12 to-blue-500/8 border-orange-500/25 text-white' 
                        : 'border-transparent hover:bg-white/3 text-slate-400'
                    }`}
                  >
                    <Folder className={`w-4 h-4 ${selectedWorkspace === ws ? 'text-[#E67E22]' : 'text-slate-500'}`} />
                    <span className="text-xs font-bold">{ws} Workspace</span>
                    <span className="ml-auto text-[9px] bg-white/5 px-1.5 py-0.2 rounded font-bold font-mono">
                      {files.filter(f => f.workspace === ws).length}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Add file in workspace */}
            <div className="glass-card p-5 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-2">Upload to {selectedWorkspace}</h3>
              
              {fileSuccess ? (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-center text-xs space-y-2">
                  <CheckCircle className="w-8 h-8 mx-auto animate-bounce" />
                  <p className="font-bold">File Uploaded successfully</p>
                </div>
              ) : (
                <form onSubmit={handleUploadFile} className="space-y-3 text-xs">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">File Name</label>
                    <input 
                      type="text" 
                      required 
                      placeholder="e.g. Agreement_draft" 
                      value={fileName}
                      onChange={e => setFileName(e.target.value)}
                      className="input-field py-1"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-500 uppercase">Doc Tag</label>
                      <select 
                        value={fileTag} 
                        onChange={e => setFileTag(e.target.value as any)}
                        className="input-field py-1"
                      >
                        {TAGS.map(t => <option key={t} value={t}>{t}</option>)}
                      </select>
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-500 uppercase">Sim. Size</label>
                      <input 
                        type="text" 
                        value={fileSize}
                        onChange={e => setFileSize(e.target.value)}
                        placeholder="e.g. 1.2 MB" 
                        className="input-field py-1 font-mono"
                      />
                    </div>
                  </div>
                  <button type="submit" className="btn-primary w-full py-1.5 mt-2">
                    Upload Simulator
                  </button>
                </form>
              )}
            </div>
          </div>

          {/* Right Column - Files Grid & Filters */}
          <div className="lg:col-span-3 glass-card p-5 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-white/5 pb-3 gap-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{selectedWorkspace} Folder Contents</h2>
              
              <div className="flex items-center gap-3 text-xs">
                {/* Search */}
                <div className="flex items-center gap-2 bg-white/3 border border-white/8 rounded-xl px-2.5 py-1">
                  <Search className="w-3.5 h-3.5 text-slate-500" />
                  <input 
                    type="text" 
                    placeholder="Filter name..." 
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="bg-transparent border-none outline-none text-[11px] text-white placeholder-slate-500 w-[120px]"
                  />
                </div>

                {/* Tag filters */}
                <div className="flex gap-1">
                  {['All', ...TAGS].map(t => (
                    <button
                      key={t}
                      onClick={() => setTagFilter(t)}
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-colors ${
                        tagFilter === t 
                          ? 'bg-[#E67E22]/20 border-[#E67E22]/40 text-[#E67E22]' 
                          : 'border-transparent text-slate-400 hover:text-white'
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              {filteredFiles.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-10 text-center">No documents matching this filter in {selectedWorkspace} Workspace.</p>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Doc ID</th>
                      <th>Document Name</th>
                      <th>Tag category</th>
                      <th>Workspace</th>
                      <th>File Size</th>
                      <th>Upload Date</th>
                      <th className="text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFiles.map(file => (
                      <tr key={file.id}>
                        <td className="font-mono text-xs">{file.id}</td>
                        <td className="font-bold text-slate-200">
                          <span className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-slate-500" />
                            {file.name}
                          </span>
                        </td>
                        <td>
                          <span className={`badge text-[9px] ${
                            file.tag === 'Invoice' ? 'badge-orange' :
                            file.tag === 'Contract' ? 'badge-cyan' :
                            file.tag === 'ID' ? 'badge-purple' : 'badge-green'
                          }`}>{file.tag}</span>
                        </td>
                        <td className="text-xs text-slate-500">{file.workspace}</td>
                        <td className="font-mono">{file.size}</td>
                        <td className="font-mono text-slate-400">{file.dateUploaded}</td>
                        <td className="text-right">
                          <div className="flex gap-1 justify-end">
                            <button className="p-1 rounded hover:bg-white/5 text-slate-400 hover:text-white">
                              <Download className="w-3.5 h-3.5" />
                            </button>
                            <button 
                              onClick={() => handleDeleteFile(file.id)}
                              className="p-1 rounded hover:bg-red-500/20 text-[#EF4444]"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      {/* eSIGN WORKFLOWS TAB VIEW */}
      {activeTab === 'esign' && (
        <div className="space-y-6">
          {/* Stats Bar */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="glass-card p-4 space-y-1">
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">Total Sent Requests</span>
              <p className="text-xl font-black text-white">{esignRequests.length} files</p>
              <span className="text-[10px] text-slate-400">Authorized eSign ledger entries</span>
            </div>
            <div className="glass-card p-4 space-y-1">
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">Signed & Secured</span>
              <p className="text-xl font-black text-emerald-400">{esignRequests.filter(r => r.status === 'Fully Signed').length} files</p>
              <span className="text-[10px] text-emerald-500 font-bold inline-flex items-center gap-0.5">
                <ShieldCheck className="w-3.5 h-3.5" /> 100% Audit Traceable
              </span>
            </div>
            <div className="glass-card p-4 space-y-1">
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">Awaiting Action</span>
              <p className="text-xl font-black text-amber-400">{esignRequests.filter(r => r.status === 'Pending Signature').length} files</p>
              <span className="text-[10px] text-amber-500">Requires recipient signoff</span>
            </div>
          </div>

          {/* eSign ledger panel */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-white/5 pb-3.5">
              <h2 className="text-xs font-bold uppercase tracking-wider text-white">eSign Signature Requests Ledger</h2>
              <button
                onClick={() => setIsRequestModalOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#E67E22] hover:bg-orange-600 text-white text-xs font-semibold transition-all shadow-md shadow-orange-500/10"
              >
                <Send className="w-3.5 h-3.5" />
                Request Signature
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Request Ref</th>
                    <th>Document Name</th>
                    <th>Recipient</th>
                    <th>Role</th>
                    <th>Date Sent</th>
                    <th>Completion Date</th>
                    <th>Status</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {esignRequests.map(req => (
                    <tr key={req.id}>
                      <td className="font-mono text-xs font-bold text-slate-400">{req.id}</td>
                      <td className="font-semibold text-slate-200">
                        <span className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-slate-500" />
                          {req.fileName}
                        </span>
                      </td>
                      <td>
                        <div>
                          <p className="font-semibold text-slate-200">{req.signerName}</p>
                          <p className="text-[9px] text-slate-500 font-mono">{req.signerEmail}</p>
                        </div>
                      </td>
                      <td className="text-xs text-slate-400">{req.role}</td>
                      <td className="font-mono text-slate-400">{req.dateRequested}</td>
                      <td className="font-mono text-slate-400">{req.dateSigned || '—'}</td>
                      <td>
                        <span className={`badge text-[9px] ${
                          req.status === 'Fully Signed' 
                            ? 'badge-green' 
                            : 'badge-orange'
                        }`}>{req.status}</span>
                      </td>
                      <td className="text-right">
                        <div className="flex gap-2 justify-end">
                          {req.status === 'Pending Signature' ? (
                            <button
                              onClick={() => { setSelectedRequest(req); setIsSignModalOpen(true); }}
                              className="px-2 py-1 bg-[#E67E22]/10 border border-[#E67E22]/20 text-[#E67E22] hover:bg-[#E67E22]/20 rounded text-[10px] font-bold transition-all"
                            >
                              Sign Now
                            </button>
                          ) : (
                            <button
                              onClick={() => { setSelectedRequest(req); setIsCertificateModalOpen(true); }}
                              className="px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 rounded text-[10px] font-bold transition-all flex items-center gap-1"
                            >
                              <ShieldCheck className="w-3 h-3" /> Audit Log
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* REQUEST SIGNATURE MODAL */}
      <AnimatePresence>
        {isRequestModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card max-w-md w-full p-6 space-y-4 relative"
            >
              <button
                onClick={() => setIsRequestModalOpen(false)}
                className="absolute top-4 right-4 text-slate-500 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="space-y-1">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">Send Signature Request</h2>
                <p className="text-[10px] text-slate-500">Dispatch an eSign contract request via the Cycom Secure Signoff module.</p>
              </div>

              <form onSubmit={handleRequestSign} className="space-y-3 text-xs">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">Select Document</label>
                  <select
                    required
                    value={reqFileName}
                    onChange={(e) => setReqFileName(e.target.value)}
                    className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-orange-500/50"
                  >
                    <option value="" className="bg-[#0a0f1e]">-- Choose File --</option>
                    {files.map(f => (
                      <option key={f.id} value={f.name} className="bg-[#0a0f1e]">{f.name} ({f.size})</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">Recipient Full Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Zaid Al-Fayegh"
                    value={reqSignerName}
                    onChange={(e) => setReqSignerName(e.target.value)}
                    className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-orange-500/50"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">Recipient Email Address</label>
                  <input
                    type="email"
                    required
                    placeholder="e.g. client@domain.jo"
                    value={reqSignerEmail}
                    onChange={(e) => setReqSignerEmail(e.target.value)}
                    className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-orange-500/50"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">Signer Role</label>
                  <select
                    value={reqRole}
                    onChange={(e) => setReqRole(e.target.value as any)}
                    className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-orange-500/50"
                  >
                    <option value="Customer" className="bg-[#0a0f1e]">Customer / Client</option>
                    <option value="Contractor" className="bg-[#0a0f1e]">Contractor / Partner</option>
                    <option value="Employee" className="bg-[#0a0f1e]">Employee</option>
                    <option value="Witness" className="bg-[#0a0f1e]">Authorized Witness</option>
                  </select>
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsRequestModalOpen(false)}
                    className="flex-1 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-semibold transition-colors border border-white/10"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-2 rounded-xl bg-[#E67E22] hover:bg-orange-600 text-white text-xs font-semibold transition-colors shadow-md shadow-orange-500/10"
                  >
                    Send Request
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* SIGN NOW SIMULATOR MODAL */}
      <AnimatePresence>
        {isSignModalOpen && selectedRequest && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card max-w-lg w-full p-6 space-y-4 relative"
            >
              <button
                onClick={() => setIsSignModalOpen(false)}
                className="absolute top-4 right-4 text-slate-500 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="space-y-1 border-b border-white/5 pb-2">
                <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-orange-500/10 text-[#E67E22] text-[9px] font-bold border border-orange-500/25">
                  <PenTool className="w-3 h-3" />
                  ESIGN SECURE PROTOCOL
                </div>
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">Sign Document: {selectedRequest.fileName}</h2>
                <p className="text-[10px] text-slate-400">Signing as recipient: <strong className="text-white">{selectedRequest.signerName}</strong> ({selectedRequest.signerEmail})</p>
              </div>

              {signCompleted ? (
                <div className="py-12 flex flex-col items-center justify-center space-y-3">
                  <motion.div
                    initial={{ scale: 0.5, rotate: -45 }}
                    animate={{ scale: 1, rotate: 0 }}
                    className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center"
                  >
                    <CheckCircle className="w-10 h-10 animate-pulse" />
                  </motion.div>
                  <p className="text-xs font-bold text-emerald-400">Document Signed & Cryptographically Locked</p>
                  <p className="text-[9px] text-slate-500 font-mono">Syncing verification codes with ZK Ledger...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Visual Document Mockup Sheet */}
                  <div className="p-4 rounded-xl bg-white/2 border border-white/5 text-[9px] text-slate-400 leading-relaxed font-serif relative min-h-[120px] select-none">
                    <p className="font-bold text-[10px] text-slate-200 mb-2">AGREEMENT & SERVICE ACCEPTANCE DEED</p>
                    <p>This legally binding deed is entered between CYCOM ERP CO. (Cycom ERP Operations) and the undersigned recipient. The signer agrees to the general terms, digital logs, and transaction audit records.</p>
                    
                    {/* Golden Signature Placeholder Target Box */}
                    <div className="mt-4 border border-dashed border-[#E67E22]/50 bg-[#E67E22]/5 p-2 rounded flex items-center justify-between">
                      <div>
                        <span className="text-[8px] text-slate-500 uppercase block font-sans">Authorized Signatory</span>
                        <span className="text-[#E67E22] font-semibold font-sans">{selectedRequest.signerName} ({selectedRequest.role})</span>
                      </div>
                      <div className="w-20 h-6 border-b border-orange-400 flex items-center justify-center font-cursive text-cyan-400 text-xs italic">
                        {signMethod === 'type' && typedName ? typedName : 'Draw Pad Active'}
                      </div>
                    </div>
                  </div>

                  {/* Method selector */}
                  <div className="flex gap-2 border-b border-white/5 pb-2 text-[10px] font-semibold">
                    <button
                      onClick={() => setSignMethod('draw')}
                      className={`px-3 py-1 rounded-lg ${signMethod === 'draw' ? 'bg-[#E67E22] text-white' : 'text-slate-400 hover:text-white'}`}
                    >
                      Draw Signature
                    </button>
                    <button
                      onClick={() => setSignMethod('type')}
                      className={`px-3 py-1 rounded-lg ${signMethod === 'type' ? 'bg-[#E67E22] text-white' : 'text-slate-400 hover:text-white'}`}
                    >
                      Type Signature
                    </button>
                  </div>

                  {/* Signature pad elements */}
                  {signMethod === 'draw' ? (
                    <div className="space-y-1">
                      <div className="flex justify-between items-center text-[10px]">
                        <span className="text-slate-400">Draw with mouse or touchpad:</span>
                        <button
                          onClick={clearCanvas}
                          className="text-[#EF4444] hover:text-red-400 text-[9px] font-bold"
                        >
                          Clear Board
                        </button>
                      </div>
                      <div className="relative border border-white/10 rounded-xl overflow-hidden bg-black/40">
                        <canvas
                          ref={canvasRef}
                          width={448}
                          height={120}
                          onMouseDown={startDrawing}
                          onMouseMove={draw}
                          onMouseUp={stopDrawing}
                          onMouseLeave={stopDrawing}
                          className="cursor-crosshair w-full block h-[120px]"
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-500 uppercase">Type Signature Name</label>
                      <input
                        type="text"
                        placeholder="Type full name for script conversion"
                        value={typedName}
                        onChange={(e) => setTypedName(e.target.value)}
                        className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-orange-500/50"
                      />
                      {typedName && (
                        <div className="p-3 rounded-xl bg-white/3 border border-white/5 text-center">
                          <span className="text-xs text-slate-400 block mb-1">Cursive Signature Preview:</span>
                          <span className="font-cursive text-lg text-cyan-400 italic font-medium leading-none tracking-wide">
                            {typedName}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => setIsSignModalOpen(false)}
                      className="flex-1 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-semibold transition-colors border border-white/10"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSubmitSignature}
                      className="flex-1 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold transition-colors shadow-md shadow-emerald-500/10"
                    >
                      Apply Signature
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* AUDIT CERTIFICATE LOG MODAL */}
      <AnimatePresence>
        {isCertificateModalOpen && selectedRequest && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card max-w-md w-full p-6 space-y-4 relative"
            >
              <button
                onClick={() => setIsCertificateModalOpen(false)}
                className="absolute top-4 right-4 text-slate-500 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="space-y-1 text-center border-b border-white/5 pb-3">
                <Award className="w-10 h-10 text-emerald-400 mx-auto animate-pulse" />
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">Cycom Secure Sign Certificate</h2>
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest text-emerald-400">Status: Legally Verified & Audited</p>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3.5 rounded-xl bg-white/3 border border-white/5 space-y-2.5">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Document Ref:</span>
                    <span className="font-bold text-slate-300">{selectedRequest.id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">File Name:</span>
                    <span className="font-bold text-slate-300 font-mono">{selectedRequest.fileName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Signed By:</span>
                    <span className="font-bold text-slate-300">{selectedRequest.signerName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Signer Email:</span>
                    <span className="font-bold text-[#5DADE2] font-mono">{selectedRequest.signerEmail}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Signer Role:</span>
                    <span className="font-bold text-slate-300">{selectedRequest.role}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Sent Date:</span>
                    <span className="font-bold text-slate-300 font-mono">{selectedRequest.dateRequested}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Signing Date:</span>
                    <span className="font-bold text-emerald-400 font-mono">{selectedRequest.dateSigned}</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">SHA-256 Ledger Integrity Stamp</label>
                  <div className="p-2.5 rounded-lg bg-black/40 border border-white/5 text-[9px] font-mono text-emerald-400 break-all leading-normal">
                    {selectedRequest.sha256}
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#10B981]/5 border border-[#10B981]/20 text-[10px] text-slate-400 leading-normal flex items-start gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <p>This signature is authenticated via **Cycom ZK cryptographic logs**. Any alteration to the original document invalidates this hash.</p>
                </div>
              </div>

              <button
                onClick={() => setIsCertificateModalOpen(false)}
                className="w-full py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-semibold transition-colors border border-white/10"
              >
                Close Certificate
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
