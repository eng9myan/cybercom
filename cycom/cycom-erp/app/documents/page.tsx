'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useCycomList, m2oName, fmtDate, type Many2One } from '@/lib/cycomModels';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FolderOpen, Folder, Plus, Trash2, Download, Search,
  FileText, ShieldCheck, CheckCircle, PenTool,
  Send, FileSignature, Award, X
} from 'lucide-react';
import { useT } from '@/lib/i18n';

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
  const t = useT();
  const WS_LABEL: Record<DocFile['workspace'], string> = {
    Finance: t('documentsPage.wsFinance'), HR: t('documentsPage.wsHr'),
    Operations: t('documentsPage.wsOperations'), Legal: t('documentsPage.wsLegal'),
  };
  const TAG_LABEL: Record<DocFile['tag'], string> = {
    Invoice: t('documentsPage.tagInvoice'), Contract: t('documentsPage.tagContract'),
    ID: t('documentsPage.tagId'), Report: t('documentsPage.tagReport'), Other: t('documentsPage.tagOther'),
  };
  const ROLE_LABEL: Record<ESignRequest['role'], string> = {
    Contractor: t('documentsPage.roleContractor'), Customer: t('documentsPage.roleCustomer'),
    Employee: t('documentsPage.roleEmployee'), Witness: t('documentsPage.roleWitness'),
  };

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

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>{t('attendanceMain.loading')}</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="page-title text-white">{t('documentsPage.title')}</h1>
          <p className="page-subtitle">{t('documentsPage.subtitle')}</p>
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
            {t('documentsPage.tabDms')}
          </button>
          <button
            onClick={() => setActiveTab('esign')}
            className={`px-4 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'esign' ? 'bg-[#E67E22] text-white shadow' : 'hover:text-white'
            }`}
          >
            <FileSignature className="w-3.5 h-3.5" />
            {t('documentsPage.tabEsign')}
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
                <FolderOpen className="w-4 h-4 text-cyan-400" /> {t('documentsPage.workspacesHeading')}
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
                    <span className="text-xs font-bold">{WS_LABEL[ws]} {t('documentsPage.workspaceSuffix')}</span>
                    <span className="ms-auto text-[9px] bg-white/5 px-1.5 py-0.2 rounded font-bold font-mono">
                      {files.filter(f => f.workspace === ws).length}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Add file in workspace */}
            <div className="glass-card p-5 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-2">{t('documentsPage.uploadTo', { workspace: WS_LABEL[selectedWorkspace] })}</h3>

              {fileSuccess ? (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-center text-xs space-y-2">
                  <CheckCircle className="w-8 h-8 mx-auto animate-bounce" />
                  <p className="font-bold">{t('documentsPage.fileUploadedSuccess')}</p>
                </div>
              ) : (
                <form onSubmit={handleUploadFile} className="space-y-3 text-xs">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">{t('documentsPage.fileName')}</label>
                    <input
                      type="text"
                      required
                      placeholder={t('documentsPage.fileNamePh')}
                      value={fileName}
                      onChange={e => setFileName(e.target.value)}
                      className="input-field py-1"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-500 uppercase">{t('documentsPage.docTag')}</label>
                      <select
                        value={fileTag}
                        onChange={e => setFileTag(e.target.value as any)}
                        className="input-field py-1"
                      >
                        {TAGS.map(tg => <option key={tg} value={tg}>{TAG_LABEL[tg]}</option>)}
                      </select>
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-500 uppercase">{t('documentsPage.simSize')}</label>
                      <input
                        type="text"
                        value={fileSize}
                        onChange={e => setFileSize(e.target.value)}
                        placeholder={t('documentsPage.simSizePh')}
                        className="input-field py-1 font-mono"
                      />
                    </div>
                  </div>
                  <button type="submit" className="btn-primary w-full py-1.5 mt-2">
                    {t('documentsPage.uploadSimulator')}
                  </button>
                </form>
              )}
            </div>
          </div>

          {/* Right Column - Files Grid & Filters */}
          <div className="lg:col-span-3 glass-card p-5 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-white/5 pb-3 gap-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('documentsPage.folderContents', { workspace: WS_LABEL[selectedWorkspace] })}</h2>

              <div className="flex items-center gap-3 text-xs">
                {/* Search */}
                <div className="flex items-center gap-2 bg-white/3 border border-white/8 rounded-xl px-2.5 py-1">
                  <Search className="w-3.5 h-3.5 text-slate-500" />
                  <input
                    type="text"
                    placeholder={t('documentsPage.searchFilterPh')}
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="bg-transparent border-none outline-none text-[11px] text-white placeholder-slate-500 w-[120px]"
                  />
                </div>

                {/* Tag filters */}
                <div className="flex gap-1">
                  {(['All', ...TAGS] as const).map(tg => (
                    <button
                      key={tg}
                      onClick={() => setTagFilter(tg)}
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-colors ${
                        tagFilter === tg
                          ? 'bg-[#E67E22]/20 border-[#E67E22]/40 text-[#E67E22]'
                          : 'border-transparent text-slate-400 hover:text-white'
                      }`}
                    >
                      {tg === 'All' ? t('documentsPage.tagAll') : TAG_LABEL[tg]}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              {filteredFiles.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-10 text-center">{t('documentsPage.noDocsFilter', { workspace: WS_LABEL[selectedWorkspace] })}</p>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{t('documentsPage.colDocId')}</th>
                      <th>{t('documentsPage.colDocumentName')}</th>
                      <th>{t('documentsPage.colTagCategory')}</th>
                      <th>{t('documentsPage.colWorkspace')}</th>
                      <th>{t('documentsPage.colFileSize')}</th>
                      <th>{t('documentsPage.colUploadDate')}</th>
                      <th className="text-end">{t('documentsPage.colActions')}</th>
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
                          }`}>{TAG_LABEL[file.tag]}</span>
                        </td>
                        <td className="text-xs text-slate-500">{WS_LABEL[file.workspace]}</td>
                        <td className="font-mono">{file.size}</td>
                        <td className="font-mono text-slate-400">{file.dateUploaded}</td>
                        <td className="text-end">
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
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">{t('documentsPage.totalSentRequests')}</span>
              <p className="text-xl font-black text-white">{t('documentsPage.filesN', { n: esignRequests.length })}</p>
              <span className="text-[10px] text-slate-400">{t('documentsPage.authorizedLedgerEntries')}</span>
            </div>
            <div className="glass-card p-4 space-y-1">
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">{t('documentsPage.signedSecured')}</span>
              <p className="text-xl font-black text-emerald-400">{t('documentsPage.filesN', { n: esignRequests.filter(r => r.status === 'Fully Signed').length })}</p>
              <span className="text-[10px] text-emerald-500 font-bold inline-flex items-center gap-0.5">
                <ShieldCheck className="w-3.5 h-3.5" /> {t('documentsPage.auditTraceable')}
              </span>
            </div>
            <div className="glass-card p-4 space-y-1">
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block">{t('documentsPage.awaitingAction')}</span>
              <p className="text-xl font-black text-amber-400">{t('documentsPage.filesN', { n: esignRequests.filter(r => r.status === 'Pending Signature').length })}</p>
              <span className="text-[10px] text-amber-500">{t('documentsPage.requiresSignoff')}</span>
            </div>
          </div>

          {/* eSign ledger panel */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-white/5 pb-3.5">
              <h2 className="text-xs font-bold uppercase tracking-wider text-white">{t('documentsPage.ledgerHeading')}</h2>
              <button
                onClick={() => setIsRequestModalOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#E67E22] hover:bg-orange-600 text-white text-xs font-semibold transition-all shadow-md shadow-orange-500/10"
              >
                <Send className="w-3.5 h-3.5" />
                {t('documentsPage.requestSignature')}
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('documentsPage.colRequestRef')}</th>
                    <th>{t('documentsPage.colDocumentName')}</th>
                    <th>{t('documentsPage.colRecipient')}</th>
                    <th>{t('documentsPage.colRole')}</th>
                    <th>{t('documentsPage.colDateSent')}</th>
                    <th>{t('documentsPage.colCompletionDate')}</th>
                    <th>{t('documentsPage.colStatus')}</th>
                    <th className="text-end">{t('documentsPage.colActions')}</th>
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
                      <td className="text-xs text-slate-400">{ROLE_LABEL[req.role]}</td>
                      <td className="font-mono text-slate-400">{req.dateRequested}</td>
                      <td className="font-mono text-slate-400">{req.dateSigned || '—'}</td>
                      <td>
                        <span className={`badge text-[9px] ${
                          req.status === 'Fully Signed'
                            ? 'badge-green'
                            : 'badge-orange'
                        }`}>{req.status === 'Fully Signed' ? t('documentsPage.stFullySigned') : t('documentsPage.stPendingSignature')}</span>
                      </td>
                      <td className="text-end">
                        <div className="flex gap-2 justify-end">
                          {req.status === 'Pending Signature' ? (
                            <button
                              onClick={() => { setSelectedRequest(req); setIsSignModalOpen(true); }}
                              className="px-2 py-1 bg-[#E67E22]/10 border border-[#E67E22]/20 text-[#E67E22] hover:bg-[#E67E22]/20 rounded text-[10px] font-bold transition-all"
                            >
                              {t('documentsPage.signNow')}
                            </button>
                          ) : (
                            <button
                              onClick={() => { setSelectedRequest(req); setIsCertificateModalOpen(true); }}
                              className="px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 rounded text-[10px] font-bold transition-all flex items-center gap-1"
                            >
                              <ShieldCheck className="w-3 h-3" /> {t('documentsPage.auditLog')}
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
                className="absolute top-4 end-4 text-slate-500 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="space-y-1">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">{t('documentsPage.sendReqModalTitle')}</h2>
                <p className="text-[10px] text-slate-500">{t('documentsPage.sendReqModalSubtitle')}</p>
              </div>

              <form onSubmit={handleRequestSign} className="space-y-3 text-xs">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">{t('documentsPage.selectDocument')}</label>
                  <select
                    required
                    value={reqFileName}
                    onChange={(e) => setReqFileName(e.target.value)}
                    className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-orange-500/50"
                  >
                    <option value="" className="bg-[#0a0f1e]">{t('documentsPage.chooseFile')}</option>
                    {files.map(f => (
                      <option key={f.id} value={f.name} className="bg-[#0a0f1e]">{f.name} ({f.size})</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">{t('documentsPage.recipientFullName')}</label>
                  <input
                    type="text"
                    required
                    placeholder={t('documentsPage.recipientFullNamePh')}
                    value={reqSignerName}
                    onChange={(e) => setReqSignerName(e.target.value)}
                    className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-orange-500/50"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">{t('documentsPage.recipientEmail')}</label>
                  <input
                    type="email"
                    required
                    placeholder={t('documentsPage.recipientEmailPh')}
                    value={reqSignerEmail}
                    onChange={(e) => setReqSignerEmail(e.target.value)}
                    className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-orange-500/50"
                    dir="ltr"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">{t('documentsPage.signerRole')}</label>
                  <select
                    value={reqRole}
                    onChange={(e) => setReqRole(e.target.value as any)}
                    className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-orange-500/50"
                  >
                    <option value="Customer" className="bg-[#0a0f1e]">{t('documentsPage.roleCustomerFull')}</option>
                    <option value="Contractor" className="bg-[#0a0f1e]">{t('documentsPage.roleContractorFull')}</option>
                    <option value="Employee" className="bg-[#0a0f1e]">{t('documentsPage.roleEmployee')}</option>
                    <option value="Witness" className="bg-[#0a0f1e]">{t('documentsPage.roleWitnessFull')}</option>
                  </select>
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsRequestModalOpen(false)}
                    className="flex-1 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-semibold transition-colors border border-white/10"
                  >
                    {t('documentsPage.cancel')}
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-2 rounded-xl bg-[#E67E22] hover:bg-orange-600 text-white text-xs font-semibold transition-colors shadow-md shadow-orange-500/10"
                  >
                    {t('documentsPage.sendRequest')}
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
                className="absolute top-4 end-4 text-slate-500 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="space-y-1 border-b border-white/5 pb-2">
                <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-orange-500/10 text-[#E67E22] text-[9px] font-bold border border-orange-500/25">
                  <PenTool className="w-3 h-3" />
                  {t('documentsPage.secureProtocolBadge')}
                </div>
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">{t('documentsPage.signDocumentTitle', { name: selectedRequest.fileName })}</h2>
                <p className="text-[10px] text-slate-400">{t('documentsPage.signingAs', { name: selectedRequest.signerName, email: selectedRequest.signerEmail })}</p>
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
                  <p className="text-xs font-bold text-emerald-400">{t('documentsPage.signedLocked')}</p>
                  <p className="text-[9px] text-slate-500 font-mono">{t('documentsPage.syncingVerification')}</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Visual Document Mockup Sheet */}
                  <div className="p-4 rounded-xl bg-white/2 border border-white/5 text-[9px] text-slate-400 leading-relaxed font-serif relative min-h-[120px] select-none">
                    <p className="font-bold text-[10px] text-slate-200 mb-2">{t('documentsPage.agreementDeedTitle')}</p>
                    <p>{t('documentsPage.agreementDeedBody')}</p>

                    {/* Golden Signature Placeholder Target Box */}
                    <div className="mt-4 border border-dashed border-[#E67E22]/50 bg-[#E67E22]/5 p-2 rounded flex items-center justify-between">
                      <div>
                        <span className="text-[8px] text-slate-500 uppercase block font-sans">{t('documentsPage.authorizedSignatory')}</span>
                        <span className="text-[#E67E22] font-semibold font-sans">{selectedRequest.signerName} ({ROLE_LABEL[selectedRequest.role]})</span>
                      </div>
                      <div className="w-20 h-6 border-b border-orange-400 flex items-center justify-center font-cursive text-cyan-400 text-xs italic">
                        {signMethod === 'type' && typedName ? typedName : t('documentsPage.drawPadActive')}
                      </div>
                    </div>
                  </div>

                  {/* Method selector */}
                  <div className="flex gap-2 border-b border-white/5 pb-2 text-[10px] font-semibold">
                    <button
                      onClick={() => setSignMethod('draw')}
                      className={`px-3 py-1 rounded-lg ${signMethod === 'draw' ? 'bg-[#E67E22] text-white' : 'text-slate-400 hover:text-white'}`}
                    >
                      {t('documentsPage.drawSignature')}
                    </button>
                    <button
                      onClick={() => setSignMethod('type')}
                      className={`px-3 py-1 rounded-lg ${signMethod === 'type' ? 'bg-[#E67E22] text-white' : 'text-slate-400 hover:text-white'}`}
                    >
                      {t('documentsPage.typeSignature')}
                    </button>
                  </div>

                  {/* Signature pad elements */}
                  {signMethod === 'draw' ? (
                    <div className="space-y-1">
                      <div className="flex justify-between items-center text-[10px]">
                        <span className="text-slate-400">{t('documentsPage.drawWithMouse')}</span>
                        <button
                          onClick={clearCanvas}
                          className="text-[#EF4444] hover:text-red-400 text-[9px] font-bold"
                        >
                          {t('documentsPage.clearBoard')}
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
                      <label className="text-[10px] font-bold text-slate-500 uppercase">{t('documentsPage.typeSignatureName')}</label>
                      <input
                        type="text"
                        placeholder={t('documentsPage.typeSignatureNamePh')}
                        value={typedName}
                        onChange={(e) => setTypedName(e.target.value)}
                        className="w-full bg-white/5 border border-white/8 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-orange-500/50"
                      />
                      {typedName && (
                        <div className="p-3 rounded-xl bg-white/3 border border-white/5 text-center">
                          <span className="text-xs text-slate-400 block mb-1">{t('documentsPage.cursivePreview')}</span>
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
                      {t('documentsPage.cancel')}
                    </button>
                    <button
                      onClick={handleSubmitSignature}
                      className="flex-1 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold transition-colors shadow-md shadow-emerald-500/10"
                    >
                      {t('documentsPage.applySignature')}
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
                className="absolute top-4 end-4 text-slate-500 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="space-y-1 text-center border-b border-white/5 pb-3">
                <Award className="w-10 h-10 text-emerald-400 mx-auto animate-pulse" />
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">{t('documentsPage.certTitle')}</h2>
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest text-emerald-400">{t('documentsPage.certStatusVerified')}</p>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3.5 rounded-xl bg-white/3 border border-white/5 space-y-2.5">
                  <div className="flex justify-between">
                    <span className="text-slate-500">{t('documentsPage.documentRef')}</span>
                    <span className="font-bold text-slate-300">{selectedRequest.id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">{t('documentsPage.fileNameLabel')}</span>
                    <span className="font-bold text-slate-300 font-mono">{selectedRequest.fileName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">{t('documentsPage.signedBy')}</span>
                    <span className="font-bold text-slate-300">{selectedRequest.signerName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">{t('documentsPage.signerEmailLabel')}</span>
                    <span className="font-bold text-[#5DADE2] font-mono" dir="ltr">{selectedRequest.signerEmail}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">{t('documentsPage.signerRoleLabel')}</span>
                    <span className="font-bold text-slate-300">{ROLE_LABEL[selectedRequest.role]}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">{t('documentsPage.sentDate')}</span>
                    <span className="font-bold text-slate-300 font-mono">{selectedRequest.dateRequested}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">{t('documentsPage.signingDate')}</span>
                    <span className="font-bold text-emerald-400 font-mono">{selectedRequest.dateSigned}</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">{t('documentsPage.shaLabel')}</label>
                  <div className="p-2.5 rounded-lg bg-black/40 border border-white/5 text-[9px] font-mono text-emerald-400 break-all leading-normal" dir="ltr">
                    {selectedRequest.sha256}
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#10B981]/5 border border-[#10B981]/20 text-[10px] text-slate-400 leading-normal flex items-start gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <p>{t('documentsPage.integrityNote')}</p>
                </div>
              </div>

              <button
                onClick={() => setIsCertificateModalOpen(false)}
                className="w-full py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-semibold transition-colors border border-white/10"
              >
                {t('documentsPage.closeCertificate')}
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
