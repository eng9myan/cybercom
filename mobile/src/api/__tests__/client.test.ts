import { apiRequest, ApiError } from "../client";

describe("apiRequest", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.resetAllMocks();
  });

  function mockFetchOnce(status: number, body: unknown) {
    global.fetch = jest.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      text: async () => JSON.stringify(body),
    }) as unknown as typeof fetch;
  }

  it("builds the URL correctly regardless of trailing/leading slashes", async () => {
    mockFetchOnce(200, { ok: true });
    await apiRequest("http://localhost:8001/api/v1/", "/catalog/categories/");
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8001/api/v1/catalog/categories/",
      expect.anything()
    );
  });

  it("attaches Authorization header when accessToken is provided", async () => {
    mockFetchOnce(200, {});
    await apiRequest("http://x", "/y", { accessToken: "abc123" });
    const [, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(init.headers.Authorization).toBe("Bearer abc123");
  });

  it("omits Authorization header when no accessToken is given", async () => {
    mockFetchOnce(200, {});
    await apiRequest("http://x", "/y");
    const [, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(init.headers.Authorization).toBeUndefined();
  });

  it("attaches Idempotency-Key header when provided", async () => {
    mockFetchOnce(201, {});
    await apiRequest("http://x", "/y", { idempotencyKey: "cart-checkout-123" });
    const [, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(init.headers["Idempotency-Key"]).toBe("cart-checkout-123");
  });

  it("serializes query params, skipping undefined values", async () => {
    mockFetchOnce(200, {});
    await apiRequest("http://x", "/y", { query: { a: "1", b: undefined, c: 2 } });
    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toBe("http://x/y?a=1&c=2");
  });

  it("returns parsed JSON on success", async () => {
    mockFetchOnce(200, { hello: "world" });
    const result = await apiRequest<{ hello: string }>("http://x", "/y");
    expect(result).toEqual({ hello: "world" });
  });

  it("throws ApiError with the RFC 7807 problem detail on failure", async () => {
    mockFetchOnce(400, {
      type: "https://cybercom.io/errors/validation_error",
      title: "Bad Request",
      status: 400,
      detail: "quantity must be positive",
      instance: "/api/v1/marketplace/carts/1/add_item/",
    });
    await expect(apiRequest("http://x", "/y")).rejects.toThrow(ApiError);
    await expect(apiRequest("http://x", "/y")).rejects.toThrow("quantity must be positive");
  });

  it("falls back to a generic message when the error body isn't a problem detail", async () => {
    mockFetchOnce(500, null);
    await expect(apiRequest("http://x", "/y")).rejects.toThrow("Request failed with status 500");
  });
});
