/**
 * Offline-first sync pipeline. ADR-0033.
 * Outbox table → Background sync → Conflict resolution → Retry.
 */

export interface SyncTransaction {
  id: string;
  entityType: string;
  action: "create" | "update" | "delete";
  payload: Record<string, unknown>;
  version: number;
  lastUpdatedAt: number;
  createdAt: number;
  retryCount: number;
}

export interface SyncResult {
  synced: string[];
  failed: string[];
  conflicts: string[];
}

export async function processOutboxQueue(
  transactions: SyncTransaction[],
  apiBaseUrl: string,
  token: string
): Promise<SyncResult> {
  const result: SyncResult = { synced: [], failed: [], conflicts: [] };

  for (const tx of transactions) {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/sync/${tx.entityType}/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          id: tx.id,
          action: tx.action,
          payload: tx.payload,
          version: tx.version,
          last_updated_at: tx.lastUpdatedAt,
        }),
      });

      if (response.status === 409) {
        result.conflicts.push(tx.id);
      } else if (response.ok) {
        result.synced.push(tx.id);
      } else {
        result.failed.push(tx.id);
      }
    } catch {
      result.failed.push(tx.id);
    }
  }

  return result;
}

export function resolveConflict(
  local: SyncTransaction,
  remote: SyncTransaction
): SyncTransaction {
  // Last-Write-Wins for standard entities
  return local.lastUpdatedAt >= remote.lastUpdatedAt ? local : remote;
}
