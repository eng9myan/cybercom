"use client";

import { useEffect, useMemo, useState } from "react";
import { Package, AlertTriangle, Boxes, Laptop } from "lucide-react";
import { cyed } from "@/lib/cyed";
import { PageHeader, ErrorNote, Loading, Field } from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/table";
import { Panel, Badge, Segmented } from "@/components/kit";
import { useToast } from "@/components/Toast";

type Item = {
  id: string; name: string; sku?: string; category?: string; unit: string;
  on_hand: string; reorder_level: string; location?: string;
};
type LowStock = {
  id: string; name: string; sku: string; category: string; on_hand: string;
  reorder_level: string; unit: string; shortfall: string; severity: string;
};
type CategoryRow = { category: string; items: number; units_on_hand: string; low_stock: number };
type Move = { id: string; item: string; move_type: string; quantity: string; reason?: string; reference?: string };
type Asset = {
  id: string; name: string; acquisition_cost?: string; annual_depreciation?: string;
  current_book_value?: string; acquisition_date?: string | null;
};

type Tab = "stock" | "low" | "moves" | "assets";

export default function InventoryPage() {
  const [tab, setTab] = useState<Tab>("stock");
  const [items, setItems] = useState<Item[]>([]);
  const [low, setLow] = useState<LowStock[]>([]);
  const [cats, setCats] = useState<CategoryRow[]>([]);
  const [moves, setMoves] = useState<Move[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const [name, setName] = useState("");
  const [category, setCategory] = useState("IT equipment");
  const [onHand, setOnHand] = useState("0");
  const [reorder, setReorder] = useState("5");

  const load = async () => {
    setLoading(true);
    try {
      const [i, l, c, m, a] = await Promise.all([
        cyed.list<Item>("inventory/items/"),
        cyed.get<{ rows: LowStock[] }>("inventory/items/low-stock/"),
        cyed.get<{ rows: CategoryRow[] }>("inventory/items/by-category/"),
        cyed.list<Move>("inventory/moves/"),
        cyed.list<Asset>("assets/assets/"),
      ]);
      setItems(i); setLow(l.rows || []); setCats(c.rows || []); setMoves(m); setAssets(a);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load inventory");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const itemName = (id: string) => items.find((x) => x.id === id)?.name || "—";

  const stats = useMemo(() => ({
    items: items.length,
    low: low.length,
    critical: low.filter((l) => l.severity === "critical").length,
    assets: assets.length,
  }), [items, low, assets]);

  const addItem = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await cyed.create("inventory/items/", {
        name, category, on_hand: onHand, reorder_level: reorder,
      });
      toast.push(`${name} added to the register`);
      setName("");
      await load();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Could not add item", "bad");
    }
  };

  const move = async (item: Item, type: "in" | "out") => {
    const q = window.prompt(`Quantity to move ${type}:`, "1");
    if (!q) return;
    try {
      await cyed.create("inventory/moves/", { item: item.id, move_type: type, quantity: q, reason: "Manual adjustment" });
      toast.push(`Stock ${type === "in" ? "received" : "issued"}`);
      await load();
    } catch (e) {
      toast.push(e instanceof Error ? e.message : "Stock move failed", "bad");
    }
  };

  if (loading) return <Loading label="Loading inventory…" />;

  const itemCols: Column<Item>[] = [
    { key: "name", header: "Item", render: (i) => <span style={{ fontWeight: 600 }}>{i.name}</span> },
    { key: "cat", header: "Category", width: 160, render: (i) => <span className="pill">{i.category || "—"}</span> },
    {
      key: "onhand", header: "On hand", width: 120, align: "right",
      render: (i) => (
        <span className={Number(i.on_hand) <= Number(i.reorder_level) ? "status status-warn" : undefined}>
          {i.on_hand} {i.unit}
        </span>
      ),
    },
    { key: "reorder", header: "Reorder at", width: 110, align: "right", render: (i) => i.reorder_level },
    { key: "loc", header: "Location", render: (i) => <span style={{ color: "var(--muted)" }}>{i.location || "—"}</span> },
    {
      key: "act", header: "", align: "right",
      render: (i) => (
        <span style={{ display: "inline-flex", gap: 6 }}>
          <button className="btn btn-ghost" onClick={() => move(i, "in")}>In</button>
          <button className="btn btn-ghost" onClick={() => move(i, "out")}>Out</button>
        </span>
      ),
    },
  ];

  const lowCols: Column<LowStock>[] = [
    { key: "name", header: "Item", render: (l) => <span style={{ fontWeight: 600 }}>{l.name}</span> },
    { key: "cat", header: "Category", width: 160, render: (l) => <span className="pill">{l.category || "—"}</span> },
    { key: "onhand", header: "On hand", width: 110, align: "right", render: (l) => `${l.on_hand} ${l.unit}` },
    { key: "short", header: "Shortfall", width: 110, align: "right", render: (l) => l.shortfall },
    {
      key: "sev", header: "Severity", width: 140,
      render: (l) => <span className={`status ${l.severity === "critical" ? "status-bad" : "status-warn"}`}>{l.severity}</span>,
    },
  ];

  const moveCols: Column<Move>[] = [
    { key: "item", header: "Item", render: (m) => <span style={{ fontWeight: 600 }}>{itemName(m.item)}</span> },
    { key: "type", header: "Type", width: 120, render: (m) => <span className="pill" style={{ textTransform: "capitalize" }}>{m.move_type}</span> },
    { key: "qty", header: "Qty", width: 90, align: "right", render: (m) => m.quantity },
    { key: "reason", header: "Reason", render: (m) => <span style={{ color: "var(--muted)" }}>{m.reason || "—"}</span> },
    { key: "ref", header: "Reference", render: (m) => <span style={{ color: "var(--faint)" }}>{m.reference || "—"}</span> },
  ];

  const assetCols: Column<Asset>[] = [
    { key: "name", header: "Asset", render: (a) => <span style={{ fontWeight: 600 }}>{a.name}</span> },
    { key: "cost", header: "Cost", width: 120, align: "right", render: (a) => `$${a.acquisition_cost ?? "0"}` },
    { key: "dep", header: "Annual dep.", width: 130, align: "right", render: (a) => `$${a.annual_depreciation ?? "0"}` },
    { key: "book", header: "Book value", width: 130, align: "right", render: (a) => <strong>${a.current_book_value ?? "0"}</strong> },
    { key: "date", header: "Acquired", width: 130, render: (a) => <span style={{ color: "var(--muted)" }}>{a.acquisition_date || "—"}</span> },
  ];

  return (
    <div>
      <PageHeader
        title="Inventory & Assets"
        subtitle="Stock register, low-stock alerts, movement log and depreciating assets."
        action={
          <Segmented
            value={tab}
            onChange={setTab}
            options={[
              { value: "stock", label: "Stock" },
              { value: "low", label: "Low stock" },
              { value: "moves", label: "Movements" },
              { value: "assets", label: "Assets" },
            ]}
          />
        }
      />

      <div className="grid gap-4 stagger mb-5" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))" }}>
        <StatCard label="Stock items" value={stats.items} accent="cyan" icon={<Package size={17} />} />
        <StatCard label="Below reorder" value={stats.low} accent="violet" icon={<AlertTriangle size={17} />} />
        <StatCard label="Out of stock" value={stats.critical} accent="blue" icon={<Boxes size={17} />} />
        <StatCard label="Assets" value={stats.assets} accent="cyan" icon={<Laptop size={17} />} />
      </div>

      {cats.length > 0 && (
        <Panel title="By category" className="mb-4">
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {cats.map((c) => (
              <div key={c.category} className="card p-3" style={{ minWidth: 160 }}>
                <div className="label">{c.category}</div>
                <div style={{ fontSize: "1.3rem", fontWeight: 800, marginTop: 4 }}>{c.units_on_hand}</div>
                <div className="text-xs" style={{ color: "var(--muted)" }}>
                  {c.items} item{c.items === 1 ? "" : "s"}
                  {c.low_stock > 0 && <span style={{ color: "var(--warn)" }}> · {c.low_stock} low</span>}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {error && <ErrorNote error={error} />}

      {tab === "stock" && (
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20, alignItems: "start" }}>
          <Panel title="New stock item">
            <form onSubmit={addItem} className="space-y-3">
              <Field label="Name"><input className="input" value={name} onChange={(e) => setName(e.target.value)} required /></Field>
              <Field label="Category">
                <select className="input" value={category} onChange={(e) => setCategory(e.target.value)}>
                  {["IT equipment", "furniture", "textbooks", "consumables", "other"].map((c) => <option key={c}>{c}</option>)}
                </select>
              </Field>
              <div style={{ display: "flex", gap: 10 }}>
                <div style={{ flex: 1 }}><Field label="On hand"><input className="input" type="number" value={onHand} onChange={(e) => setOnHand(e.target.value)} /></Field></div>
                <div style={{ flex: 1 }}><Field label="Reorder at"><input className="input" type="number" value={reorder} onChange={(e) => setReorder(e.target.value)} /></Field></div>
              </div>
              <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }}>Add item</button>
            </form>
          </Panel>
          <DataTable columns={itemCols} rows={items} filterKeys={["name", "sku", "category"]} emptyLabel="Nothing in the register yet." />
        </div>
      )}

      {tab === "low" && <DataTable columns={lowCols} rows={low} emptyLabel="Nothing below its reorder level." />}
      {tab === "moves" && <DataTable columns={moveCols} rows={moves} emptyLabel="No stock movements recorded." />}
      {tab === "assets" && <DataTable columns={assetCols} rows={assets} filterKeys={["name"]} emptyLabel="No assets registered." />}
    </div>
  );
}
