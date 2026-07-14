export type RoleTemplate = 'strict' | 'standard' | 'open';

export type PermissionsIndustryDefaults = {
  roleTemplate: RoleTemplate;
  financeRestricted: boolean;
  payrollRestricted: boolean;
  inventoryRestricted: boolean;
  posRestricted: boolean;
  createCycomManagerGroup: boolean;
};

export const PERMISSION_DEFAULTS: Record<string, PermissionsIndustryDefaults> = {
  retail:        { roleTemplate: 'standard', financeRestricted: true,  payrollRestricted: true,  inventoryRestricted: true,  posRestricted: true,  createCycomManagerGroup: true },
  wholesale:     { roleTemplate: 'standard', financeRestricted: true,  payrollRestricted: true,  inventoryRestricted: true,  posRestricted: false, createCycomManagerGroup: true },
  manufacturing: { roleTemplate: 'strict',   financeRestricted: true,  payrollRestricted: true,  inventoryRestricted: true,  posRestricted: false, createCycomManagerGroup: true },
  services:      { roleTemplate: 'open',     financeRestricted: true,  payrollRestricted: true,  inventoryRestricted: false, posRestricted: false, createCycomManagerGroup: true },
  hospitality:   { roleTemplate: 'standard', financeRestricted: true,  payrollRestricted: true,  inventoryRestricted: false, posRestricted: true,  createCycomManagerGroup: true },
  other:         { roleTemplate: 'standard', financeRestricted: true,  payrollRestricted: true,  inventoryRestricted: false, posRestricted: false, createCycomManagerGroup: false },
};

export const ROLE_TEMPLATE_LABEL: Record<RoleTemplate, string> = {
  strict: 'Strict (least privilege)',
  standard: 'Standard (role-based)',
  open: 'Open (all-internal access)',
};

export function getPermissionDefaults(industry?: string): PermissionsIndustryDefaults {
  return PERMISSION_DEFAULTS[industry ?? 'other'] ?? PERMISSION_DEFAULTS.other;
}
