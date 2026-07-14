export type ManufacturingType = 'none' | 'discrete' | 'process' | 'food' | 'pharma';

export type ManufacturingIndustryDefaults = {
  mfgType: ManufacturingType;
  enableMrp: boolean;
  enableWorkorders: boolean;
  enableMaintenance: boolean;
  enableQuality: boolean;
  enablePlm: boolean;
};

export const MANUFACTURING_DEFAULTS: Record<string, ManufacturingIndustryDefaults> = {
  retail:        { mfgType: 'none',     enableMrp: false, enableWorkorders: false, enableMaintenance: false, enableQuality: false, enablePlm: false },
  wholesale:     { mfgType: 'none',     enableMrp: false, enableWorkorders: false, enableMaintenance: false, enableQuality: false, enablePlm: false },
  manufacturing: { mfgType: 'discrete', enableMrp: true,  enableWorkorders: true,  enableMaintenance: true,  enableQuality: true,  enablePlm: true  },
  services:      { mfgType: 'none',     enableMrp: false, enableWorkorders: false, enableMaintenance: false, enableQuality: false, enablePlm: false },
  hospitality:   { mfgType: 'food',     enableMrp: true,  enableWorkorders: false, enableMaintenance: false, enableQuality: false, enablePlm: false },
  other:         { mfgType: 'none',     enableMrp: false, enableWorkorders: false, enableMaintenance: false, enableQuality: false, enablePlm: false },
};

export const MFG_TYPE_LABEL: Record<ManufacturingType, string> = {
  none: 'No manufacturing',
  discrete: 'Discrete (assembled units)',
  process: 'Process (continuous production)',
  food: 'Food production',
  pharma: 'Pharmaceutical',
};

export function getManufacturingDefaults(industry?: string): ManufacturingIndustryDefaults {
  return MANUFACTURING_DEFAULTS[industry ?? 'other'] ?? MANUFACTURING_DEFAULTS.other;
}
