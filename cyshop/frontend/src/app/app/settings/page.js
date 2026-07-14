"use client";

import { useState, useEffect } from "react";
import { Settings, Globe, Palette, ShieldAlert } from "lucide-react";

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [currency, setCurrency] = useState("JOD");
  const [timezone, setTimezone] = useState("Asia/Amman");
  const [language, setLanguage] = useState("ar");
  const [themeMode, setThemeMode] = useState("DARK");

  const fetchSettings = async () => {
    setLoading(true);
    setError("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const response = await fetch("/api/v1/tenants/settings/", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId
        }
      });
      if (response.ok) {
        const data = await response.json();
        if (data.length > 0) {
          const s = data[0];
          setSettings(s);
          setCurrency(s.currency);
          setTimezone(s.timezone);
          setLanguage(s.language);
          setThemeMode(s.theme_mode);
        }
      } else {
        throw new Error("Failed to load settings");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    if (!settings) return;

    try {
      const response = await fetch(`/api/v1/tenants/settings/${settings.id}/`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId
        },
        body: JSON.stringify({
          ...settings,
          currency,
          timezone,
          language,
          theme_mode: themeMode
        })
      });

      if (response.ok) {
        setSuccess("System settings saved successfully.");
        fetchSettings();
      } else {
        throw new Error("Failed to update system settings");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="w-8 h-8 border-4 border-[var(--color-line)] border-t-orange-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl space-y-8 animate-fade text-[var(--color-ink)]">
      
      {error && (
        <div className="bg-red-950/40 border border-red-800 text-red-400 p-4 rounded-xl text-xs">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-emerald-950/40 border border-emerald-800 text-emerald-400 p-4 rounded-xl text-xs">
          {success}
        </div>
      )}

      <form onSubmit={handleSaveSettings} className="space-y-8">
        
        {/* Localization & Branding Settings */}
        <div className="bg-white backdrop-blur-xl border border-[var(--color-line)] rounded-2xl p-6 shadow-xl space-y-6">
          <h3 className="text-sm font-bold uppercase tracking-wider border-b border-[var(--color-line)] pb-3 flex items-center gap-2">
            <Globe className="w-4 h-4 text-[#ED6C00]" /> Localization & Regional Settings
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-[var(--color-ink-muted)] text-[10px] font-bold uppercase mb-2">Base Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full bg-white border border-[var(--color-line)] rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-orange-500 transition"
              >
                <option value="JOD">JOD - Jordanian Dinar</option>
                <option value="SAR">SAR - Saudi Riyal</option>
                <option value="AED">AED - UAE Dirham</option>
                <option value="USD">USD - US Dollar</option>
              </select>
            </div>

            <div>
              <label className="block text-[var(--color-ink-muted)] text-[10px] font-bold uppercase mb-2">System Timezone</label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full bg-white border border-[var(--color-line)] rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-orange-500 transition"
              >
                <option value="Asia/Amman">Asia/Amman</option>
                <option value="Asia/Riyadh">Asia/Riyadh</option>
                <option value="Asia/Dubai">Asia/Dubai</option>
                <option value="UTC">UTC - Coordinated Universal Time</option>
              </select>
            </div>

            <div>
              <label className="block text-[var(--color-ink-muted)] text-[10px] font-bold uppercase mb-2">System Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full bg-white border border-[var(--color-line)] rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-orange-500 transition"
              >
                <option value="ar">العربية (Arabic)</option>
                <option value="en">English (US)</option>
              </select>
            </div>

            <div>
              <label className="block text-[var(--color-ink-muted)] text-[10px] font-bold uppercase mb-2">Visual Theme</label>
              <select
                value={themeMode}
                onChange={(e) => setThemeMode(e.target.value)}
                className="w-full bg-white border border-[var(--color-line)] rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-orange-500 transition"
              >
                <option value="DARK">Dark Space (Recommended)</option>
                <option value="LIGHT">Light Theme</option>
                <option value="SYSTEM">System Settings</option>
              </select>
            </div>
          </div>
        </div>

        {/* Subscription details */}
        <div className="bg-white backdrop-blur-xl border border-[var(--color-line)] rounded-2xl p-6 shadow-xl space-y-4">
          <h3 className="text-sm font-bold uppercase tracking-wider border-b border-[var(--color-line)] pb-3 flex items-center gap-2">
            <Palette className="w-4 h-4 text-sky-400" /> SaaS Node Subscription
          </h3>

          <div className="flex justify-between items-center text-xs font-semibold bg-white p-4 rounded-xl border border-[var(--color-line)]">
            <div className="flex flex-col gap-1">
              <span className="text-[var(--color-ink-soft)]">Active Node Tier: <strong className="text-[#ED6C00]">{settings?.subscription_tier}</strong></span>
              <span className="text-[var(--color-ink-muted)]">Status: <strong className="text-green-500">{settings?.subscription_status}</strong></span>
            </div>
            <button
              type="button"
              className="bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-2)] px-4 py-2 rounded-lg font-bold transition text-[10px] border border-[var(--color-ink)]"
            >
              Upgrade Subscription
            </button>
          </div>
        </div>

        <button
          type="submit"
          className="w-full bg-[#ED6C00] hover:bg-[#ED6C00] active:scale-[0.99] text-white font-bold py-3 rounded-xl text-xs transition shadow-lg shadow-orange-500/10"
        >
          Save System Configurations
        </button>
      </form>
    </div>
  );
}
