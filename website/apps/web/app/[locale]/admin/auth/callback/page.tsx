"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Loader2, AlertCircle } from "lucide-react";
import { handleCallback, isPlatformAdmin, logout } from "@/lib/auth/cyidentity";

export default function AdminAuthCallbackPage() {
  const params = useParams();
  const router = useRouter();
  const locale = (params.locale as string) ?? "en";
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    handleCallback(locale)
      .then(({ returnUrl }) => {
        if (!isPlatformAdmin()) {
          setError("This account does not have platform_admin or tenant_admin access.");
          return;
        }
        router.replace(returnUrl);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Login failed");
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-dvh flex items-center justify-center bg-cy-darker px-4">
      <div className="glass-card rounded-2xl p-8 max-w-sm w-full text-center">
        {error ? (
          <>
            <div className="w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-6 h-6 text-red-400" />
            </div>
            <p className="text-sm text-red-400 mb-4">{error}</p>
            <button
              onClick={() => logout(locale)}
              className="btn-secondary px-4 py-2 text-xs"
            >
              Back to login
            </button>
          </>
        ) : (
          <>
            <Loader2 className="w-6 h-6 text-cy-orange animate-spin mx-auto mb-4" />
            <p className="text-sm text-cy-gray-400">Completing sign-in…</p>
          </>
        )}
      </div>
    </div>
  );
}
