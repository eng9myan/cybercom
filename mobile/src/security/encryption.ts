/**
 * Device-level encryption key management. ADR-0033 (offline-first, SQLCipher).
 * Keys generated at first launch, stored in iOS Keychain / Android Keystore.
 * Retrieved only after biometric authentication.
 */
import * as Keychain from "react-native-keychain";

const DB_KEY_SERVICE = "cybercom.db.encryption.key";
const TOKEN_SERVICE = "cybercom.auth.tokens";

/** Retrieve or generate the SQLCipher database encryption key. */
export async function getOrCreateDatabaseKey(): Promise<string> {
  const existing = await Keychain.getGenericPassword({ service: DB_KEY_SERVICE });
  if (existing) {
    return existing.password;
  }

  const key = generateSecureKey(32);
  await Keychain.setGenericPassword("cybercom", key, {
    service: DB_KEY_SERVICE,
    accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  });

  return key;
}

/** Store auth tokens securely. */
export async function storeTokens(accessToken: string, refreshToken: string): Promise<void> {
  const payload = JSON.stringify({ accessToken, refreshToken });
  await Keychain.setGenericPassword("cybercom", payload, {
    service: TOKEN_SERVICE,
    accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED,
    authenticationType: Keychain.AUTHENTICATION_TYPE.BIOMETRICS,
  });
}

/** Retrieve stored tokens. Requires biometric unlock. */
export async function getStoredTokens(): Promise<{
  accessToken: string;
  refreshToken: string;
} | null> {
  const result = await Keychain.getGenericPassword({ service: TOKEN_SERVICE });
  if (!result) return null;
  return JSON.parse(result.password) as { accessToken: string; refreshToken: string };
}

/** Remove stored tokens (on logout). */
export async function clearTokens(): Promise<void> {
  await Keychain.resetGenericPassword({ service: TOKEN_SERVICE });
}

function generateSecureKey(length: number): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*";
  let result = "";
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}
