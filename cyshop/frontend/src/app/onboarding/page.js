"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Building2, MapPin, Percent, Warehouse, Rocket,
  ArrowRight, ArrowLeft, Check, Plus, Trash2, AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";

const STEPS = [
  { id: 1, label: "Company", icon: Building2 },
  { id: 2, label: "Currency & Tax", icon: Percent },
  { id: 3, label: "Branches", icon: MapPin },
  { id: 4, label: "Warehouses", icon: Warehouse },
  { id: 5, label: "Go Live", icon: Rocket },
];

const CURRENCIES = ["JOD", "SAR", "AED", "USD", "EUR", "GBP"];
const COUNTRIES = [
  { code: "JO", label: "Jordan" },
  { code: "SA", label: "Saudi Arabia" },
  { code: "AE", label: "UAE" },
  { code: "GB", label: "United Kingdom" },
  { code: "US", label: "United States" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [settingsId, setSettingsId] = useState(null);
  const [company, setCompany] = useState(null);
  const [branches, setBranches] = useState([]);
  const [warehouses, setWarehouses] = useState([]);

  const [companyForm, setCompanyForm] = useState({ name: "", legal_name: "", tax_number: "", country_code: "JO" });
  const [taxForm, setTaxForm] = useState({ currency: "JOD", tax_name: "Standard", tax_rate: "16" });
  const [newBranch, setNewBranch] = useState({ name: "", address: "" });

  useEffect(() => {
    const token = typeof window !== "undefined" && localStorage.getItem("access_token");
    if (!token) { router.push("/login"); return; }
    setReady(true);
  }, [router]);

  const load = useCallback(async () => {
    try {
      const [settingsRes, companiesRes, branchesRes, warehousesRes] = await Promise.all([
        api.get("/api/v1/tenants/settings/"),
        api.get("/api/v1/tenants/companies/"),
        api.get("/api/v1/tenants/branches/"),
        api.get("/api/v1/inventory/warehouses/"),
      ]);
      const settingsList = Array.isArray(settingsRes) ? settingsRes : settingsRes.results || [];
      const companiesList = Array.isArray(companiesRes) ? companiesRes : companiesRes.results || [];
      const branchesList = Array.isArray(branchesRes) ? branchesRes : branchesRes.results || [];
      const warehousesList = Array.isArray(warehousesRes) ? warehousesRes : warehousesRes.results || [];

      if (settingsList[0]) {
        setSettingsId(settingsList[0].id);
        setTaxForm((f) => ({ ...f, currency: settingsList[0].currency || "JOD" }));
        if (settingsList[0].onboarding_completed) { router.push("/app"); return; }
        if (settingsList[0].onboarding_step >= 1) setStep(Math.min(settingsList[0].onboarding_step + 1, 5));
      }
      if (companiesList[0]) {
        setCompany(companiesList[0]);
        setCompanyForm({
          name: companiesList[0].name || "",
          legal_name: companiesList[0].legal_name || "",
          tax_number: companiesList[0].tax_number || "",
          country_code: companiesList[0].country_code || "JO",
        });
      }
      setBranches(branchesList);
      setWarehouses(warehousesList);
    } catch (err) {
      setError(err.message);
    }
  }, [router]);

  useEffect(() => { if (ready) load(); }, [ready, load]);

  const advanceStep = async (nextStep) => {
    if (settingsId) {
      try { await api.patch(`/api/v1/tenants/settings/${settingsId}/`, { onboarding_step: nextStep - 1 }); }
      catch (_) { /* non-fatal: progress tracking only */ }
    }
    setStep(nextStep);
  };

  const saveCompany = async (e) => {
    e.preventDefault();
    if (!company) return;
    setSaving(true); setError("");
    try {
      await api.patch(`/api/v1/tenants/companies/${company.id}/`, companyForm);
      await advanceStep(2);
    } catch (err) { setError(err.message); } finally { setSaving(false); }
  };

  const saveTax = async (e) => {
    e.preventDefault();
    setSaving(true); setError("");
    try {
      if (settingsId) await api.patch(`/api/v1/tenants/settings/${settingsId}/`, { currency: taxForm.currency });
      if (company) {
        await api.post("/api/v1/catalog/tax-classes/", {
          company: company.id, name: taxForm.tax_name, code: "STD",
          rate: (parseFloat(taxForm.tax_rate || "0") / 100).toFixed(4),
        });
      }
      await advanceStep(3);
    } catch (err) { setError(err.message); } finally { setSaving(false); }
  };

  const addBranch = async () => {
    if (!newBranch.name || !company) return;
    setSaving(true); setError("");
    try {
      const created = await api.post("/api/v1/tenants/branches/", { ...newBranch, company: company.id });
      setBranches((b) => [...b, created]);
      setNewBranch({ name: "", address: "" });
    } catch (err) { setError(err.message); } finally { setSaving(false); }
  };

  const removeBranch = async (id) => {
    try { await api.del(`/api/v1/tenants/branches/${id}/`); setBranches((b) => b.filter((x) => x.id !== id)); }
    catch (err) { setError(err.message); }
  };

  const createWarehouse = async (branch) => {
    if (!company) return;
    setSaving(true); setError("");
    try {
      const code = `WH-${branch.name.slice(0, 3).toUpperCase()}`;
      const wh = await api.post("/api/v1/inventory/warehouses/", {
        company: company.id, branch: branch.id, name: `${branch.name} Warehouse`, code,
      });
      await api.post("/api/v1/inventory/locations/", {
        warehouse: wh.id, name: "Receiving", code: "RCV", location_type: "RECEIVING",
      });
      setWarehouses((w) => [...w, wh]);
    } catch (err) { setError(err.message); } finally { setSaving(false); }
  };

  const goLive = async () => {
    setSaving(true); setError("");
    try {
      if (settingsId) {
        await api.patch(`/api/v1/tenants/settings/${settingsId}/`, {
          onboarding_completed: true, onboarding_step: 5,
        });
      }
      router.push("/app");
    } catch (err) { setError(err.message); setSaving(false); }
  };

  if (!ready) return null;

  const branchesWithoutWarehouse = branches.filter((b) => !warehouses.some((w) => w.branch === b.id));

  return (
    <div className="min-h-dvh bg-[#0a0a0a] text-white flex flex-col">
      <header className="h-16 px-6 flex items-center border-b border-white/10">
        <span className="font-bold text-lg">CyShop Setup</span>
      </header>

      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-xl">
          <div className="flex items-center gap-2 mb-8">
            {STEPS.map((s, i) => (
              <div key={s.id} className="flex items-center gap-2 flex-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border transition shrink-0 ${
                  step > s.id ? "bg-[#ED6C00] border-[#ED6C00]" : step === s.id ? "border-[#ED6C00] text-[#ED6C00]" : "border-white/20 text-white/40"
                }`}>
                  {step > s.id ? <Check className="w-4 h-4" /> : <s.icon className="w-4 h-4" />}
                </div>
                {i < STEPS.length - 1 && <div className="flex-1 h-px bg-white/10" />}
              </div>
            ))}
          </div>

          <div className="bg-white/5 border border-white/10 rounded-2xl p-8">
            <h1 className="text-2xl font-bold mb-1">{STEPS[step - 1].label}</h1>
            <p className="text-sm text-white/50 mb-6">Step {step} of {STEPS.length}</p>

            {error && (
              <div className="mb-5 flex items-start gap-2 p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-sm">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" /><span>{error}</span>
              </div>
            )}

            {step === 1 && (
              <form onSubmit={saveCompany} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-white/60 block mb-1.5">Company Name *</label>
                  <input required className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-sm" value={companyForm.name} onChange={(e) => setCompanyForm((f) => ({ ...f, name: e.target.value }))} />
                </div>
                <div>
                  <label className="text-xs font-semibold text-white/60 block mb-1.5">Legal Name</label>
                  <input className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-sm" value={companyForm.legal_name} onChange={(e) => setCompanyForm((f) => ({ ...f, legal_name: e.target.value }))} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-white/60 block mb-1.5">Country</label>
                    <select className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-sm" value={companyForm.country_code} onChange={(e) => setCompanyForm((f) => ({ ...f, country_code: e.target.value }))}>
                      {COUNTRIES.map((c) => <option key={c.code} value={c.code}>{c.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-white/60 block mb-1.5">Tax Number</label>
                    <input className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-sm" value={companyForm.tax_number} onChange={(e) => setCompanyForm((f) => ({ ...f, tax_number: e.target.value }))} />
                  </div>
                </div>
                <button disabled={saving} className="w-full mt-2 bg-[#ED6C00] hover:opacity-90 disabled:opacity-50 rounded-lg py-3 text-sm font-bold flex items-center justify-center gap-2">
                  {saving ? "Saving…" : "Continue"} <ArrowRight className="w-4 h-4" />
                </button>
              </form>
            )}

            {step === 2 && (
              <form onSubmit={saveTax} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-white/60 block mb-1.5">Base Currency *</label>
                  <select required className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-sm" value={taxForm.currency} onChange={(e) => setTaxForm((f) => ({ ...f, currency: e.target.value }))}>
                    {CURRENCIES.map((c) => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-white/60 block mb-1.5">Tax Class Name</label>
                    <input className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-sm" value={taxForm.tax_name} onChange={(e) => setTaxForm((f) => ({ ...f, tax_name: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-white/60 block mb-1.5">Tax Rate (%)</label>
                    <input type="number" step="0.01" min="0" className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-sm" value={taxForm.tax_rate} onChange={(e) => setTaxForm((f) => ({ ...f, tax_rate: e.target.value }))} />
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setStep(1)} className="flex-1 border border-white/15 rounded-lg py-3 text-sm font-semibold flex items-center justify-center gap-2"><ArrowLeft className="w-4 h-4" /> Back</button>
                  <button disabled={saving} className="flex-1 bg-[#ED6C00] hover:opacity-90 disabled:opacity-50 rounded-lg py-3 text-sm font-bold flex items-center justify-center gap-2">
                    {saving ? "Saving…" : "Continue"} <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </form>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  {branches.map((b) => (
                    <div key={b.id} className="flex items-center justify-between bg-white/5 border border-white/10 rounded-lg px-3 py-2.5">
                      <div>
                        <div className="text-sm font-semibold">{b.name}</div>
                        <div className="text-xs text-white/40">{b.address}</div>
                      </div>
                      {branches.length > 1 && (
                        <button onClick={() => removeBranch(b.id)} className="text-white/40 hover:text-red-400"><Trash2 className="w-4 h-4" /></button>
                      )}
                    </div>
                  ))}
                </div>
                <div className="border border-dashed border-white/15 rounded-lg p-3 space-y-2">
                  <input placeholder="Branch name" className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2 text-sm" value={newBranch.name} onChange={(e) => setNewBranch((f) => ({ ...f, name: e.target.value }))} />
                  <input placeholder="Address" className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2 text-sm" value={newBranch.address} onChange={(e) => setNewBranch((f) => ({ ...f, address: e.target.value }))} />
                  <button onClick={addBranch} disabled={saving || !newBranch.name} className="w-full border border-white/15 rounded-lg py-2 text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-40">
                    <Plus className="w-4 h-4" /> Add Branch
                  </button>
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setStep(2)} className="flex-1 border border-white/15 rounded-lg py-3 text-sm font-semibold flex items-center justify-center gap-2"><ArrowLeft className="w-4 h-4" /> Back</button>
                  <button onClick={() => advanceStep(4)} className="flex-1 bg-[#ED6C00] hover:opacity-90 rounded-lg py-3 text-sm font-bold flex items-center justify-center gap-2">
                    Continue <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  {warehouses.map((w) => (
                    <div key={w.id} className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm">
                      <Check className="w-4 h-4 text-[#16A34A]" /> {w.name} <span className="text-white/40 font-mono text-xs">({w.code})</span>
                    </div>
                  ))}
                  {branchesWithoutWarehouse.map((b) => (
                    <div key={b.id} className="flex items-center justify-between bg-white/5 border border-white/10 rounded-lg px-3 py-2.5">
                      <span className="text-sm">{b.name} — no warehouse yet</span>
                      <button disabled={saving} onClick={() => createWarehouse(b)} className="text-xs font-semibold bg-[#ED6C00] rounded-md px-3 py-1.5 disabled:opacity-50">
                        Create Warehouse
                      </button>
                    </div>
                  ))}
                  {branches.length === 0 && <p className="text-sm text-white/40">Add a branch first.</p>}
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setStep(3)} className="flex-1 border border-white/15 rounded-lg py-3 text-sm font-semibold flex items-center justify-center gap-2"><ArrowLeft className="w-4 h-4" /> Back</button>
                  <button onClick={() => advanceStep(5)} className="flex-1 bg-[#ED6C00] hover:opacity-90 rounded-lg py-3 text-sm font-bold flex items-center justify-center gap-2">
                    Continue <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {step === 5 && (
              <div className="space-y-5">
                <div className="rounded-xl bg-white/5 border border-white/10 p-4 space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-white/50">Company</span><span className="font-semibold">{companyForm.name || "—"}</span></div>
                  <div className="flex justify-between"><span className="text-white/50">Currency</span><span className="font-semibold">{taxForm.currency}</span></div>
                  <div className="flex justify-between"><span className="text-white/50">Branches</span><span className="font-semibold">{branches.length}</span></div>
                  <div className="flex justify-between"><span className="text-white/50">Warehouses</span><span className="font-semibold">{warehouses.length}</span></div>
                </div>
                <div className="flex gap-3">
                  <button type="button" onClick={() => setStep(4)} className="flex-1 border border-white/15 rounded-lg py-3 text-sm font-semibold flex items-center justify-center gap-2"><ArrowLeft className="w-4 h-4" /> Back</button>
                  <button onClick={goLive} disabled={saving} className="flex-1 bg-[#ED6C00] hover:opacity-90 disabled:opacity-50 rounded-lg py-3 text-sm font-bold flex items-center justify-center gap-2">
                    {saving ? "Launching…" : "Go Live"} <Rocket className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
