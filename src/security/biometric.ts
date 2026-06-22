/**
 * Biometric authentication for CyIdentity mobile flows.
 * Uses react-native-biometrics for Face ID / Fingerprint / Device Credential.
 * ADR-0017 §5.3 — WebAuthn/passkey primary; biometric is the local device layer.
 */
import ReactNativeBiometrics, { BiometryTypes } from "react-native-biometrics";

const rnBiometrics = new ReactNativeBiometrics({ allowDeviceCredentials: true });

export interface BiometricResult {
  success: boolean;
  error?: string;
}

export interface BiometricAvailability {
  available: boolean;
  biometryType?: "TouchID" | "FaceID" | "Biometrics" | "DeviceCredentials";
}

/**
 * Check if biometrics are available on this device.
 */
export async function checkBiometricAvailability(): Promise<BiometricAvailability> {
  try {
    const { available, biometryType } = await rnBiometrics.isSensorAvailable();
    return { available, biometryType: biometryType as BiometricAvailability["biometryType"] };
  } catch {
    return { available: false };
  }
}

/**
 * Prompt biometric authentication. Returns success or reason for failure.
 */
export async function authenticateWithBiometrics(
  promptMessage: string = "Authenticate to access CyberCom"
): Promise<BiometricResult> {
  try {
    const { success, error } = await rnBiometrics.simplePrompt({ promptMessage });
    return { success, error };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/**
 * Create a biometric-bound key pair for device attestation (passkey pre-step).
 * The public key is submitted to the CyIdentity WebAuthn registration endpoint.
 */
export async function createBiometricKeyPair(): Promise<{ publicKey: string } | null> {
  try {
    const { keysExist } = await rnBiometrics.biometricKeysExist();
    if (!keysExist) {
      const { publicKey } = await rnBiometrics.createKeys();
      return { publicKey };
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Sign a server challenge using the biometric-bound private key.
 * Returns the signature for WebAuthn assertion verification.
 */
export async function signChallengeWithBiometrics(
  challenge: string,
  promptMessage: string = "Verify your identity"
): Promise<{ signature: string } | null> {
  try {
    const { success, signature } = await rnBiometrics.createSignature({
      promptMessage,
      payload: challenge,
    });
    return success && signature ? { signature } : null;
  } catch {
    return null;
  }
}

/**
 * Delete the biometric key pair (on logout / device de-registration).
 */
export async function deleteBiometricKeys(): Promise<boolean> {
  try {
    const { keysDeleted } = await rnBiometrics.deleteKeys();
    return keysDeleted;
  } catch {
    return false;
  }
}
