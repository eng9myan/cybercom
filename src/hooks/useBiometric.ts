/**
 * Biometric authentication hook. ADR-0033 (mobile security).
 * Wraps react-native-biometrics for FaceID / TouchID / Fingerprint.
 */
import { useState, useCallback } from "react";
import ReactNativeBiometrics, { BiometryTypes } from "react-native-biometrics";

const rnBiometrics = new ReactNativeBiometrics({ allowDeviceCredentials: true });

export interface BiometricState {
  isAvailable: boolean;
  biometryType: keyof typeof BiometryTypes | null;
  isLoading: boolean;
  error: string | null;
}

export function useBiometric() {
  const [state, setState] = useState<BiometricState>({
    isAvailable: false,
    biometryType: null,
    isLoading: false,
    error: null,
  });

  const checkAvailability = useCallback(async () => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const { available, biometryType } = await rnBiometrics.isSensorAvailable();
      setState({
        isAvailable: available,
        biometryType: biometryType as keyof typeof BiometryTypes | null,
        isLoading: false,
        error: null,
      });
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : "Biometric check failed",
      }));
    }
  }, []);

  const authenticate = useCallback(async (promptMessage: string): Promise<boolean> => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const { success } = await rnBiometrics.simplePrompt({ promptMessage });
      setState((s) => ({ ...s, isLoading: false }));
      return success;
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : "Biometric authentication failed",
      }));
      return false;
    }
  }, []);

  return { ...state, checkAvailability, authenticate };
}
