import { walletApi } from "../wallet";

describe("walletApi", () => {
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

  it("getBalance sends the currency as a query param", async () => {
    mockFetch({ person_id: "p-1", currency: "USD", balance: "42.00" });
    await walletApi.getBalance("token", "USD");
    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("/wallet/balance/");
    expect(url).toContain("currency=USD");
  });

  it("topUp POSTs currency/amount/reference", async () => {
    mockFetch({ id: "e-1", entry_type: "topup", amount: "10.00", balance_after: "52.00", reference: "mobile_topup", created_by: "", created_at: "2026-01-01T00:00:00Z" });
    await walletApi.topUp("token", "USD", "10.00", "mobile_topup");
    const [url, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("/wallet/topup/");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ currency: "USD", amount: "10.00", reference: "mobile_topup" });
  });

  it("includes the bearer token on both calls", async () => {
    mockFetch({ person_id: "p-1", currency: "USD", balance: "0.00" });
    await walletApi.getBalance("secret-token", "USD");
    const [, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(init.headers.Authorization).toBe("Bearer secret-token");
  });
});
