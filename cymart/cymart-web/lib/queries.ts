"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import type {
  AgentReply,
  Cart,
  DietPlan,
  DietProfile,
  DietProfileInput,
  DietRegime,
  OrderTracking,
  ReplenishItem,
  TodayStatus,
} from "./types";

// ── Diet Shield ──────────────────────────────────────────────────────────

export function useDietProfile() {
  return useQuery<DietProfile | null>({
    queryKey: ["diet-profile"],
    queryFn: async () => {
      try {
        return await api.get<DietProfile>("/dietshield/profile/");
      } catch (err: unknown) {
        if (err && typeof err === "object" && "status" in err && (err as { status: number }).status === 404) {
          return null;
        }
        throw err;
      }
    },
  });
}

export function useDietPlan(enabled: boolean) {
  return useQuery<DietPlan | null>({
    queryKey: ["diet-plan"],
    enabled,
    queryFn: async () => {
      try {
        return await api.get<DietPlan>("/dietshield/plan/");
      } catch (err: unknown) {
        if (err && typeof err === "object" && "status" in err && (err as { status: number }).status === 404) {
          return null;
        }
        throw err;
      }
    },
  });
}

export function useTodayStatus(enabled: boolean) {
  return useQuery<TodayStatus | null>({
    queryKey: ["diet-today"],
    enabled,
    refetchInterval: 30_000,
    queryFn: async () => {
      try {
        return await api.get<TodayStatus>("/dietshield/today/");
      } catch (err: unknown) {
        if (err && typeof err === "object" && "status" in err && (err as { status: number }).status === 404) {
          return null;
        }
        throw err;
      }
    },
  });
}

export function useRegimes() {
  return useQuery<DietRegime[]>({
    queryKey: ["diet-regimes"],
    queryFn: () => api.get<DietRegime[]>("/dietshield/regimes/"),
  });
}

export function useCreateDietProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: DietProfileInput) =>
      api.post<{ profile: DietProfile; plan: DietPlan }>("/dietshield/profile/", input),
    onSuccess: (data) => {
      qc.setQueryData(["diet-profile"], data.profile);
      qc.setQueryData(["diet-plan"], data.plan);
      qc.invalidateQueries({ queryKey: ["diet-today"] });
    },
  });
}

// ── Cart ─────────────────────────────────────────────────────────────────

export function useActiveCart() {
  return useQuery<Cart>({
    queryKey: ["cart"],
    queryFn: () => api.get<Cart>("/marketplace/carts/active/"),
    refetchInterval: 15_000,
  });
}

export function useCheckout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (cartId: string) =>
      api.post<{ order_id: string; status: string }>(`/marketplace/carts/${cartId}/checkout/`, {
        fulfillment_type: "delivery",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cart"] });
    },
  });
}

// ── Agent ────────────────────────────────────────────────────────────────

export function useSendAgentMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (text: string) => api.post<AgentReply>("/agent/message/", { text }),
    onSuccess: () => {
      // A tool call may have changed the cart or diet log — refresh both.
      qc.invalidateQueries({ queryKey: ["cart"] });
      qc.invalidateQueries({ queryKey: ["diet-today"] });
    },
  });
}

// ── Pantry ───────────────────────────────────────────────────────────────

export function useReplenishBasket(enabled: boolean) {
  return useQuery<ReplenishItem[]>({
    queryKey: ["replenish"],
    enabled,
    queryFn: () => api.get<ReplenishItem[]>("/pantry/replenish/"),
  });
}

// ── Delivery ─────────────────────────────────────────────────────────────

export function useOrderTracking(orderId: string | null) {
  return useQuery<OrderTracking | null>({
    queryKey: ["tracking", orderId],
    enabled: !!orderId,
    refetchInterval: 10_000,
    queryFn: async () => {
      try {
        return await api.get<OrderTracking>(`/delivery/track/${orderId}/`);
      } catch (err: unknown) {
        if (err && typeof err === "object" && "status" in err && (err as { status: number }).status === 404) {
          return null;
        }
        throw err;
      }
    },
  });
}
