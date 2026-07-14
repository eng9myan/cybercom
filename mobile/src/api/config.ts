/**
 * Backend base URLs.
 *
 * Metro doesn't inline `process.env.*` for arbitrary custom variables out
 * of the box (only NODE_ENV) — using process.env here without wiring up
 * react-native-config or babel-plugin-transform-inline-environment-variables
 * would silently always fall through to the hardcoded default on device,
 * which is worse than just being honest that it's hardcoded for now.
 *
 * Only "local" is a real value. staging/production URLs don't exist yet —
 * they get filled in when those environments are actually provisioned,
 * not guessed at here.
 */
export const API_CONFIG = {
  // 10.0.2.2 is the Android emulator's host-loopback address; iOS
  // Simulator can use localhost directly. Pick per platform when wiring
  // up a real device/emulator matrix.
  cyIdentityBaseUrl: "http://localhost:8000/api/v1",
  cyMartBaseUrl: "http://localhost:8001/api/v1",
};
