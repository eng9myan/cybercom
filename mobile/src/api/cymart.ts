import { API_CONFIG } from "./config";
import { apiRequest, PaginatedResponse } from "./client";

export interface Category {
  id: string;
  parent: string | null;
  slug: string;
  name_en: string;
  name_ar: string;
  image_url: string;
  is_restricted: boolean;
  min_age: number | null;
  full_path: string;
}

export interface CartItem {
  id: string;
  product_id: string;
  product_name_snapshot: string;
  quantity: string;
  unit_price: string;
  item_discount: string;
}

export interface Cart {
  id: string;
  customer_id: string;
  store_id: string | null;
  tenant_id: string | null;
  status: "active" | "checked_out" | "abandoned";
  order_id: string | null;
  items: CartItem[];
}

export interface MarketplaceOrder {
  id: string;
  status: string;
  tenant_id: string;
  store_id: string;
  total_amount: string;
  created_at: string;
}

function cymart<T>(path: string, options: Parameters<typeof apiRequest>[2] = {}): Promise<T> {
  return apiRequest<T>(API_CONFIG.cyMartBaseUrl, path, options);
}

export const cymartApi = {
  listCategories(accessToken: string, parentId?: string): Promise<PaginatedResponse<Category>> {
    return cymart("/catalog/categories/", {
      accessToken,
      query: { parent_id: parentId ?? "root" },
    });
  },

  getCart(accessToken: string, cartId: string): Promise<Cart> {
    return cymart(`/marketplace/carts/${cartId}/`, { accessToken });
  },

  /** The caller's current cart, derived server-side from the verified JWT
   * — created on first call if none exists yet. */
  getActiveCart(accessToken: string): Promise<Cart> {
    return cymart("/marketplace/carts/active/", { accessToken });
  },

  addCartItem(
    accessToken: string,
    cartId: string,
    item: { store_id: string; tenant_id: string; product_id: string; quantity: number; unit_price: number; product_name?: string }
  ): Promise<Cart> {
    return cymart(`/marketplace/carts/${cartId}/add_item/`, {
      method: "POST",
      accessToken,
      body: item,
    });
  },

  checkout(
    accessToken: string,
    cartId: string,
    options: { fulfillment_type?: string; delivery_fee?: number; tip_amount?: number } = {}
  ): Promise<{ order_id: string; status: string }> {
    return cymart(`/marketplace/carts/${cartId}/checkout/`, {
      method: "POST",
      accessToken,
      idempotencyKey: `checkout-${cartId}`,
      body: options,
    });
  },

  listOrders(accessToken: string, customerId: string): Promise<PaginatedResponse<MarketplaceOrder>> {
    return cymart("/marketplace/orders/", { accessToken, query: { customer_id: customerId } });
  },
};
