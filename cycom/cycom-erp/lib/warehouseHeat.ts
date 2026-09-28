// Shared occupancy heat-scale + per-type sizing for the 2D and 3D warehouse
// map views, so both draw from the exact same rules as the existing list
// view's occupancyTone() (app/inventory/warehouse-map/page.tsx) rather than
// drifting into a second, slightly-different color scale.

export function occupancyHexColor(pct: number | null): string {
  if (pct === null) return '#334155';       // slate-700: unknown capacity
  if (pct >= 100) return '#f43f5e';         // rose-500: full/over
  if (pct >= 75) return '#f59e0b';          // amber-500: high
  if (pct >= 40) return '#06b6d4';          // cyan-500: medium
  if (pct > 0) return '#10b981';            // emerald-500: low
  return '#1e293b';                         // slate-800: empty
}

// Vertical extrusion height (3D) in floor-plan units, by location type --
// a warehouse's own hierarchy depth varies (zone>bin directly, or all 5
// levels), so this keys off the type itself rather than tree depth.
export const TYPE_HEIGHT: Record<string, number> = {
  zone: 0.15,
  aisle: 0.1,
  rack: 2.4,
  shelf: 1.6,
  bin: 1.0,
};

export const DEFAULT_SIZE: Record<string, { w: number; d: number }> = {
  zone: { w: 6, d: 6 },
  aisle: { w: 4, d: 1 },
  rack: { w: 1.2, d: 3 },
  shelf: { w: 1, d: 1 },
  bin: { w: 0.8, d: 0.8 },
};

export interface FlatLocationNode {
  id: string;
  code: string;
  name: string;
  location_type: string;
  parent_path: string;
  capacity: number | null;
  occupancy_percent: number | null;
  total_quantity: number;
  total_product_count: number;
  pos_x: number | null;
  pos_y: number | null;
  size_w: number | null;
  size_d: number | null;
}

/** Walks the layout tree (any depth) into a flat list -- the map views place
 * whatever level(s) a tenant has actually positioned, not a fixed depth. */
export function flattenLayout(tree: any[]): FlatLocationNode[] {
  const out: FlatLocationNode[] = [];
  const walk = (node: any, parentPath: string) => {
    out.push({
      id: node.id,
      code: node.code,
      name: node.name,
      location_type: node.location_type,
      parent_path: parentPath,
      capacity: node.capacity,
      occupancy_percent: node.occupancy_percent,
      total_quantity: node.total_quantity,
      total_product_count: node.total_product_count,
      pos_x: node.pos_x,
      pos_y: node.pos_y,
      size_w: node.size_w,
      size_d: node.size_d,
    });
    const path = parentPath ? `${parentPath} / ${node.code}` : node.code;
    (node.children || []).forEach((c: any) => walk(c, path));
  };
  tree.forEach((n) => walk(n, ''));
  return out;
}
