"use client";

import { useEffect, useRef, useState } from "react";
import { cyed, cyedUrl } from "@/lib/cyed";
import { PageHeader, Loading, ErrorNote, Field } from "@/components/ui";
import { Panel } from "@/components/kit";
import { useToast } from "@/components/Toast";
import type { SchoolProfile } from "@/lib/types";
import { Building2, ImageUp } from "lucide-react";

export default function SettingsPage() {
  const [profile, setProfile] = useState<SchoolProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [logoV, setLogoV] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  useEffect(() => {
    (async () => {
      try {
        setProfile(await cyed.get<SchoolProfile>("school/profile/"));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load school profile");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const set = (k: keyof SchoolProfile, v: string) => setProfile((p) => (p ? { ...p, [k]: v } : p));

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    setSaving(true);
    try {
      const updated = await cyed.patch<SchoolProfile>("school/profile/", {
        name: profile.name, short_name: profile.short_name, address: profile.address,
        suburb: profile.suburb, state: profile.state, postcode: profile.postcode,
        principal_name: profile.principal_name, contact_email: profile.contact_email,
        contact_phone: profile.contact_phone,
      });
      setProfile(updated);
      toast.push("School settings saved");
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Save failed", "bad");
    } finally {
      setSaving(false);
    }
  };

  const uploadLogo = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("logo", file);
    try {
      await cyed.upload("school/logo/", form);
      setProfile((p) => (p ? { ...p, has_logo: true } : p));
      setLogoV((v) => v + 1);
      toast.push("Logo updated — now on report cards");
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Logo upload failed", "bad");
    }
  };

  if (loading) return <Loading label="Loading school settings…" />;
  if (!profile) return <ErrorNote error={error || "No profile"} />;

  return (
    <div style={{ maxWidth: 860 }}>
      <PageHeader title="School Settings" subtitle="Your school name and logo appear on report cards" />
      {error && <ErrorNote error={error} />}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 20, alignItems: "start" }}>
        <Panel title={<div className="flex items-center gap-2"><Building2 size={15} style={{ color: "var(--cyan)" }} /><span className="label">School profile</span></div>}>
          <form onSubmit={save} className="space-y-3">
            <Field label="School name">
              <input className="input" value={profile.name} onChange={(e) => set("name", e.target.value)} required />
            </Field>
            <div style={{ display: "flex", gap: 10 }}>
              <div style={{ flex: 1 }}><Field label="Suburb"><input className="input" value={profile.suburb || ""} onChange={(e) => set("suburb", e.target.value)} /></Field></div>
              <div style={{ width: 90 }}><Field label="State"><input className="input" value={profile.state || ""} onChange={(e) => set("state", e.target.value)} /></Field></div>
              <div style={{ width: 90 }}><Field label="Postcode"><input className="input" value={profile.postcode || ""} onChange={(e) => set("postcode", e.target.value)} /></Field></div>
            </div>
            <Field label="Address"><input className="input" value={profile.address || ""} onChange={(e) => set("address", e.target.value)} /></Field>
            <Field label="Principal"><input className="input" value={profile.principal_name || ""} onChange={(e) => set("principal_name", e.target.value)} /></Field>
            <div style={{ display: "flex", gap: 10 }}>
              <div style={{ flex: 1 }}><Field label="Contact email"><input className="input" value={profile.contact_email || ""} onChange={(e) => set("contact_email", e.target.value)} /></Field></div>
              <div style={{ flex: 1 }}><Field label="Contact phone"><input className="input" value={profile.contact_phone || ""} onChange={(e) => set("contact_phone", e.target.value)} /></Field></div>
            </div>
            <button className="btn btn-primary" type="submit" disabled={saving}>{saving ? "Saving…" : "Save settings"}</button>
          </form>
        </Panel>

        <Panel title={<div className="flex items-center gap-2"><ImageUp size={15} style={{ color: "var(--violet)" }} /><span className="label">School logo</span></div>}>
          <div style={{ height: 120, display: "flex", alignItems: "center", justifyContent: "center", background: "#fff", borderRadius: 10, border: "1px solid var(--border)", marginBottom: 12 }}>
            {profile.has_logo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={`${cyedUrl("school/logo/")}?v=${logoV}`} alt="School logo" style={{ maxHeight: 100, maxWidth: 220 }} />
            ) : (
              <span style={{ color: "#94a3b8", fontSize: 12 }}>No logo</span>
            )}
          </div>
          <input ref={fileRef} type="file" accept="image/jpeg,image/png" className="text-xs" style={{ marginBottom: 10 }} />
          <button className="btn btn-ghost" style={{ width: "100%", justifyContent: "center" }} onClick={uploadLogo}>Upload logo</button>
          <div className="text-xs mt-2" style={{ color: "var(--muted)" }}>
            JPEG recommended — it embeds directly into the report-card PDF.
          </div>
        </Panel>
      </div>
    </div>
  );
}
