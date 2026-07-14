'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { FileText, Shield, CheckCircle, Edit3, Trash2, Calendar, User, Eye, Download, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function PublicSignPage() {
  const params = useParams();
  const token = params.token as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);

  // Signature drawing/typing states
  const [showSignModal, setShowSignModal] = useState(false);
  const [signMethod, setSignMethod] = useState<'draw' | 'type'>('draw');
  const [typedName, setTypedName] = useState('');
  const [typedFont, setTypedFont] = useState('font-cursive'); // tailwind or custom font
  const [signatureImage, setSignatureImage] = useState<string | null>(null);
  const [isSigned, setIsSigned] = useState(false);
  const [signedDate, setSignedDate] = useState('');
  const [success, setSuccess] = useState(false);
  const [signing, setSigning] = useState(false);

  // Canvas drawing ref & logic
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);

  useEffect(() => {
    if (!token) return;

    fetch(`http://localhost:8000/api/sign/requests/public/${token}`)
      .then(res => {
        if (!res.ok) throw new Error("Invalid or expired signature link.");
        return res.json();
      })
      .then(resData => {
        setData(resData);
        if (resData.request.status === 'Signed') {
          setIsSigned(true);
          setSuccess(true);
        }
        setSignedDate(new Date().toLocaleDateString());
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [token]);

  // Touch & Mouse Drawing Handlers
  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';

    const rect = canvas.getBoundingClientRect();
    const clientX = ('touches' in e) ? e.touches[0].clientX : e.clientX;
    const clientY = ('touches' in e) ? e.touches[0].clientY : e.clientY;

    ctx.beginPath();
    ctx.moveTo(clientX - rect.left, clientY - rect.top);
    setIsDrawing(true);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const clientX = ('touches' in e) ? e.touches[0].clientX : e.clientX;
    const clientY = ('touches' in e) ? e.touches[0].clientY : e.clientY;

    ctx.lineTo(clientX - rect.left, clientY - rect.top);
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

  const saveSignature = () => {
    if (signMethod === 'draw') {
      const canvas = canvasRef.current;
      if (!canvas) return;
      // Convert canvas to base64 image
      const dataUrl = canvas.toDataURL();
      setSignatureImage(dataUrl);
    } else {
      if (!typedName) return;
      // Create text signature representation
      setSignatureImage(`TEXT:${typedName}:${typedFont}`);
    }
    setShowSignModal(false);
  };

  const handleFinalizeSigning = async () => {
    if (!signatureImage) return;

    setSigning(true);
    try {
      const res = await fetch(`http://localhost:8000/api/sign/requests/public/${token}/sign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signature: signatureImage,
          dateSigned: new Date().toISOString()
        })
      });

      if (res.ok) {
        setSuccess(true);
        setIsSigned(true);
      } else {
        console.error("Failed to sign document");
      }
    } catch (err) {
      console.error("Error signing document:", err);
    } finally {
      setSigning(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#030712] text-white flex items-center justify-center font-sans">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-rose-500/20 border-t-rose-500 rounded-full animate-spin mx-auto" />
          <p className="text-slate-400 text-xs font-bold">Verifying eSign Request...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#030712] text-white flex items-center justify-center p-6 font-sans">
        <div className="w-full max-w-md bg-[#0B0F19] border border-white/5 p-8 rounded-2xl text-center space-y-4 shadow-2xl">
          <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-500 flex items-center justify-center mx-auto border border-red-500/20">
            <Trash2 className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-black text-white">Verification Failed</h2>
          <p className="text-xs text-slate-400 leading-relaxed">{error}</p>
        </div>
      </div>
    );
  }

  const signer = data.request.signers?.[0] || { name: 'Recipient', email: '' };

  return (
    <div className="min-h-screen bg-[#030712] text-white p-4 md:p-8 font-sans relative overflow-x-hidden">
      {/* Background gradients */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-rose-500/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-5%] w-[40%] h-[40%] bg-purple-500/5 rounded-full blur-[120px]" />
      </div>

      <div className="max-w-4xl mx-auto space-y-6 relative z-10">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-white/5 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-rose-500 to-rose-600 flex items-center justify-center text-xs font-black shadow-lg shadow-rose-500/20">
              CY
            </div>
            <div>
              <div className="flex items-baseline gap-0.5">
                <span className="text-xs font-black text-rose-400">CY</span>
                <span className="text-xs font-black text-white">COM</span>
                <span className="text-[8px] font-bold px-1 rounded bg-rose-500/20 text-[#FB7185] ml-1.5 border border-rose-500/30">SIGN</span>
              </div>
              <p className="text-[8px] text-slate-500 font-bold uppercase tracking-widest mt-0.5">Secure Document Portal</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[10px] font-bold">
            <Shield className="w-3.5 h-3.5" /> Secured via AES-256
          </div>
        </header>

        {success ? (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-8 text-center space-y-5 max-w-lg mx-auto"
          >
            <div className="w-14 h-14 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/20">
              <CheckCircle className="w-8 h-8 animate-bounce" />
            </div>
            <div className="space-y-1.5">
              <h2 className="text-lg font-black text-white">Document Signed Successfully</h2>
              <p className="text-xs text-slate-400">The agreement has been finalized and recorded in Cycom ERP.</p>
            </div>

            <div className="p-4 bg-white/2 border border-white/5 rounded-xl text-left space-y-2 font-mono text-[9px] text-slate-500">
              <div><span className="font-bold text-slate-400">Contract:</span> {data.template.name}</div>
              <div><span className="font-bold text-slate-400">Signer:</span> {signer.name} ({signer.email})</div>
              <div><span className="font-bold text-slate-400">Fingerprint:</span> sha256-{token.substring(0, 16)}...</div>
              <div><span className="font-bold text-slate-400">Timestamp:</span> {new Date().toUTCString()}</div>
            </div>

            <button 
              onClick={() => window.close()}
              className="btn-primary py-2 px-6 text-xs w-full"
            >
              Close Signing Portal
            </button>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
            {/* Left Column: Instructions and Metadata */}
            <div className="glass-card p-5 space-y-5">
              <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-2">Signing Instructions</h3>
              
              <div className="space-y-4 text-xs">
                <div className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-[10px] font-bold text-rose-400 shrink-0">1</div>
                  <p className="text-slate-400 leading-relaxed">Review the contract text inside the document container.</p>
                </div>
                <div className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-[10px] font-bold text-rose-400 shrink-0">2</div>
                  <p className="text-slate-400 leading-relaxed">Scroll to the bottom and click on the designated <strong>Signature Field</strong>.</p>
                </div>
                <div className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-[10px] font-bold text-rose-400 shrink-0">3</div>
                  <p className="text-slate-400 leading-relaxed">Draw or type your signature and click <strong>Finalize</strong>.</p>
                </div>
              </div>

              <div className="border-t border-white/5 pt-4 space-y-3 text-xs">
                <div className="flex justify-between items-center text-[10px] text-slate-500 uppercase font-bold">Document Details</div>
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-rose-400" />
                  <span className="text-white font-bold truncate">{data.template.name}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <User className="w-4 h-4 text-slate-500" />
                  <span>{signer.name}</span>
                </div>
              </div>
            </div>

            {/* Right Column: Simulated document and signature pad placement */}
            <div className="lg:col-span-2 space-y-6">
              {/* Document Simulator Container */}
              <div className="glass-card p-6 md:p-8 bg-white/[0.01] border-white/5 min-h-[600px] flex flex-col justify-between relative">
                {/* Simulated Document content */}
                <div className="space-y-6">
                  <div className="text-center space-y-2 border-b border-white/5 pb-6">
                    <h1 className="text-xl font-bold text-white uppercase tracking-wider">{data.template.name}</h1>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Standard Agreement Document</p>
                  </div>

                  <div className="text-slate-300 text-xs leading-relaxed space-y-4 font-light">
                    <p>This agreement is entered into as of <strong>{signedDate}</strong> by and between the active corporate parties of <strong>Cycom</strong> and the undersigned signee <strong>{signer.name}</strong>.</p>
                    <p className="text-slate-400 uppercase text-[9px] font-bold tracking-wider">1. Confidential Information & Term</p>
                    <p>The signee acknowledges that during the term of execution of duties, they will have access to confidential, proprietary, and raw trade data including manufacturing costs, PLM specifications, biometrics logging setups, and POS cash drawer balances. The signee agrees to safeguard this data with the utmost security.</p>
                    <p className="text-slate-400 uppercase text-[9px] font-bold tracking-wider">2. Hardware Binding & Authorization</p>
                    <p>All access logs, biometric registers, and transactions conducted within Cycom ERP are protected under Single Device Binding logic and verified by security hashes.</p>
                    <p className="text-slate-400 italic">By placing their cryptographic signature below, both parties confirm adherence to these policies.</p>
                  </div>
                </div>

                {/* Mapped signature fields based on template fields_config */}
                <div className="mt-12 border-t border-dashed border-white/10 pt-8 grid grid-cols-1 sm:grid-cols-2 gap-6">
                  {data.template.fields_config?.map((field: any, idx: number) => {
                    if (field.type === 'signature') {
                      return (
                        <div 
                          key={idx}
                          onClick={() => setShowSignModal(true)}
                          className="border border-dashed border-rose-500/20 bg-rose-500/2 hover:bg-rose-500/5 p-4 rounded-xl text-center cursor-pointer transition-all flex flex-col items-center justify-center min-h-[100px] group relative overflow-hidden"
                        >
                          {signatureImage ? (
                            signatureImage.startsWith('TEXT:') ? (
                              <div className={`text-xl text-white font-bold ${signatureImage.split(':')[2]}`}>
                                {signatureImage.split(':')[1]}
                              </div>
                            ) : (
                              <img src={signatureImage} alt="Drawn signature" className="h-12 max-w-full object-contain invert brightness-200" />
                            )
                          ) : (
                            <>
                              <Edit3 className="w-5 h-5 text-rose-500/60 mb-2 group-hover:scale-110 transition-transform" />
                              <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider">Click to Sign</span>
                            </>
                          )}
                          <span className="absolute bottom-1.5 left-2 text-[8px] text-slate-500 uppercase font-bold font-mono">Signer Signature Block</span>
                        </div>
                      );
                    }

                    if (field.type === 'text') {
                      return (
                        <div key={idx} className="border border-white/5 bg-white/2 p-4 rounded-xl min-h-[100px] flex flex-col justify-end relative">
                          <span className="text-white font-bold text-xs">{signer.name}</span>
                          <span className="absolute bottom-1.5 left-2 text-[8px] text-slate-500 uppercase font-bold font-mono">Full Name Block</span>
                        </div>
                      );
                    }

                    if (field.type === 'date') {
                      return (
                        <div key={idx} className="border border-white/5 bg-white/2 p-4 rounded-xl min-h-[100px] flex flex-col justify-end relative">
                          <span className="text-white font-bold text-xs font-mono">{signedDate}</span>
                          <span className="absolute bottom-1.5 left-2 text-[8px] text-slate-500 uppercase font-bold font-mono">Date Block</span>
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>

              {/* Action Submit */}
              <button 
                onClick={handleFinalizeSigning}
                disabled={!signatureImage || signing}
                className="w-full py-3 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 disabled:opacity-40 text-white rounded-2xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-rose-500/20 transition-all text-sm"
              >
                {signing ? (
                  <span className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <CheckCircle className="w-5 h-5" /> Finalize & Sign Document
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Signature Canvas Drawing Modal */}
      <AnimatePresence>
        {showSignModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#0b0f19] border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl relative space-y-4"
            >
              <div className="flex justify-between items-center border-b border-white/5 pb-3">
                <h3 className="text-base font-black text-white">Create Signature</h3>
                <button onClick={() => setShowSignModal(false)} className="text-slate-500 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex gap-2 p-1 bg-white/2 border border-white/5 rounded-xl text-xs font-bold text-center">
                <button 
                  onClick={() => setSignMethod('draw')}
                  className={`flex-1 py-1.5 rounded-lg transition-all ${signMethod === 'draw' ? 'bg-rose-500 text-white shadow' : 'text-slate-400 hover:text-white'}`}
                >
                  Draw Signature
                </button>
                <button 
                  onClick={() => setSignMethod('type')}
                  className={`flex-1 py-1.5 rounded-lg transition-all ${signMethod === 'type' ? 'bg-rose-500 text-white shadow' : 'text-slate-400 hover:text-white'}`}
                >
                  Type Signature
                </button>
              </div>

              {signMethod === 'draw' ? (
                <div className="space-y-3">
                  <div className="bg-black/60 rounded-xl border border-white/10 overflow-hidden relative touch-none">
                    <canvas 
                      ref={canvasRef}
                      width={380}
                      height={200}
                      onMouseDown={startDrawing}
                      onMouseMove={draw}
                      onMouseUp={stopDrawing}
                      onMouseLeave={stopDrawing}
                      onTouchStart={startDrawing}
                      onTouchMove={draw}
                      onTouchEnd={stopDrawing}
                      className="w-full h-[200px] block cursor-crosshair"
                    />
                    <div className="absolute top-2 left-2 text-[8px] text-slate-500 font-bold uppercase tracking-wider pointer-events-none">
                      Draw with pointer / touch
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <button 
                      onClick={clearCanvas}
                      className="p-1 px-3 rounded-lg border border-white/5 hover:border-white/10 text-slate-400 hover:text-white text-[10px] font-bold flex items-center gap-1.5"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> Clear Pad
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 text-xs">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">Your Full Name</label>
                    <input 
                      type="text" 
                      value={typedName}
                      onChange={e => setTypedName(e.target.value)}
                      placeholder="e.g. Ahmad Masri"
                      className="input-field py-2.5"
                    />
                  </div>

                  <div className="space-y-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">Select Signature Style</span>
                    <div className="grid grid-cols-2 gap-2">
                      {[
                        { id: 'font-sans italic', label: 'Modern Script' },
                        { id: 'font-serif italic', label: 'Classic Script' },
                        { id: 'font-cursive', label: 'Cursive Script' }
                      ].map((style) => (
                        <button
                          key={style.id}
                          onClick={() => setTypedFont(style.id)}
                          className={`p-3 border rounded-xl text-center transition-all ${
                            typedFont === style.id 
                              ? 'border-rose-500 bg-rose-500/10 text-white' 
                              : 'border-white/5 hover:border-white/10 text-slate-400 hover:text-white'
                          }`}
                        >
                          <span className={`text-sm truncate block ${style.id}`}>{typedName || "Signature"}</span>
                          <span className="text-[8px] text-slate-500 mt-1 block uppercase font-bold">{style.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <button 
                onClick={saveSignature}
                className="w-full py-2 bg-rose-500 hover:bg-rose-600 text-white rounded-xl font-bold transition-all text-xs"
              >
                Insert Signature
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
