"use client";

import { useState } from "react";
import { Save, Bell, Shield, Users, Building2, Check } from "lucide-react";

type Tab = "profile" | "organization" | "notifications" | "security" | "team";

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("profile");
  const [saved, setSaved] = useState(false);

  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: "profile", label: "Profile", icon: Users },
    { id: "organization", label: "Organization", icon: Building2 },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "security", label: "Security", icon: Shield },
    { id: "team", label: "Team", icon: Users },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-semibold text-white mb-1">Settings</h1>
        <p className="text-sm text-cy-gray-400">Manage your account and organization preferences</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* Tab nav */}
        <div className="space-y-0.5">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-left ${tab === id ? "bg-cy-orange/15 text-cy-orange border border-cy-orange/20" : "text-cy-gray-300 hover:bg-cy-glass-border/50 hover:text-white"}`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="lg:col-span-3 space-y-6">
          {tab === "profile" && (
            <div className="glass-card p-6 rounded-xl">
              <h2 className="font-heading font-semibold text-white mb-5">Profile Information</h2>
              <div className="space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <Field label="First Name" defaultValue="Mohammad" />
                  <Field label="Last Name" defaultValue="Al-Nsour" />
                </div>
                <Field label="Work Email" defaultValue="m.alnsour@cy-com.com" type="email" />
                <Field label="Phone" defaultValue="+962 79 XXX XXXX" />
                <Field label="Job Title" defaultValue="Chief Executive Officer" />
                <SelectField label="Language" options={["English", "Arabic"]} defaultValue="English" />
                <button onClick={handleSave} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium bg-cy-orange hover:bg-cy-orange-light text-white transition-all">
                  {saved ? <><Check className="w-4 h-4" /> Saved</> : <><Save className="w-4 h-4" /> Save Changes</>}
                </button>
              </div>
            </div>
          )}

          {tab === "organization" && (
            <div className="glass-card p-6 rounded-xl">
              <h2 className="font-heading font-semibold text-white mb-5">Organization Details</h2>
              <div className="space-y-4">
                <Field label="Organization Name" defaultValue="CyberCom" />
                <Field label="Industry" defaultValue="Healthcare Technology" />
                <SelectField label="Country" options={["Jordan", "Saudi Arabia", "UAE", "Kuwait", "Qatar"]} defaultValue="Jordan" />
                <Field label="Tax / VAT Number" defaultValue="TRN-JO-XXXXXXX" />
                <Field label="Billing Address" defaultValue="Amman, Jordan" />
                <button onClick={handleSave} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium bg-cy-orange hover:bg-cy-orange-light text-white transition-all">
                  {saved ? <><Check className="w-4 h-4" /> Saved</> : <><Save className="w-4 h-4" /> Save Changes</>}
                </button>
              </div>
            </div>
          )}

          {tab === "notifications" && (
            <div className="glass-card p-6 rounded-xl">
              <h2 className="font-heading font-semibold text-white mb-5">Notification Preferences</h2>
              <div className="space-y-4">
                {[
                  { label: "Invoice generated", desc: "Email when a new invoice is issued", enabled: true },
                  { label: "Payment confirmed", desc: "Email when payment is processed", enabled: true },
                  { label: "Renewal reminder", desc: "30-day and 7-day renewal notice", enabled: true },
                  { label: "Support ticket updates", desc: "Email on ticket reply or status change", enabled: true },
                  { label: "Product updates", desc: "Release notes for subscribed products", enabled: false },
                  { label: "Seat limit warnings", desc: "Alert when usage exceeds 85%", enabled: true },
                ].map((item) => (
                  <label key={item.label} className="flex items-start gap-4 cursor-pointer group">
                    <div className="relative mt-0.5">
                      <input type="checkbox" className="sr-only peer" defaultChecked={item.enabled} />
                      <div className="w-10 h-5 bg-cy-glass-border rounded-full peer-checked:bg-cy-orange transition-colors" />
                      <div className="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform peer-checked:translate-x-5" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white">{item.label}</div>
                      <div className="text-xs text-cy-gray-400">{item.desc}</div>
                    </div>
                  </label>
                ))}
                <button onClick={handleSave} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium bg-cy-orange hover:bg-cy-orange-light text-white transition-all mt-2">
                  {saved ? <><Check className="w-4 h-4" /> Saved</> : <><Save className="w-4 h-4" /> Save Preferences</>}
                </button>
              </div>
            </div>
          )}

          {tab === "security" && (
            <div className="space-y-4">
              <div className="glass-card p-6 rounded-xl">
                <h2 className="font-heading font-semibold text-white mb-5">Security Settings</h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between py-3 border-b border-cy-glass-border">
                    <div>
                      <div className="text-sm font-medium text-white">Two-Factor Authentication</div>
                      <div className="text-xs text-cy-gray-400">TOTP authenticator app</div>
                    </div>
                    <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">Enabled</span>
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-cy-glass-border">
                    <div>
                      <div className="text-sm font-medium text-white">SSO / SAML</div>
                      <div className="text-xs text-cy-gray-400">Single sign-on via identity provider</div>
                    </div>
                    <button className="text-xs text-cy-orange hover:text-cy-orange-light">Configure</button>
                  </div>
                  <div className="flex items-center justify-between py-3">
                    <div>
                      <div className="text-sm font-medium text-white">IP Allowlist</div>
                      <div className="text-xs text-cy-gray-400">Restrict portal access by IP range</div>
                    </div>
                    <button className="text-xs text-cy-orange hover:text-cy-orange-light">Set up</button>
                  </div>
                </div>
              </div>

              <div className="glass-card p-6 rounded-xl">
                <h2 className="font-heading font-semibold text-white mb-1">Change Password</h2>
                <p className="text-xs text-cy-gray-400 mb-4">Applies to your portal login only. Product access is managed separately.</p>
                <div className="space-y-3">
                  <Field label="Current Password" type="password" defaultValue="" placeholder="••••••••" />
                  <Field label="New Password" type="password" defaultValue="" placeholder="Min 12 characters" />
                  <Field label="Confirm New Password" type="password" defaultValue="" placeholder="••••••••" />
                  <button className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium bg-cy-orange hover:bg-cy-orange-light text-white transition-all">
                    Update Password
                  </button>
                </div>
              </div>
            </div>
          )}

          {tab === "team" && (
            <div className="glass-card p-6 rounded-xl">
              <div className="flex items-center justify-between mb-5">
                <h2 className="font-heading font-semibold text-white">Team Members</h2>
                <button className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-cy-orange hover:bg-cy-orange-light text-white transition-colors">
                  Invite Member
                </button>
              </div>
              <div className="space-y-3">
                {[
                  { name: "Mohammad Al-Nsour", email: "m.alnsour@cy-com.com", role: "Admin", status: "active" },
                  { name: "Dr. Sarah Khalil", email: "s.khalil@cy-com.com", role: "Clinical Admin", status: "active" },
                  { name: "IT Department", email: "it@cy-com.com", role: "Technical", status: "active" },
                ].map((member) => (
                  <div key={member.email} className="flex items-center gap-4 py-3 border-b border-cy-glass-border last:border-0">
                    <div className="w-8 h-8 rounded-full bg-cy-orange/20 flex items-center justify-center text-sm font-bold text-cy-orange">
                      {member.name[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-white">{member.name}</div>
                      <div className="text-xs text-cy-gray-400">{member.email}</div>
                    </div>
                    <span className="text-xs text-cy-gray-400">{member.role}</span>
                    <button className="text-xs text-cy-gray-500 hover:text-red-400 transition-colors">Remove</button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, defaultValue, type = "text", placeholder }: { label: string; defaultValue: string; type?: string; placeholder?: string }) {
  return (
    <div>
      <label className="block text-xs text-cy-gray-400 mb-1.5">{label}</label>
      <input
        type={type}
        defaultValue={defaultValue}
        placeholder={placeholder}
        className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-cy-gray-500 outline-none focus:border-cy-orange border border-cy-glass-border transition-colors"
      />
    </div>
  );
}

function SelectField({ label, options, defaultValue }: { label: string; options: string[]; defaultValue: string }) {
  return (
    <div>
      <label className="block text-xs text-cy-gray-400 mb-1.5">{label}</label>
      <select
        defaultValue={defaultValue}
        className="w-full glass-card rounded-lg px-3 py-2.5 text-sm text-white outline-none focus:border-cy-orange border border-cy-glass-border transition-colors bg-cy-dark"
      >
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}
