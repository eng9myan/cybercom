export type SalesMotion = 'b2c' | 'b2b' | 'mixed';

export type SalesIndustryDefaults = {
  motion: SalesMotion;
  freeDiscountLimitPct: number;       // up to this, no approval needed
  managerDiscountLimitPct: number;    // above this needs manager approval
  dualApprovalThresholdPct: number;   // above this needs two approvers
  enableDiscountExceptionApproval: boolean;
  enableLineLevelApproval: boolean;
  enablePricingControl: boolean;
  enableSaleFiscalKeepPrice: boolean;
};

export const SALES_DEFAULTS: Record<string, SalesIndustryDefaults> = {
  retail:        { motion: 'b2c',   freeDiscountLimitPct: 5,  managerDiscountLimitPct: 10, dualApprovalThresholdPct: 20, enableDiscountExceptionApproval: true,  enableLineLevelApproval: true,  enablePricingControl: true,  enableSaleFiscalKeepPrice: true  },
  wholesale:     { motion: 'b2b',   freeDiscountLimitPct: 5,  managerDiscountLimitPct: 12, dualApprovalThresholdPct: 18, enableDiscountExceptionApproval: true,  enableLineLevelApproval: true,  enablePricingControl: true,  enableSaleFiscalKeepPrice: true  },
  manufacturing: { motion: 'b2b',   freeDiscountLimitPct: 3,  managerDiscountLimitPct: 8,  dualApprovalThresholdPct: 15, enableDiscountExceptionApproval: true,  enableLineLevelApproval: true,  enablePricingControl: true,  enableSaleFiscalKeepPrice: false },
  services:      { motion: 'b2b',   freeDiscountLimitPct: 0,  managerDiscountLimitPct: 10, dualApprovalThresholdPct: 25, enableDiscountExceptionApproval: true,  enableLineLevelApproval: false, enablePricingControl: false, enableSaleFiscalKeepPrice: false },
  hospitality:   { motion: 'b2c',   freeDiscountLimitPct: 10, managerDiscountLimitPct: 20, dualApprovalThresholdPct: 30, enableDiscountExceptionApproval: false, enableLineLevelApproval: false, enablePricingControl: false, enableSaleFiscalKeepPrice: false },
  other:         { motion: 'mixed', freeDiscountLimitPct: 5,  managerDiscountLimitPct: 10, dualApprovalThresholdPct: 20, enableDiscountExceptionApproval: true,  enableLineLevelApproval: false, enablePricingControl: false, enableSaleFiscalKeepPrice: false },
};

export const MOTION_LABEL: Record<SalesMotion, string> = {
  b2c: 'B2C (consumer)',
  b2b: 'B2B (business buyers)',
  mixed: 'Mixed',
};

export function getSalesDefaults(industry?: string): SalesIndustryDefaults {
  return SALES_DEFAULTS[industry ?? 'other'] ?? SALES_DEFAULTS.other;
}
