import { cymartApi } from "../cymart";

describe("cymartApi", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.resetAllMocks();
  });

  function mockFetch(body: unknown, status = 200) {
    global.fetch = jest.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      text: async () => JSON.stringify(body),
    }) as unknown as typeof fetch;
  }

  it("listCategories defaults parent_id to 'root'", async () => {
    mockFetch({ data: [], pagination: { next_cursor: null, previous_cursor: null, has_more: false, count: 0, limit: 20 } });
    await cymartApi.listCategories("token123");
    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("parent_id=root");
  });

  it("getActiveCart hits the /carts/active/ endpoint", async () => {
    mockFetch({ id: "cart-1", customer_id: "cust-1", items: [] });
    await cymartApi.getActiveCart("token");
    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("/marketplace/carts/active/");
  });

  it("checkout sends an idempotency key derived from the cart id", async () => {
    mockFetch({ order_id: "ord-1", status: "draft" });
    await cymartApi.checkout("token", "cart-abc");
    const [, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(init.headers["Idempotency-Key"]).toBe("checkout-cart-abc");
  });

  it("addCartItem POSTs the item payload", async () => {
    mockFetch({ id: "cart-1", items: [] });
    await cymartApi.addCartItem("token", "cart-1", {
      store_id: "store-1",
      tenant_id: "tenant-1",
      product_id: "prod-1",
      quantity: 2,
      unit_price: 9.99,
    });
    const [url, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("/marketplace/carts/cart-1/add_item/");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toMatchObject({ product_id: "prod-1", quantity: 2 });
  });

  it("listOrders filters by customer_id", async () => {
    mockFetch({ data: [], pagination: { next_cursor: null, previous_cursor: null, has_more: false, count: 0, limit: 20 } });
    await cymartApi.listOrders("token", "cust-1");
    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("customer_id=cust-1");
  });
});
