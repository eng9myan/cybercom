"use client";

import { useState, useEffect } from "react";
import { Shield, ShieldAlert, Key, Plus } from "lucide-react";

export default function RolesPage() {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [newRoleCode, setNewRoleCode] = useState("");
  const [newRoleName, setNewRoleName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const headers = {
        "Authorization": `Bearer ${token}`,
        "X-Tenant-ID": tenantId
      };

      const roleRes = await fetch("/api/v1/identity/roles/", { headers });
      const roleData = roleRes.ok ? await roleRes.json() : [];

      const permRes = await fetch("/api/v1/identity/permissions/", { headers });
      const permData = permRes.ok ? await permRes.json() : [];

      setRoles(roleData);
      setPermissions(permData);
    } catch (err) {
      setError("Failed to load security definitions");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRole = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const response = await fetch("/api/v1/identity/roles/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId
        },
        body: JSON.stringify({
          code: newRoleCode.toUpperCase(),
          name: newRoleName
        })
      });

      if (!response.ok) {
        throw new Error("Failed to create role");
      }

      setNewRoleCode("");
      setNewRoleName("");
      fetchData();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="w-8 h-8 border-4 border-[var(--color-line)] border-t-orange-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade text-[var(--color-ink)]">
      
      {error && (
        <div className="bg-red-950/40 border border-red-800 text-red-400 p-4 rounded-xl text-xs">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Roles Table */}
        <div className="lg:col-span-2 bg-white backdrop-blur-xl border border-[var(--color-line)] rounded-2xl p-6 shadow-xl">
          <h3 className="text-sm font-bold uppercase tracking-wider mb-6 border-b border-[var(--color-line)] pb-3 flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#ED6C00]" /> Security Roles
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-semibold">
              <thead>
                <tr className="border-b border-[var(--color-line)] text-[var(--color-ink-muted)] uppercase tracking-wider text-[10px]">
                  <th className="py-3">Role Code</th>
                  <th className="py-3">Display Name</th>
                  <th className="py-3">Assigned Permissions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-850 text-[var(--color-ink-soft)]">
                {roles.length === 0 ? (
                  <tr>
                    <td colSpan="3" className="py-4 text-center text-[var(--color-ink-muted)]">No security roles declared</td>
                  </tr>
                ) : (
                  roles.map((r) => (
                    <tr key={r.id}>
                      <td className="py-4 font-mono font-bold text-[#ED6C00]">{r.code}</td>
                      <td className="py-4 font-bold text-[var(--color-ink)]">{r.name}</td>
                      <td className="py-4 text-[var(--color-ink-muted)]">
                        {r.permissions?.length || 0} scopes mapped
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Create Role & System Permissions */}
        <div className="space-y-8">
          
          {/* Create Role Card */}
          <div className="bg-white backdrop-blur-xl border border-[var(--color-line)] rounded-2xl p-6 shadow-xl">
            <h3 className="text-sm font-bold uppercase tracking-wider mb-6 border-b border-[var(--color-line)] pb-3 flex items-center gap-2">
              <Plus className="w-4 h-4 text-sky-400" /> Create Security Role
            </h3>

            <form onSubmit={handleCreateRole} className="space-y-4">
              <div>
                <label className="block text-[var(--color-ink-muted)] text-[10px] font-bold uppercase mb-2">Role Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CASHIER"
                  value={newRoleCode}
                  onChange={(e) => setNewRoleCode(e.target.value)}
                  className="w-full bg-white border border-[var(--color-line)] rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition"
                />
              </div>
              <div>
                <label className="block text-[var(--color-ink-muted)] text-[10px] font-bold uppercase mb-2">Role Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. POS Sales Agent"
                  value={newRoleName}
                  onChange={(e) => setNewRoleName(e.target.value)}
                  className="w-full bg-white border border-[var(--color-line)] rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-[#ED6C00] hover:bg-[#ED6C00] active:scale-[0.99] text-white font-bold py-2.5 rounded-lg text-xs transition disabled:opacity-50"
              >
                {submitting ? "Deploying..." : "Add Security Role"}
              </button>
            </form>
          </div>

          {/* Permissions Registry list */}
          <div className="bg-white backdrop-blur-xl border border-[var(--color-line)] rounded-2xl p-6 shadow-xl">
            <h3 className="text-sm font-bold uppercase tracking-wider mb-6 border-b border-[var(--color-line)] pb-3 flex items-center gap-2">
              <Key className="w-4 h-4 text-purple-400" /> Active Permission Registry
            </h3>

            <div className="space-y-3 max-h-60 overflow-y-auto pr-2">
              {permissions.length === 0 ? (
                <div className="text-[var(--color-ink-muted)] text-xs text-center py-4">No permission scopes registered</div>
              ) : (
                permissions.map((p) => (
                  <div key={p.id} className="flex justify-between items-center text-xs font-semibold bg-white border border-[var(--color-line)] p-2.5 rounded-lg">
                    <span className="font-mono text-[var(--color-ink-soft)]">{p.code}</span>
                    <span className="text-[10px] text-[var(--color-ink-muted)]">{p.name}</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
