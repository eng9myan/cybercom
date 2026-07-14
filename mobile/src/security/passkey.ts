/**
 * Passkey support placeholder — FIDO2 / WebAuthn passkey flows.
 * ADR-0017 §5.3 — WebAuthn/passkey is the PRIMARY authentication method.
 *
 * Full implementation requires a FIDO2 library (e.g. react-native-passkeys,
 * @simplewebauthn/browser, or native modules for iOS passkeys / Android FIDO2).
 * This module defines the interface and stubs so CyIdentity UI can reference
 * the functions while the native module is integrated in Program 2.2.
 *
 * Status: PLACEHOLDER — replace stubs with real FIDO2 library calls.
 */

export interface PasskeyRegistrationOptions {
  rpId: string;
  rpName: string;
  challenge: string;
  userId: string;
  userName: string;
  userDisplayName: string;
}

export interface PasskeyRegistrationResult {
  credentialId: string;
  publicKey: string;
  attestationObject: string;
  clientDataJSON: string;
}

export interface PasskeyAssertionOptions {
  rpId: string;
  challenge: string;
  allowCredentials: Array<{ id: string; type: "public-key" }>;
}

export interface PasskeyAssertionResult {
  credentialId: string;
  signature: string;
  authenticatorData: string;
  clientDataJSON: string;
  userHandle?: string;
}

/**
 * Register a new passkey for the current user.
 * Calls the CyIdentity WebAuthn registration endpoint to get options,
 * invokes the FIDO2 platform authenticator, and submits the response.
 *
 * PLACEHOLDER — returns null until native module is wired.
 */
export async function registerPasskey(
  _options: PasskeyRegistrationOptions
): Promise<PasskeyRegistrationResult | null> {
  console.warn("[CyIdentity] Passkey registration: native module not yet integrated (Program 2.2).");
  return null;
}

/**
 * Assert a passkey for authentication.
 * Invokes the stored passkey and returns the signed assertion.
 *
 * PLACEHOLDER — returns null until native module is wired.
 */
export async function assertPasskey(
  _options: PasskeyAssertionOptions
): Promise<PasskeyAssertionResult | null> {
  console.warn("[CyIdentity] Passkey assertion: native module not yet integrated (Program 2.2).");
  return null;
}

/**
 * Check if the platform supports passkeys.
 */
export async function isPasskeySupported(): Promise<boolean> {
  // iOS 16+, Android 9+ with FIDO2 support
  // Real check: query the native FIDO2 module availability
  return false; // placeholder
}
