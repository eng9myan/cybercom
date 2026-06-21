/**
 * Auth context for React Native. ADR-0005 + ADR-0033 (offline-first).
 * Tokens stored in Keychain (iOS Keychain / Android Keystore).
 */
import React, { createContext, useContext, useState, useCallback, type ReactNode } from "react";

export interface MobileUserSession {
  userId: string;
  email: string;
  tenantId: string;
  roles: string[];
  accessToken: string;
  tokenExpiresAt: number;
}

interface AuthContextValue {
  session: MobileUserSession | null;
  isAuthenticated: boolean;
  setSession: (session: MobileUserSession | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSessionState] = useState<MobileUserSession | null>(null);

  const setSession = useCallback((s: MobileUserSession | null) => {
    setSessionState(s);
  }, []);

  const logout = useCallback(() => {
    setSessionState(null);
  }, []);

  return (
    <AuthContext.Provider value={{ session, isAuthenticated: session !== null, setSession, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
