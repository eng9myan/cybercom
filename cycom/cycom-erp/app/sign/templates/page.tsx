'use client';

import React, { useState, useEffect } from 'react';
import { Upload, FileText, Plus, Search, X, Check, Copy, ExternalLink, Shield, Send } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function SignTemplates() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Modals state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);

  // Upload Form states
  const [newTemplateName, setNewTemplateName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [reqSignature, setReqSignature] = useState(true);
  const [reqName, setReqName] = useState(true);
  const [reqDate, setReqDate] = useState(true);
  const [uploading, setUploading] = useState(false);

  // Request Form states
  const [recipientName, setRecipientName] = useState('');
  const [recipientEmail, setRecipientEmail] = useState('');
  const [sendingRequest, setSendingRequest] = useState(false);
  const [generatedRequest, setGeneratedRequest] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/sign/templates');
      const data = await res.json();
      setTemplates(data);
    } catch (err) {
      console.error("Failed to fetch templates", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      if (!newTemplateName) {
        // Auto fill name from file
        const baseName = e.target.files[0].name.replace(/\.[^/.]+$/, "");
        setNewTemplateName(baseName);
      }
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !newTemplateName) return;

    setUploading(true);

    // Build fields config JSON structure
    const fieldsConfig = [];
    if (reqSignature) {
      fieldsConfig.push({ type: 'signature', label: 'Signature Block', page: 1, x: 100, y: 600 });
    }
    if (reqName) {
      fieldsConfig.push({ type: 'text', label: 'Full Name', page: 1, x: 100, y: 660 });
    }
    if (reqDate) {
      fieldsConfig.push({ type: 'date', label: 'Date Signed', page: 1, x: 100, y: 720 });
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('name', newTemplateName);
    formData.append('fields_config', JSON.stringify(fieldsConfig));

    try {
      const res = await fetch('/api/sign/templates', {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        setShowUploadModal(false);
        // Reset form
        setSelectedFile(null);
        setNewTemplateName('');
        fetchTemplates();
      } else {
        console.error("Upload failed");
      }
    } catch (err) {
      console.error("Error uploading template:", err);
    } finally {
      setUploading(false);
    }
  };

  const handleRequestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTemplate || !recipientName || !recipientEmail) return;

    setSendingRequest(true);
    try {
      const res = await fetch('/api/sign/requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: selectedTemplate.id,
          signers: [{ name: recipientName, email: recipientEmail }]
        })
      });

      if (res.ok) {
        const data = await res.json();
        setGeneratedRequest(data);
      } else {
        console.error("Failed to generate request");
      }
    } catch (err) {
      console.error("Error creating signature request:", err);
    } finally {
      setSendingRequest(false);
    }
  };

  const handleCopyLink = () => {
    if (!generatedRequest) return;
    const url = `${window.location.origin}/sign/public/${generatedRequest.token}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredTemplates = templates.filter(t => 
    t.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">Document Templates</h2>
          <p className="text-xs text-slate-400">Upload PDFs and map signature fields for reusable contracts.</p>
        </div>
        <div className="flex gap-3">
          <div className="relative w-64">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search templates..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-rose-500/50 focus:ring-1 focus:ring-rose-500/50 transition-all"
            />
          </div>
          <button 
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-rose-500/20"
          >
            <Upload className="w-4 h-4" />
            Upload Template
          </button>
        </div>
      </div>

      <div className="glass-card p-6 min-h-[400px]">
        {loading ? (
          <div className="flex justify-center items-center h-[300px] text-slate-400">Loading templates...</div>
        ) : filteredTemplates.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 border border-white/10">
              <FileText className="w-8 h-8 text-slate-500" />
            </div>
            <h3 className="text-white font-bold mb-2">No templates found</h3>
            <p className="text-sm text-slate-400 max-w-sm mb-6">Upload an NDA, Employment Contract, or Sales Agreement PDF to get started.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {filteredTemplates.map((tpl: any) => (
              <div 
                key={tpl.id} 
                onClick={() => { setSelectedTemplate(tpl); setShowRequestModal(true); setGeneratedRequest(null); setRecipientName(''); setRecipientEmail(''); }}
                className="p-5 border border-white/5 hover:border-rose-500/30 rounded-2xl bg-white/3 hover:bg-rose-500/4 transition-all cursor-pointer group flex items-start gap-4"
              >
                <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 group-hover:bg-rose-500/20 transition-colors">
                  <FileText className="w-6 h-6" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-white font-bold text-sm group-hover:text-rose-400 transition-colors truncate">{tpl.name}</h4>
                  <p className="text-[10px] text-slate-500 font-mono mt-1">Uploaded: {new Date(tpl.created_at).toLocaleDateString()}</p>
                  <div className="flex gap-1.5 mt-3">
                    {tpl.fields_config?.map((f: any, idx: number) => (
                      <span key={idx} className="text-[8px] bg-white/5 border border-white/10 text-slate-400 px-1.5 py-0.5 rounded uppercase font-bold">
                        {f.type}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload Template Modal */}
      <AnimatePresence>
        {showUploadModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#0b0f19] border border-white/10 rounded-2xl p-6 w-full max-w-xl shadow-2xl relative space-y-4"
            >
              <div className="flex justify-between items-center border-b border-white/5 pb-3">
                <h3 className="text-base font-black text-white flex items-center gap-2">
                  <Upload className="w-5 h-5 text-rose-400" /> Upload PDF Template
                </h3>
                <button onClick={() => setShowUploadModal(false)} className="text-slate-500 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-4">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-500 uppercase">Template Name</label>
                      <input 
                        type="text" 
                        required
                        placeholder="e.g. Mutual NDA 2026"
                        value={newTemplateName}
                        onChange={e => setNewTemplateName(e.target.value)}
                        className="input-field py-2"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-500 uppercase">PDF File</label>
                      <div className="border border-dashed border-white/10 rounded-xl p-6 text-center hover:border-rose-500/50 transition-colors relative cursor-pointer bg-white/2">
                        <input 
                          type="file" 
                          required
                          accept="application/pdf"
                          onChange={handleFileChange}
                          className="absolute inset-0 opacity-0 cursor-pointer"
                        />
                        <FileText className="w-8 h-8 text-rose-400/60 mx-auto mb-2" />
                        <p className="text-white font-bold text-[11px] truncate">
                          {selectedFile ? selectedFile.name : "Select or drag contract PDF"}
                        </p>
                        <p className="text-[10px] text-slate-500 mt-1">PDF document only, up to 10MB</p>
                      </div>
                    </div>
                  </div>

                  {/* Simulated visual mapping fields */}
                  <div className="space-y-3 bg-white/3 border border-white/5 p-4 rounded-xl flex flex-col">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">Map Signature Fields</span>
                    <p className="text-[10px] text-slate-400 leading-relaxed">Check the fields you want to automatically place at the bottom of the document:</p>
                    
                    <div className="space-y-2 mt-2">
                      <label className="flex items-center gap-2 cursor-pointer p-2 rounded-lg bg-white/2 hover:bg-white/5 border border-white/5">
                        <input 
                          type="checkbox" 
                          checked={reqSignature}
                          onChange={e => setReqSignature(e.target.checked)}
                          className="rounded bg-white/5 border-white/10 text-rose-500"
                        />
                        <span className="text-white font-semibold">Place Signature Pad Block</span>
                      </label>

                      <label className="flex items-center gap-2 cursor-pointer p-2 rounded-lg bg-white/2 hover:bg-white/5 border border-white/5">
                        <input 
                          type="checkbox" 
                          checked={reqName}
                          onChange={e => setReqName(e.target.checked)}
                          className="rounded bg-white/5 border-white/10 text-rose-500"
                        />
                        <span className="text-white font-semibold">Place Signer Full Name Block</span>
                      </label>

                      <label className="flex items-center gap-2 cursor-pointer p-2 rounded-lg bg-white/2 hover:bg-white/5 border border-white/5">
                        <input 
                          type="checkbox" 
                          checked={reqDate}
                          onChange={e => setReqDate(e.target.checked)}
                          className="rounded bg-white/5 border-white/10 text-rose-500"
                        />
                        <span className="text-white font-semibold">Place Date Signed Block</span>
                      </label>
                    </div>

                    {/* Visual paper layout mockup */}
                    <div className="mt-4 flex-1 h-[140px] rounded border border-white/5 bg-white/2 flex flex-col justify-end p-4 relative overflow-hidden">
                      <div className="absolute top-2 left-2 right-2 border-b border-white/5 pb-1">
                        <div className="h-1 bg-white/10 rounded w-1/3 mb-1" />
                        <div className="h-1 bg-white/10 rounded w-full" />
                      </div>
                      <div className="space-y-2.5">
                        {reqSignature && (
                          <div className="border border-rose-500/20 bg-rose-500/5 p-1 rounded text-[8px] text-rose-400 font-bold text-center border-dashed">
                            × Signer Signature Place
                          </div>
                        )}
                        <div className="grid grid-cols-2 gap-2">
                          {reqName && (
                            <div className="border border-white/10 bg-white/5 p-1 rounded text-[7px] text-slate-400 font-semibold text-center truncate">
                              Full Name Block
                            </div>
                          )}
                          {reqDate && (
                            <div className="border border-white/10 bg-white/5 p-1 rounded text-[7px] text-slate-400 font-semibold text-center truncate">
                              Date Block
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <button 
                  type="submit" 
                  disabled={uploading}
                  className="w-full py-2.5 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white rounded-xl font-bold flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {uploading ? (
                    <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <Check className="w-4 h-4" /> Save Template
                    </>
                  )}
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Launch Request Modal */}
      <AnimatePresence>
        {showRequestModal && selectedTemplate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#0b0f19] border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl relative space-y-4"
            >
              <div className="flex justify-between items-center border-b border-white/5 pb-3">
                <h3 className="text-base font-black text-white flex items-center gap-2 truncate">
                  <Send className="w-5 h-5 text-rose-400" /> Send: {selectedTemplate.name}
                </h3>
                <button onClick={() => setShowRequestModal(false)} className="text-slate-500 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {!generatedRequest ? (
                <form onSubmit={handleRequestSubmit} className="space-y-4 text-xs">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Signer Name</label>
                    <input 
                      type="text" 
                      required
                      placeholder="e.g. Ahmad Masri"
                      value={recipientName}
                      onChange={e => setRecipientName(e.target.value)}
                      className="input-field py-2"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Signer Email Address</label>
                    <input 
                      type="email" 
                      required
                      placeholder="signer@example.com"
                      value={recipientEmail}
                      onChange={e => setRecipientEmail(e.target.value)}
                      className="input-field py-2"
                    />
                  </div>

                  <button 
                    type="submit" 
                    disabled={sendingRequest}
                    className="w-full py-2.5 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white rounded-xl font-bold flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {sendingRequest ? (
                      <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>
                        <Send className="w-4 h-4" /> Send Signature Request
                      </>
                    )}
                  </button>
                </form>
              ) : (
                <div className="space-y-4 text-center py-2 text-xs">
                  <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/20">
                    <Check className="w-6 h-6 animate-pulse" />
                  </div>
                  <div>
                    <h4 className="text-white font-bold">Signature Request Sent</h4>
                    <p className="text-[10px] text-slate-500 mt-1">Copy the secure link below to simulate the recipient experience:</p>
                  </div>

                  <div className="p-3 bg-white/3 border border-white/5 rounded-xl flex items-center justify-between gap-3 text-left font-mono text-[10px] text-slate-400">
                    <span className="truncate flex-1">
                      {window.location.origin}/sign/public/{generatedRequest.token}
                    </span>
                    <button 
                      onClick={handleCopyLink}
                      className="p-1.5 rounded bg-white/5 border border-white/10 hover:border-white/20 text-slate-300 hover:text-white"
                    >
                      {copied ? "Copied" : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2">
                    <button 
                      onClick={handleCopyLink}
                      className="py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 font-bold text-slate-300 hover:text-white transition-colors"
                    >
                      Copy Link
                    </button>
                    <a 
                      href={`/sign/public/${generatedRequest.token}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="py-2 rounded-xl bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white font-bold flex items-center justify-center gap-1.5 shadow-lg shadow-rose-500/20 transition-all"
                    >
                      <span>Open Signer Portal</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
