/**
 * CyID ecosystem, Phase 9 — real wallet balance + top-up, wired to
 * platform.wallet (see src/api/wallet.ts). No transaction-history list:
 * the backend has no "list my ledger entries" endpoint yet, so this
 * screen doesn't show one it can't really fetch.
 */
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useAuth } from "../contexts/auth";
import { walletApi } from "../api/wallet";
import { ApiError } from "../api/client";

const CURRENCY = "USD"; // single-currency MVP; the backend already supports per-currency wallets

export default function WalletScreen() {
  const { session } = useAuth();
  const [balance, setBalance] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [amount, setAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadBalance = useCallback(async () => {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      const result = await walletApi.getBalance(session.accessToken, CURRENCY);
      setBalance(result.balance);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load wallet balance.");
    } finally {
      setLoading(false);
    }
  }, [session]);

  useEffect(() => {
    loadBalance();
  }, [loadBalance]);

  async function handleTopUp() {
    if (!session) return;
    const parsed = Number(amount);
    if (!amount || Number.isNaN(parsed) || parsed <= 0) {
      Alert.alert("Invalid amount", "Enter a positive amount to top up.");
      return;
    }
    setSubmitting(true);
    try {
      await walletApi.topUp(session.accessToken, CURRENCY, parsed.toFixed(2), "mobile_topup");
      setAmount("");
      await loadBalance();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Top-up failed. Please try again.";
      Alert.alert("Top-up failed", message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.label}>CyID Wallet Balance</Text>
        {loading ? (
          <ActivityIndicator size="large" color="#2563eb" style={styles.loader} />
        ) : error ? (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : (
          <Text style={styles.balance}>
            {balance} {CURRENCY}
          </Text>
        )}

        <View style={styles.topUpBlock}>
          <Text style={styles.label}>Top Up</Text>
          <TextInput
            style={styles.input}
            placeholder="0.00"
            placeholderTextColor="#6b7280"
            keyboardType="decimal-pad"
            value={amount}
            onChangeText={setAmount}
            editable={!submitting}
          />
          <TouchableOpacity
            style={[styles.btn, submitting && styles.btnDisabled]}
            onPress={handleTopUp}
            disabled={submitting}
            accessibilityLabel="Top up wallet"
          >
            {submitting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.btnText}>Add Funds</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f1117" },
  content: { padding: 20 },
  label: { color: "#9ca3af", fontSize: 13, fontWeight: "600", marginBottom: 8 },
  loader: { marginTop: 16 },
  balance: { color: "#fff", fontSize: 36, fontWeight: "800", marginBottom: 24 },
  topUpBlock: { marginTop: 16, gap: 12 },
  input: {
    backgroundColor: "#1e293b",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#334155",
    color: "#fff",
    padding: 14,
    fontSize: 16,
  },
  btn: {
    backgroundColor: "#2563eb",
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
  },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: "#fff", fontSize: 15, fontWeight: "700" },
  errorBox: { padding: 16, backgroundColor: "#7f1d1d", borderRadius: 8, marginBottom: 24 },
  errorText: { color: "#fca5a5", textAlign: "center" },
});
