/**
 * CyberCom Mobile — Offline Tenant Context Storage
 * Persists tenant context to AsyncStorage so the app works offline
 * after initial auth. Context syncs on next successful connection.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { TenantContext } from './tenantContext';

const STORAGE_KEY = '@cybercom:tenant_context';
const SYNC_KEY = '@cybercom:tenant_context_synced_at';

/**
 * Persist tenant context for offline access.
 */
export async function saveTenantContextOffline(context: TenantContext): Promise<void> {
  try {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(context));
    await AsyncStorage.setItem(SYNC_KEY, new Date().toISOString());
  } catch (err) {
    console.error('[OfflineTenant] Failed to persist context:', err);
  }
}

/**
 * Load cached tenant context. Returns null if never synced.
 */
export async function loadOfflineTenantContext(): Promise<TenantContext | null> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as TenantContext;
  } catch (err) {
    console.error('[OfflineTenant] Failed to load context:', err);
    return null;
  }
}

/**
 * Returns ISO timestamp of last successful sync, or null.
 */
export async function getLastSyncedAt(): Promise<string | null> {
  return AsyncStorage.getItem(SYNC_KEY);
}

/**
 * Check if the cached context is stale (> maxAgeMinutes old).
 */
export async function isCacheStale(maxAgeMinutes = 60): Promise<boolean> {
  const syncedAt = await getLastSyncedAt();
  if (!syncedAt) return true;
  const age = (Date.now() - new Date(syncedAt).getTime()) / 60000;
  return age > maxAgeMinutes;
}

/**
 * Clear all cached tenant context.
 */
export async function clearOfflineTenantContext(): Promise<void> {
  await AsyncStorage.multiRemove([STORAGE_KEY, SYNC_KEY]);
}

/**
 * Sync context: try to fetch fresh, fall back to offline cache.
 */
export async function syncTenantContext(
  apiBaseUrl: string,
  accessToken: string,
  tenantId: string,
): Promise<TenantContext | null> {
  const { fetchTenantContext } = await import('./tenantContext');

  const fresh = await fetchTenantContext(apiBaseUrl, accessToken, tenantId);
  if (fresh) {
    await saveTenantContextOffline(fresh);
    return fresh;
  }

  console.warn('[OfflineTenant] Network unavailable — using cached context');
  return loadOfflineTenantContext();
}
