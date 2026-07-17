"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Shield, Loader2, AlertCircle } from "lucide-react";
import { initiateLogin } from "@/lib/auth/cyidentity";

export default function AdminLoginPage() {
  const params = useParams();
  const locale = (params.locale as string) ?? "en";
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      await initiateLogin(locale, `/${locale}/admin`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start login");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-dvh flex items-center justify-center bg-cy-darker px-4">
      <div className="glass-card rounded-2xl p-8 max-w-sm w-full text-center">
        <div className="w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-4">
          <Shield className="w-6 h-6 text-red-400" />
        </div>
        <h1 className="text-xl font-heading font-semibold text-white mb-1">CyberCom Admin</h1>
        <p className="text-sm text-cy-gray-400 mb-6">Platform-admin access only.</p>

        {error && (
          <div className="mb-4 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 flex items-center gap-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            {error}
          </div>
        )}

        <button
          onClick={handleLogin}
          disabled={loading}
          className="btn-primary w-full py-3 text-sm inline-flex items-center justify-center gap-2 disabled:opacity-60"
        >
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          Sign in with CyIdentity
        </button>
      </div>
    </div>
  );
}
