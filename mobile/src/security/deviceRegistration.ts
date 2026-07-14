/**
 * Device registration for CyIdentity mobile.
 * Registers this device with the CyIdentity control plane so it can be
 * used for MFA, passkey binding, and session tracking.
 * ADR-0017 §5.3 — device binding is required before WebAuthn enrollment.
 */
import { Platform } from "react-native";
import { createBiometricKeyPair } from "./biometric";

export interface DeviceInfo {
  deviceId: string;
  name: string;
  deviceType: "mobile";
  platform: "iOS" | "Android" | "unknown";
  osVersion: string;
  userAgent: string;
}

export interface DeviceRegistrationPayload {
  name: string;
  device_type: string;
  platform: string;
  os_version: string;
  user_agent: string;
  metadata: {
    biometric_key_created: boolean;
    app_version: string;
  };
}

const APP_VERSION = "2.1.0";

/**
 * Gather device metadata for registration.
 */
export function collectDeviceInfo(): DeviceInfo {
  const platform = Platform.OS === "ios" ? "iOS" : Platform.OS === "android" ? "Android" : "unknown";
  const osVersion = String(Platform.Version || "unknown");
  const userAgent = `CyberComMobile/${APP_VERSION} (${platform}; OS ${osVersion})`;

  return {
    deviceId: generateDeviceId(),
    name: `${platform} Device`,
    deviceType: "mobile",
    platform,
    osVersion,
    userAgent,
  };
}

/**
 * Build the payload for `POST /api/v1/identity/devices/`.
 */
export async function buildRegistrationPayload(): Promise<DeviceRegistrationPayload> {
  const info = collectDeviceInfo();
  const keypairResult = await createBiometricKeyPair();

  return {
    name: info.name,
    device_type: info.deviceType,
    platform: info.platform,
    os_version: info.osVersion,
    user_agent: info.userAgent,
    metadata: {
      biometric_key_created: keypairResult !== null,
      app_version: APP_VERSION,
    },
  };
}

/**
 * Submit device registration to the CyIdentity API.
 * Returns the registered device ID or null on failure.
 */
export async function registerDevice(
  apiBaseUrl: string,
  accessToken: string
): Promise<string | null> {
  try {
    const payload = await buildRegistrationPayload();
    const response = await fetch(`${apiBaseUrl}/api/v1/identity/devices/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      console.error("[CyIdentity] Device registration failed:", response.status);
      return null;
    }

    const data = await response.json();
    return data.device_id as string;
  } catch (err) {
    console.error("[CyIdentity] Device registration error:", err);
    return null;
  }
}

function generateDeviceId(): string {
  const chars = "abcdefghijklmnopqrstuvwxyz0123456789";
  let id = "";
  for (let i = 0; i < 32; i++) {
    id += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return `${id.slice(0, 8)}-${id.slice(8, 12)}-${id.slice(12, 16)}-${id.slice(16, 20)}-${id.slice(20)}`;
}
