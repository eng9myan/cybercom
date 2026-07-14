/**
 * CyIdentity mobile login screen.
 * Supports: OIDC redirect, biometric unlock, passkey (placeholder).
 * ADR-0017 §5.3 — WebAuthn/passkey primary; biometric is device-layer gate.
 */
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import {
  authenticateWithBiometrics,
  checkBiometricAvailability,
} from "../security/biometric";
import { getStoredTokens } from "../security/encryption";
import { isPasskeySupported } from "../security/passkey";

type AuthState = "idle" | "checking" | "biometric" | "passkey" | "oidc" | "success" | "error";

export default function LoginScreen() {
  const [authState, setAuthState] = useState<AuthState>("idle");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [passkeyAvailable, setPasskeyAvailable] = useState(false);
  const [biometryLabel, setBiometryLabel] = useState("Biometrics");

  useEffect(() => {
    initAuthOptions();
  }, []);

  async function initAuthOptions() {
    setAuthState("checking");
    const [availability, passkey] = await Promise.all([
      checkBiometricAvailability(),
      isPasskeySupported(),
    ]);
    setBiometricAvailable(availability.available);
    setPasskeyAvailable(passkey);
    if (availability.biometryType === "FaceID") setBiometryLabel("Face ID");
    else if (availability.biometryType === "TouchID") setBiometryLabel("Touch ID");
    else if (availability.available) setBiometryLabel("Biometrics");
    setAuthState("idle");
  }

  async function handleBiometricLogin() {
    setAuthState("biometric");
    setErrorMessage("");
    try {
      // Try to retrieve stored tokens (silent re-auth)
      const tokens = await getStoredTokens();
      if (!tokens) {
        setErrorMessage("No stored session. Please sign in with OIDC first.");
        setAuthState("error");
        return;
      }
      const result = await authenticateWithBiometrics("Verify your identity to access CyberCom");
      if (result.success) {
        setAuthState("success");
        // In production: validate token freshness, refresh if needed
      } else {
        setErrorMessage(result.error || "Biometric authentication failed.");
        setAuthState("error");
      }
    } catch (err) {
      setErrorMessage(String(err));
      setAuthState("error");
    }
  }

  async function handlePasskeyLogin() {
    setAuthState("passkey");
    Alert.alert(
      "Passkey Login",
      "Passkey authentication (FIDO2/WebAuthn) will be enabled in Program 2.2. Please use OIDC or biometric login.",
      [{ text: "OK", onPress: () => setAuthState("idle") }]
    );
  }

  function handleOIDCLogin() {
    setAuthState("oidc");
    // In production: open the Keycloak OIDC authorization URL via in-app browser.
    // Requires react-native-app-auth or Expo AuthSession.
    Alert.alert(
      "OIDC Sign In",
      "Opening Keycloak authorization endpoint...\n(OIDC browser flow configured in app-auth settings)",
      [{ text: "OK", onPress: () => setAuthState("idle") }]
    );
  }

  const isLoading = authState === "checking" || authState === "biometric" || authState === "oidc";

  return (
    <View style={styles.container}>
      {/* Logo + Title */}
      <View style={styles.header}>
        <View style={styles.logoRing}>
          <Text style={styles.logoText}>CY</Text>
        </View>
        <Text style={styles.title}>CyberCom</Text>
        <Text style={styles.subtitle}>تسجيل الدخول الآمن · Secure Identity</Text>
      </View>

      {/* Auth options */}
      <View style={styles.authBlock}>
        {isLoading ? (
          <ActivityIndicator size="large" color="#2563eb" style={styles.loader} />
        ) : (
          <>
            {/* Biometric button — shown when available */}
            {biometricAvailable && (
              <TouchableOpacity
                style={[styles.btn, styles.biometricBtn]}
                onPress={handleBiometricLogin}
                accessibilityLabel={`Sign in with ${biometryLabel}`}
              >
                <Text style={styles.biometricIcon}>
                  {biometryLabel === "Face ID" ? "👤" : "👆"}
                </Text>
                <Text style={styles.btnText}>Sign in with {biometryLabel}</Text>
              </TouchableOpacity>
            )}

            {/* Passkey button — placeholder */}
            <TouchableOpacity
              style={[styles.btn, styles.passkeyBtn]}
              onPress={handlePasskeyLogin}
              accessibilityLabel="Sign in with Passkey"
            >
              <Text style={styles.btnText}>🔑  Sign in with Passkey</Text>
            </TouchableOpacity>

            {/* OIDC fallback */}
            <TouchableOpacity
              style={[styles.btn, styles.oidcBtn]}
              onPress={handleOIDCLogin}
              accessibilityLabel="Sign in with organization account"
            >
              <Text style={styles.btnText}>تسجيل الدخول / Sign In with Account</Text>
            </TouchableOpacity>
          </>
        )}

        {/* Error display */}
        {authState === "error" && errorMessage ? (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{errorMessage}</Text>
          </View>
        ) : null}

        {/* Success state */}
        {authState === "success" ? (
          <View style={styles.successBox}>
            <Text style={styles.successText}>✓ Authenticated — loading your workspace…</Text>
          </View>
        ) : null}
      </View>

      <Text style={styles.footer}>
        Secured by CyIdentity · Keycloak 24 · OAuth 2.1 + WebAuthn
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f1117",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 64,
    paddingHorizontal: 24,
  },
  header: { alignItems: "center", gap: 12 },
  logoRing: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "#2563eb",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 8,
  },
  logoText: { color: "#fff", fontSize: 28, fontWeight: "800" },
  title: { fontSize: 32, fontWeight: "bold", color: "#ffffff" },
  subtitle: { fontSize: 14, color: "#9ca3af", textAlign: "center" },
  authBlock: { width: "100%", gap: 12 },
  btn: {
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 10,
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "center",
    gap: 8,
  },
  biometricBtn: { backgroundColor: "#1d4ed8" },
  passkeyBtn: { backgroundColor: "#374151", borderWidth: 1, borderColor: "#4b5563" },
  oidcBtn: { backgroundColor: "#1e293b", borderWidth: 1, borderColor: "#334155" },
  biometricIcon: { fontSize: 20 },
  btnText: { color: "#ffffff", fontSize: 16, fontWeight: "600" },
  loader: { marginVertical: 32 },
  errorBox: {
    backgroundColor: "#7f1d1d",
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  errorText: { color: "#fca5a5", fontSize: 14, textAlign: "center" },
  successBox: {
    backgroundColor: "#14532d",
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  successText: { color: "#86efac", fontSize: 14, textAlign: "center" },
  footer: { color: "#4b5563", fontSize: 11, textAlign: "center" },
});
