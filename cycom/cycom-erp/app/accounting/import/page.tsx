'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, ArrowLeft, CheckCircle2, AlertTriangle, 
  Settings, Database, Play, Download, AlertCircle, FileSpreadsheet
} from 'lucide-react';
import { call } from '@/lib/cycom';

const SCHEMA_FIELDS = [
  { key: 'reference', label: 'Entry Reference (Required)', required: true },
  { key: 'journal_code', label: 'Journal Code (Required)', required: true },
  { key: 'date', label: 'Entry Date (Required)', required: true },
  { key: 'description', label: 'Entry Description', required: false },
  { key: 'account_code', label: 'Account Code (Required)', required: true },
  { key: 'label', label: 'Line Label', required: false },
  { key: 'debit', label: 'Debit Amount (Required)', required: true },
  { key: 'credit', label: 'Credit Amount (Required)', required: true },
];

export default function JournalImport() {
  const router = useRouter();
  const [csvText, setCsvText] = useState('');
  const [headers, setHeaders] = useState<string[]>([]);
  const [rows, setRows] = useState<string[][]>([]);
  const [mappings, setMappings] = useState<Record<string, string>>({});
  const [step, setStep] = useState(1); // 1: Upload, 2: Map, 3: Preview & Import, 4: Success
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [importing, setImporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [importedCount, setImportedCount] = useState(0);

  // Helper: Download a sample CSV template
  const downloadTemplate = () => {
    const csvContent = "reference,journal_code,date,description,account_code,label,debit,credit\n" +
      "MOVE/2026/06/101,GEN,2026-06-15,Opening Balance Cash,101000,Cash Office,5000.00,0.00\n" +
      "MOVE/2026/06/101,GEN,2026-06-15,Opening Balance Cash,301000,Retained Earnings,0.00,5000.00\n" +
      "MOVE/2026/06/102,GEN,2026-06-15,Opening Inventory,120000,Product Inventory,12500.00,0.00\n" +
      "MOVE/2026/06/102,GEN,2026-06-15,Opening Inventory,301000,Retained Earnings,0.00,12500.00\n";
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "journal_entry_import_template.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Parse CSV text
  const handleParse = (text: string) => {
    const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);
    if (lines.length < 2) {
      alert("Invalid CSV: Must contain at least a header row and one data row.");
      return;
    }
    const headerCols = lines[0].split(',').map(c => c.trim().replace(/^["']|["']$/g, ''));
    const dataRows = lines.slice(1).map(line => line.split(',').map(c => c.trim().replace(/^["']|["']$/g, '')));
    
    setHeaders(headerCols);
    setRows(dataRows);

    // Auto-map matching names
    const initialMap: Record<string, string> = {};
    headerCols.forEach((h, idx) => {
      const match = SCHEMA_FIELDS.find(f => f.key.toLowerCase() === h.toLowerCase() || f.label.toLowerCase() === h.toLowerCase());
      if (match) {
        initialMap[match.key] = idx.toString();
      }
    });
    setMappings(initialMap);
    setStep(2);
  };

  // Handle file drop/upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      setCsvText(text);
      handleParse(text);
    };
    reader.readAsText(file);
  };

  // Perform validation on mapped columns (including debit/credit balancing verification)
  const handleValidate = () => {
    const errors: string[] = [];
    const refIdx = mappings['reference'];
    const jnlIdx = mappings['journal_code'];
    const dateIdx = mappings['date'];
    const accIdx = mappings['account_code'];
    const debIdx = mappings['debit'];
    const credIdx = mappings['credit'];

    if (!refIdx) errors.push("Missing mapping for Entry Reference.");
    if (!jnlIdx) errors.push("Missing mapping for Journal Code.");
    if (!dateIdx) errors.push("Missing mapping for Entry Date.");
    if (!accIdx) errors.push("Missing mapping for Account Code.");
    if (!debIdx) errors.push("Missing mapping for Debit Amount.");
    if (!credIdx) errors.push("Missing mapping for Credit Amount.");

    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }

    const refCol = parseInt(refIdx);
    const jnlCol = parseInt(jnlIdx);
    const dateCol = parseInt(dateIdx);
    const accCol = parseInt(accIdx);
    const debCol = parseInt(debIdx);
    const credCol = parseInt(credIdx);

    // Track debit/credit totals by reference to ensure balancing
    const refBalances: Record<string, { debits: number; credits: number }> = {};
    
    rows.forEach((row, idx) => {
      const refVal = row[refCol];
      const jnlVal = row[jnlCol];
      const dateVal = row[dateCol];
      const accVal = row[accCol];
      const debVal = parseFloat(row[debCol] || '0');
      const credVal = parseFloat(row[credCol] || '0');

      if (!refVal) errors.push(`Row ${idx + 1}: Missing Entry Reference.`);
      if (!jnlVal) errors.push(`Row ${idx + 1}: Missing Journal Code.`);
      if (!dateVal) errors.push(`Row ${idx + 1}: Missing Entry Date.`);
      if (!accVal) errors.push(`Row ${idx + 1}: Missing Account Code.`);

      if (refVal) {
        if (!refBalances[refVal]) {
          refBalances[refVal] = { debits: 0, credits: 0 };
        }
        refBalances[refVal].debits += debVal;
        refBalances[refVal].credits += credVal;
      }
    });

    // Check balances for each unique entry reference
    Object.entries(refBalances).forEach(([ref, bal]) => {
      if (Math.abs(bal.debits - bal.credits) > 0.01) {
        errors.push(`Unbalanced Entry [${ref}]: Debits (JOD ${bal.debits.toFixed(2)}) do not match Credits (JOD ${bal.credits.toFixed(2)}). Difference is JOD ${Math.abs(bal.debits - bal.credits).toFixed(2)}.`);
      }
    });

    setValidationErrors(errors);
    setStep(3);
  };

  // Trigger Bulk Import via RPC
  const startImport = async () => {
    setImporting(true);
    setProgress(15);
    try {
      const payloadItems = rows.map(row => {
        const item: Record<string, string> = {};
        SCHEMA_FIELDS.forEach(f => {
          const mappedIdx = mappings[f.key];
          if (mappedIdx) {
            item[f.key] = row[parseInt(mappedIdx)] || '';
          }
        });
        return item;
      });

      setProgress(60);
      const res = await call<any>({
        model: 'account.move',
        method: 'bulk_import',
        args: [payloadItems]
      });
      
      setProgress(90);
      if (res?.success) {
        setImportedCount(res.imported_count);
        setStep(4);
      } else {
        alert("Import failed: No success confirmation returned.");
      }
    } catch (err: any) {
      alert("Error importing journal entries: " + err.message);
    } finally {
      setImporting(false);
      setProgress(100);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      {/* Header */}
      <div className="max-w-5xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push('/accounting')}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
              Bulk Import Journal Entries
            </h1>
            <p className="text-sm text-slate-400">Onboard opening balances by importing double-entry journal logs</p>
          </div>
        </div>
        
        <button 
          onClick={downloadTemplate}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition text-sm"
        >
          <Download className="w-4 h-4" />
          Download Template
        </button>
      </div>

      <div className="max-w-5xl mx-auto bg-slate-900/40 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl">
        {/* Step Indicator */}
        <div className="flex justify-between items-center mb-8 border-b border-slate-800/60 pb-6">
          {[
            { step: 1, label: 'Upload Sheet' },
            { step: 2, label: 'Map Fields' },
            { step: 3, label: 'Preview & Verify' },
            { step: 4, label: 'Complete' }
          ].map((s) => (
            <div key={s.step} className="flex items-center gap-2">
              <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                step === s.step 
                  ? 'bg-cyan-605 text-white shadow-lg shadow-cyan-500/20' 
                  : step > s.step 
                    ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30' 
                    : 'bg-slate-800 text-slate-500 border border-slate-700/50'
              }`}>
                {step > s.step ? '✓' : s.step}
              </span>
              <span className={`text-sm ${step === s.step ? 'text-slate-100 font-medium' : 'text-slate-500'}`}>{s.label}</span>
            </div>
          ))}
        </div>

        {/* Step 1: File Dropzone */}
        {step === 1 && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="text-center py-12">
            <div className="border-2 border-dashed border-slate-800 hover:border-cyan-500/50 transition-all rounded-2xl p-8 max-w-xl mx-auto cursor-pointer relative">
              <input 
                type="file" 
                accept=".csv" 
                onChange={handleFileUpload}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <Upload className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <h3 className="font-semibold text-lg mb-1">Upload CSV Document</h3>
              <p className="text-sm text-slate-400 mb-6">Drag and drop your export file here, or click to browse</p>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs font-medium text-slate-300">
                <FileSpreadsheet className="w-4 h-4 text-emerald-500" />
                Supports comma-separated values (.csv)
              </div>
            </div>
          </motion.div>
        )}

        {/* Step 2: Schema Mapping */}
        {step === 2 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Settings className="w-5 h-5 text-cyan-455" /> Map Sheet Headers to System Fields
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {SCHEMA_FIELDS.map((f) => (
                <div key={f.key} className="flex flex-col gap-1.5 p-3 bg-slate-950/40 border border-slate-850 rounded-xl">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    {f.label}
                  </label>
                  <select
                    value={mappings[f.key] || ''}
                    onChange={(e) => setMappings({ ...mappings, [f.key]: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-cyan-500/50"
                  >
                    <option value="">-- Ignore Field --</option>
                    {headers.map((h, idx) => (
                      <option key={idx} value={idx}>{h}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 border-t border-slate-800/60 pt-6">
              <button 
                onClick={() => setStep(1)}
                className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg text-sm transition"
              >
                Back
              </button>
              <button 
                onClick={handleValidate}
                className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-sm text-white font-medium shadow-lg shadow-cyan-600/15 transition"
              >
                Verify Data
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 3: Verification & Import Preview */}
        {step === 3 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Database className="w-5 h-5 text-cyan-400" /> Preview Verification Results
            </h2>

            {validationErrors.length > 0 ? (
              <div className="bg-red-950/20 border border-red-900/30 rounded-xl p-4 mb-6 flex gap-3 items-start">
                <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-red-400 text-sm mb-1">Validation Errors Found</h4>
                  <ul className="text-xs text-red-300/80 list-disc list-inside space-y-1">
                    {validationErrors.slice(0, 10).map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                    {validationErrors.length > 10 && (
                      <li>...and {validationErrors.length - 10} more discrepancies</li>
                    )}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="bg-emerald-950/20 border border-emerald-900/30 rounded-xl p-4 mb-6 flex gap-3 items-center">
                <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
                <p className="text-sm text-emerald-400 font-medium">All entry sheets parsed, balanced, and verified successfully!</p>
              </div>
            )}

            {/* Preview table */}
            <div className="overflow-x-auto border border-slate-850 rounded-xl mb-6">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                    {SCHEMA_FIELDS.map(f => (
                      <th key={f.key} className="px-4 py-3 font-medium">{f.key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {rows.slice(0, 5).map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-900/20 transition">
                      {SCHEMA_FIELDS.map(f => {
                        const mIdx = mappings[f.key];
                        return (
                          <td key={f.key} className="px-4 py-3 text-slate-300">
                            {mIdx ? row[parseInt(mIdx)] || '—' : '—'}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
              {rows.length > 5 && (
                <div className="p-3 text-center bg-slate-950/30 text-slate-500 text-xs">
                  + {rows.length - 5} more rows waiting to import
                </div>
              )}
            </div>

            {importing && (
              <div className="mb-6">
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Importing journal entry records...</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-cyan-600 rounded-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
                </div>
              </div>
            )}

            <div className="flex justify-end gap-3 border-t border-slate-800/60 pt-6">
              <button 
                onClick={() => setStep(2)}
                disabled={importing}
                className="px-4 py-2 border border-slate-800 hover:bg-slate-800 rounded-lg text-sm transition"
              >
                Back
              </button>
              <button 
                onClick={startImport}
                disabled={importing || validationErrors.length > 0}
                className="flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm text-white font-medium shadow-lg shadow-emerald-600/15 transition"
              >
                <Play className="w-4 h-4" />
                Commit to Database
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 4: Success Message */}
        {step === 4 && (
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-12">
            <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Import Successful</h2>
            <p className="text-sm text-slate-400 max-w-md mx-auto mb-8">
              Successfully parsed, balanced, and imported <span className="font-semibold text-slate-200">{importedCount}</span> journal entry sets to the ledger.
            </p>
            <button 
              onClick={() => router.push('/accounting')}
              className="px-6 py-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition rounded-xl text-sm font-semibold"
            >
              Return to Ledger
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}
