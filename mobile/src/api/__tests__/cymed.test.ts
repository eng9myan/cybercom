import { cymedApi } from "../cymed";

describe("cymedApi", () => {
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

  it("listOrders sends X-Tenant-ID header", async () => {
    mockFetch({ count: 0, next: null, previous: null, results: [] });
    await cymedApi.listOrders("token", "tenant-123");
    const [, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(init.headers["X-Tenant-ID"]).toBe("tenant-123");
  });

  it("listOrders filters by order_type when supplied", async () => {
    mockFetch({ count: 0, next: null, previous: null, results: [] });
    await cymedApi.listOrders("token", "tenant-123", { order_type: "medication" });
    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("order_type=medication");
  });

  it("listOrders omits order_type when not supplied", async () => {
    mockFetch({ count: 0, next: null, previous: null, results: [] });
    await cymedApi.listOrders("token", "tenant-123");
    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).not.toContain("order_type");
  });
});
