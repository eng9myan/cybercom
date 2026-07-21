const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.cy-com.com";

export interface DemoProvisionPayload {
  product_code: string;
  email: string;
  org_name?: string;
  locale?: "en" | "ar";
  // demo.cy-com.com sandbox: shortens the trial to 3h instead of the
  // default 7 days. See platform/tenant/services.py's SANDBOX_TRIAL_HOURS.
  sandbox?: boolean;
}

export interface DemoProvisionResponse {
  tenant_slug: string;
  // realm_name is present for every Keycloak-backed product. cyshop has its
  // own separate, unfederated auth system (adapter approach — see
  // platform/tenant/services.py::_provision_demo_cyshop) so it returns
  // cyshop_subdomain instead and omits realm_name.
  realm_name?: string;
  product_code?: string;
  cyshop_subdomain?: string;
  username: string;
  password: string;
  trial_ends_at: string;
}

export interface DemoProvisionError {
  detail: string;
  contact_required?: boolean;
}

export class DemoProvisionApiError extends Error {
  constructor(
    public status: number,
    public body: DemoProvisionError,
  ) {
    super(body.detail);
  }
}

export const demoProvisionApi = {
  // Bypasses the shared apiClient — the DRF error shape here ({detail,
  // contact_required}) doesn't match apiClient's generic {errors: {...}}
  // validation-error convention, so that helper would silently drop both
  // fields on failure.
  async provision(payload: DemoProvisionPayload): Promise<DemoProvisionResponse> {
    const baseUrl = DEFAULT_BASE_URL.replace(/\/$/, "");
    const res = await fetch(`${baseUrl}/api/v1/public/demo/provision/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await res.json().catch(() => ({}) as DemoProvisionError);
    if (!res.ok) {
      throw new DemoProvisionApiError(res.status, body as DemoProvisionError);
    }
    return body as DemoProvisionResponse;
  },
};
