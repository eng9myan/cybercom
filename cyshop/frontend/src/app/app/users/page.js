"use client";

import { useState, useEffect } from "react";
import { Users, Trash2, Plus, Mail, Shield } from "lucide-react";

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // Invite form state
  const [newUsername, setNewUsername] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    setError("");
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const response = await fetch("/api/v1/identity/users/", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else {
        throw new Error("Failed to load user roster");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const response = await fetch("/api/v1/identity/register/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          username: newUsername,
          email: newEmail,
          password: newPassword,
          tenant_id: tenantId
        })
      });

      if (!response.ok) {
        throw new Error("Failed to invite user. Verify details.");
      }

      setNewUsername("");
      setNewEmail("");
      setNewPassword("");
      fetchUsers();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm("Are you sure you want to disable this user account?")) return;
    const token = localStorage.getItem("access_token");
    const tenantId = localStorage.getItem("tenant_id");

    try {
      const response = await fetch(`/api/v1/identity/users/${userId}/`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Tenant-ID": tenantId
        }
      });

      if (response.ok) {
        fetchUsers();
      } else {
        throw new Error("Failed to disable user account");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  return (
    <div className="space-y-8 animate-fade text-[var(--color-ink)]">
      
      {error && (
        <div className="bg-red-950/40 border border-red-800 text-red-400 p-4 rounded-xl text-xs">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* User list */}
        <div className="lg:col-span-2 bg-white backdrop-blur-xl border border-[var(--color-line)] rounded-2xl p-6 shadow-xl">
          <h3 className="text-sm font-bold uppercase tracking-wider mb-6 border-b border-[var(--color-line)] pb-3 flex items-center gap-2">
            <Users className="w-4 h-4 text-[#ED6C00]" /> Organizational Roster
          </h3>

          {loading ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-4 border-[var(--color-line)] border-t-orange-500 rounded-full animate-spin mx-auto"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-semibold">
                <thead>
                  <tr className="border-b border-[var(--color-line)] text-[var(--color-ink-muted)] uppercase tracking-wider text-[10px]">
                    <th className="py-3">User Details</th>
                    <th className="py-3">Email</th>
                    <th className="py-3">Status</th>
                    <th className="py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-850 text-[var(--color-ink-soft)]">
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="py-4 text-center text-[var(--color-ink-muted)]">No users found</td>
                    </tr>
                  ) : (
                    users.map((u) => (
                      <tr key={u.id} className="hover:bg-white">
                        <td className="py-4 font-bold text-[var(--color-ink)]">{u.username}</td>
                        <td className="py-4 font-mono text-[var(--color-ink-muted)]">{u.email}</td>
                        <td className="py-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${u.is_active ? "bg-green-950/40 text-green-400 border border-green-900/60" : "bg-red-950/40 text-red-400 border border-red-900/60"}`}>
                            {u.is_active ? "ACTIVE" : "DISABLED"}
                          </span>
                        </td>
                        <td className="py-4 text-right">
                          <button
                            onClick={() => handleDeleteUser(u.id)}
                            className="text-[var(--color-ink-muted)] hover:text-red-400 transition duration-150"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Invite User Card */}
        <div className="bg-white backdrop-blur-xl border border-[var(--color-line)] rounded-2xl p-6 shadow-xl h-fit">
          <h3 className="text-sm font-bold uppercase tracking-wider mb-6 border-b border-[var(--color-line)] pb-3 flex items-center gap-2">
            <Plus className="w-4 h-4 text-sky-400" /> Invite / Add User
          </h3>

          <form onSubmit={handleCreateUser} className="space-y-4">
            <div>
              <label className="block text-[var(--color-ink-muted)] text-[10px] font-bold uppercase mb-2 tracking-wide">Username</label>
              <input
                type="text"
                required
                placeholder="john_doe"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                className="w-full bg-white border border-[var(--color-line)] rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition"
              />
            </div>

            <div>
              <label className="block text-[var(--color-ink-muted)] text-[10px] font-bold uppercase mb-2 tracking-wide">Email Address</label>
              <input
                type="email"
                required
                placeholder="john@company.com"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                className="w-full bg-white border border-[var(--color-line)] rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition"
              />
            </div>

            <div>
              <label className="block text-[var(--color-ink-muted)] text-[10px] font-bold uppercase mb-2 tracking-wide">Initial Password</label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-white border border-[var(--color-line)] rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-[#ED6C00] hover:bg-[#ED6C00] active:scale-[0.99] text-white font-bold py-2.5 rounded-lg text-xs transition disabled:opacity-50"
            >
              {submitting ? "Inviting..." : "Add User Account"}
            </button>
          </form>
        </div>

      </div>

    </div>
  );
}
