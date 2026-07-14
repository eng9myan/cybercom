/**
 * Payroll defaults per industry. Cycom uses the industry chosen in Company Setup to pre-fill
 * pay frequency, weekly hours, and overtime/lateness policy. User can override every value.
 */

export type PayFrequency = 'monthly' | 'bi_weekly' | 'weekly';

export type PayrollIndustryDefaults = {
  frequency: PayFrequency;
  weeklyHours: number;
  otMultiplier: number;
  latenessGraceMinutes: number;
};

export const PAYROLL_DEFAULTS: Record<string, PayrollIndustryDefaults> = {
  retail:        { frequency: 'monthly',   weeklyHours: 48, otMultiplier: 1.5, latenessGraceMinutes: 15 },
  wholesale:     { frequency: 'monthly',   weeklyHours: 45, otMultiplier: 1.5, latenessGraceMinutes: 15 },
  manufacturing: { frequency: 'bi_weekly', weeklyHours: 48, otMultiplier: 1.5, latenessGraceMinutes: 10 },
  services:      { frequency: 'monthly',   weeklyHours: 40, otMultiplier: 1.5, latenessGraceMinutes: 30 },
  hospitality:   { frequency: 'bi_weekly', weeklyHours: 54, otMultiplier: 1.5, latenessGraceMinutes: 10 },
  other:         { frequency: 'monthly',   weeklyHours: 40, otMultiplier: 1.5, latenessGraceMinutes: 15 },
};

export const FREQUENCY_LABEL: Record<PayFrequency, string> = {
  monthly: 'Monthly',
  bi_weekly: 'Bi-weekly (every 2 weeks)',
  weekly: 'Weekly',
};

export function getPayrollDefaults(industry?: string): PayrollIndustryDefaults {
  return PAYROLL_DEFAULTS[industry ?? 'other'] ?? PAYROLL_DEFAULTS.other;
}
