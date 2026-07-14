export type CostingMethod = 'standard' | 'fifo' | 'average';

export type WarehouseIndustryDefaults = {
  costingMethod: CostingMethod;
  negativeStockGuard: boolean;
  lowStockThreshold: number;
  enableWarehouseRestriction: boolean;
  enableDiscrepancyWorkflow: boolean;
};

export const WAREHOUSE_DEFAULTS: Record<string, WarehouseIndustryDefaults> = {
  retail:        { costingMethod: 'fifo',     negativeStockGuard: true,  lowStockThreshold: 10, enableWarehouseRestriction: true,  enableDiscrepancyWorkflow: true },
  wholesale:     { costingMethod: 'fifo',     negativeStockGuard: true,  lowStockThreshold: 50, enableWarehouseRestriction: true,  enableDiscrepancyWorkflow: true },
  manufacturing: { costingMethod: 'standard', negativeStockGuard: false, lowStockThreshold: 25, enableWarehouseRestriction: false, enableDiscrepancyWorkflow: true },
  services:      { costingMethod: 'average',  negativeStockGuard: false, lowStockThreshold: 5,  enableWarehouseRestriction: false, enableDiscrepancyWorkflow: false },
  hospitality:   { costingMethod: 'average',  negativeStockGuard: true,  lowStockThreshold: 5,  enableWarehouseRestriction: false, enableDiscrepancyWorkflow: false },
  other:         { costingMethod: 'fifo',     negativeStockGuard: true,  lowStockThreshold: 10, enableWarehouseRestriction: false, enableDiscrepancyWorkflow: false },
};

export const COSTING_LABEL: Record<CostingMethod, string> = {
  standard: 'Standard cost',
  fifo: 'FIFO (first in, first out)',
  average: 'Weighted average',
};

export function getWarehouseDefaults(industry?: string): WarehouseIndustryDefaults {
  return WAREHOUSE_DEFAULTS[industry ?? 'other'] ?? WAREHOUSE_DEFAULTS.other;
}
