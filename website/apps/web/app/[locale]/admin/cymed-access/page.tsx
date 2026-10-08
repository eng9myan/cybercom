"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Loader2, Plus, Trash2, Stethoscope } from "lucide-react";
import {
  adminApi,
  type Tenant,
  type CymedProduct,
  type CymedEdition,
  type CymedTenantProductSubscription,
} from "@/lib/adminApi";

export default function AdminCymedAccessPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [products, setProducts] = useState<CymedProduct[]>([]);
  const [editions, setEditions] = useState<CymedEdition[]>([]);
  const [subs, setSubs] = useState<CymedTenantProductSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actingId, setActingId] = useState<string | null>(null);

  const [tenantId, setTenantId] = useState("");
  const [productCode, setProductCode] = useState("");
  const [editionCode, setEditionCode] = useState("");
  const [granting, setGranting] = useState(false);

  const tenantsById = useMemo(
    () => Object.fromEntries(tenants.map((t) => [t.id, t])),
    [tenants],
  );
  const editionsForProduct = useMemo(
    () => editions.filter((e) => products.find((p) => p.code === productCode)?.id === e.product),
    [editions, products, productCode],
  );

  const load = () => {
    setLoading(true);
    setError(null);
    return Promise.all([
      adminApi.listTenants(),
      adminApi.listCymedProducts(),
      adminApi.listCymedEditions(),
      adminApi.listCymedTenantSubscriptions(),
    ])
      .then(([tenantRows, productRows, editionRows, subRows]) => {
        setTenants(tenantRows);
        setProducts(productRows);
        setEditions(editionRows);
        setSubs(subRows);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load CyMed product access"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    // load() sets state inside its own .then/.catch/.finally callbacks, not
    // synchronously in the effect body — safe, but the compiler's static
    // analysis can't see through the function call to verify that.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, []);

  async function grant() {
    if (!tenantId || !productCode || !editionCode) return;
    setGranting(true);
    setError(null);
    try {
      await adminApi.grantCymedProduct(tenantId, productCode, editionCode);
      setTenantId("");
      setProductCode("");
      setEditionCode("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to grant product access");
    } finally {
      setGranting(false);
    }
  }

  async function revoke(sub: CymedTenantProductSubscription) {
    setActingId(sub.id);
    try {
      await adminApi.revokeCymedProduct(sub.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to revoke product access");
    } finally {
      setActingId(null);
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-semibold text-white mb-1">CyMed Product Access</h1>
        <p className="text-sm text-cy-gray-400">
          Grant a tenant access to a standalone CyMed product (Hospital, Clinic, Pharmacy, Laboratory,
          Imaging). {subs.length} active grant{subs.length === 1 ? "" : "s"}.
        </p>
      </div>

      {error && (
        <div className="mb-4 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      <div className="glass-card rounded-xl p-5 mb-6">
        <h2 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
          <Plus className="w-4 h-4 text-cy-orange" /> Grant access
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <select
            className="glass-card rounded-lg px-3 py-2.5 text-sm text-white outline-none border border-cy-glass-border focus:border-cy-orange"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
          >
            <option value="">Select tenant…</option>
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>{t.display_name || t.name}</option>
            ))}
          </select>
          <select
            className="glass-card rounded-lg px-3 py-2.5 text-sm text-white outline-none border border-cy-glass-border focus:border-cy-orange"
            value={productCode}
            onChange={(e) => {
              setProductCode(e.target.value);
              setEditionCode("");
            }}
          >
            <option value="">Select product…</option>
            {products.filter((p) => p.is_active).map((p) => (
              <option key={p.id} value={p.code}>{p.name}</option>
            ))}
          </select>
          <select
            className="glass-card rounded-lg px-3 py-2.5 text-sm text-white outline-none border border-cy-glass-border focus:border-cy-orange disabled:opacity-50"
            value={editionCode}
            onChange={(e) => setEditionCode(e.target.value)}
            disabled={!productCode}
          >
            <option value="">Select edition…</option>
            {editionsForProduct.filter((e) => e.is_active).map((e) => (
              <option key={e.id} value={e.code}>{e.name}</option>
            ))}
          </select>
          <button
            onClick={grant}
            disabled={!tenantId || !productCode || !editionCode || granting}
            className="btn-primary text-sm py-2.5 px-4 disabled:opacity-50 inline-flex items-center justify-center gap-1.5"
          >
            {granting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
            Grant
          </button>
        </div>
        <p className="mt-3 text-xs text-cy-gray-500">
          Granting again for the same tenant/product upgrades or downgrades the existing edition — it
          never creates a duplicate.
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-5 h-5 text-cy-orange animate-spin" />
        </div>
      ) : (
        <div className="space-y-2">
          {subs.map((sub) => {
            const tenant = tenantsById[sub.tenant_id];
            const product = products.find((p) => p.code === sub.product_code);
            return (
              <div key={sub.id} className="glass-card rounded-xl p-4 flex items-center gap-4">
                <div className="w-9 h-9 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center flex-shrink-0">
                  <Stethoscope className="w-4 h-4 text-teal-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">
                    {tenant?.display_name || tenant?.name || sub.tenant_id}
                  </div>
                  <div className="text-xs text-cy-gray-400">
                    {product?.name || sub.product_code} · {sub.edition_code}
                  </div>
                </div>
                <span
                  className={`inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full border shrink-0 ${
                    sub.is_active
                      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                      : "text-cy-gray-400 bg-cy-gray-500/10 border-cy-gray-500/20"
                  }`}
                >
                  {sub.is_active ? "Active" : "Inactive"}
                </span>
                <button
                  onClick={() => revoke(sub)}
                  disabled={actingId === sub.id}
                  title="Revoke access"
                  className="p-2 rounded-lg text-cy-gray-400 hover:text-red-400 hover:bg-red-500/10 disabled:opacity-50 transition-colors"
                >
                  {actingId === sub.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                </button>
              </div>
            );
          })}
          {subs.length === 0 && (
            <div className="text-center py-12 text-cy-gray-400 text-sm">No CyMed product grants yet.</div>
          )}
        </div>
      )}
    </div>
  );
}
