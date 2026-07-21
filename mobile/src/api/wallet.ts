/**
 * CyID ecosystem, Phase 9 — mobile client for platform.wallet
 * (see platform/wallet/views.py). Lives on the same backend as
 * cyIdentityBaseUrl (cymed's Django project mounts platform.wallet
 * directly) — no new base URL needed.
 *
 * Scoped to what the backend actually supports: balance + top-up +
 * debit. There is no "list recent transactions" endpoint yet — the
 * screen built on this client doesn't show a transaction history it
 * can't really fetch.
 */
import { API_CONFIG } from "./config";
import { apiRequest } from "./client";

export interface WalletLedgerEntry {
  id: string;
  entry_type: "topup" | "debit" | "refund" | "adjustment";
  amount: string;
  balance_after: string;
  reference: string;
  created_by: string;
  created_at: string;
}

export interface WalletBalance {
  person_id: string;
  currency: string;
  balance: string;
}

function wallet<T>(path: string, options: Parameters<typeof apiRequest>[2] = {}): Promise<T> {
  return apiRequest<T>(API_CONFIG.cyIdentityBaseUrl, path, options);
}

export const walletApi = {
  getBalance(accessToken: string, currency: string): Promise<WalletBalance> {
    return wallet("/wallet/balance/", { accessToken, query: { currency } });
  },

  topUp(accessToken: string, currency: string, amount: string, reference?: string): Promise<WalletLedgerEntry> {
    return wallet("/wallet/topup/", {
      method: "POST",
      accessToken,
      body: { currency, amount, reference },
    });
  },
};
