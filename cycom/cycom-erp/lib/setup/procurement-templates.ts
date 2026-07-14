export type ApprovalPolicy = 'auto' | 'single' | 'dual';

export type ProcurementIndustryDefaults = {
  approvalPolicy: ApprovalPolicy;
  approvalThresholdAmount: number; // in tenant currency; >= amount needs approval
  rfqValidityDays: number;
  defaultLeadTimeDays: number;
  enableAltanmyaExtension: boolean;
  enableApprovalContact: boolean;
};

export const PROCUREMENT_DEFAULTS: Record<string, ProcurementIndustryDefaults> = {
  retail:        { approvalPolicy: 'single', approvalThresholdAmount: 1000,  rfqValidityDays: 14, defaultLeadTimeDays: 7,  enableAltanmyaExtension: true,  enableApprovalContact: true  },
  wholesale:     { approvalPolicy: 'dual',   approvalThresholdAmount: 5000,  rfqValidityDays: 21, defaultLeadTimeDays: 14, enableAltanmyaExtension: true,  enableApprovalContact: true  },
  manufacturing: { approvalPolicy: 'dual',   approvalThresholdAmount: 2500,  rfqValidityDays: 30, defaultLeadTimeDays: 21, enableAltanmyaExtension: true,  enableApprovalContact: true  },
  services:      { approvalPolicy: 'single', approvalThresholdAmount: 500,   rfqValidityDays: 14, defaultLeadTimeDays: 5,  enableAltanmyaExtension: false, enableApprovalContact: true  },
  hospitality:   { approvalPolicy: 'single', approvalThresholdAmount: 750,   rfqValidityDays: 7,  defaultLeadTimeDays: 2,  enableAltanmyaExtension: false, enableApprovalContact: false },
  other:         { approvalPolicy: 'single', approvalThresholdAmount: 1000,  rfqValidityDays: 14, defaultLeadTimeDays: 7,  enableAltanmyaExtension: false, enableApprovalContact: false },
};

export const APPROVAL_POLICY_LABEL: Record<ApprovalPolicy, string> = {
  auto: 'Auto-confirm (no approval)',
  single: 'Manager approval',
  dual: 'Two-manager approval',
};

export function getProcurementDefaults(industry?: string): ProcurementIndustryDefaults {
  return PROCUREMENT_DEFAULTS[industry ?? 'other'] ?? PROCUREMENT_DEFAULTS.other;
}
