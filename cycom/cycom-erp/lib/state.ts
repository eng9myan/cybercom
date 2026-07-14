import { create } from 'zustand';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

// Zustand Local UI State Store
interface UIStateStore {
  sidebarCollapsed: boolean;
  activeCompanyId: number | null;
  activeTenantId: number | null;
  toggleSidebar: () => void;
  setActiveCompanyId: (id: number | null) => void;
  setActiveTenantId: (id: number | null) => void;
}

export const useUIStore = create<UIStateStore>((set) => ({
  sidebarCollapsed: false,
  activeCompanyId: 1,
  activeTenantId: 1,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setActiveCompanyId: (id) => set({ activeCompanyId: id }),
  setActiveTenantId: (id) => set({ activeTenantId: id }),
}));

// WebSocket Bridge for Live Cache Invalidation
export function useLiveSync() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    let socket: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      try {
        socket = new WebSocket(wsUrl);

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'mutation' && data.model) {
              console.info(`[WS LiveSync] Invalidating server state cache for model: ${data.model}`);
              // Invalidate cache for this specific model type
              queryClient.invalidateQueries({ queryKey: [data.model] });
            }
          } catch (e) {
            console.error('[WS LiveSync] Failed to parse event payload:', e);
          }
        };

        socket.onclose = () => {
          console.warn('[WS LiveSync] Socket closed. Attempting reconnect in 5s...');
          reconnectTimeout = setTimeout(connect, 5000);
        };

        socket.onerror = (err) => {
          console.error('[WS LiveSync] Connection error:', err);
        };
      } catch (e) {
        console.error('[WS LiveSync] Failed to establish connection:', e);
      }
    };

    connect();

    return () => {
      if (socket) {
        // Remove onclose handler to prevent reconnect loops on unmount
        socket.onclose = null;
        socket.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, [queryClient]);
}
