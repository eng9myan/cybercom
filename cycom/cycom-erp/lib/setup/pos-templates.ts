export type PaymentMix = 'cash_heavy' | 'card_heavy' | 'split';

export type PosIndustryDefaults = {
  paymentMix: PaymentMix;
  dailyCashCloseout: boolean;
  enableAdvanceOrder: boolean;
  enablePledge: boolean;
  enableRefundBuyer: boolean;
  enableCashMoveAccess: boolean;
  enablePredefinedDiscounts: boolean;
  enablePosRounding: boolean;
};

export const POS_DEFAULTS: Record<string, PosIndustryDefaults> = {
  retail:        { paymentMix: 'split',      dailyCashCloseout: true,  enableAdvanceOrder: true,  enablePledge: true,  enableRefundBuyer: true,  enableCashMoveAccess: true,  enablePredefinedDiscounts: true,  enablePosRounding: true  },
  wholesale:     { paymentMix: 'card_heavy', dailyCashCloseout: false, enableAdvanceOrder: true,  enablePledge: false, enableRefundBuyer: false, enableCashMoveAccess: false, enablePredefinedDiscounts: true,  enablePosRounding: false },
  manufacturing: { paymentMix: 'card_heavy', dailyCashCloseout: false, enableAdvanceOrder: false, enablePledge: false, enableRefundBuyer: false, enableCashMoveAccess: false, enablePredefinedDiscounts: false, enablePosRounding: false },
  services:      { paymentMix: 'card_heavy', dailyCashCloseout: false, enableAdvanceOrder: false, enablePledge: false, enableRefundBuyer: false, enableCashMoveAccess: false, enablePredefinedDiscounts: false, enablePosRounding: false },
  hospitality:   { paymentMix: 'cash_heavy', dailyCashCloseout: true,  enableAdvanceOrder: false, enablePledge: false, enableRefundBuyer: true,  enableCashMoveAccess: true,  enablePredefinedDiscounts: true,  enablePosRounding: true  },
  other:         { paymentMix: 'split',      dailyCashCloseout: true,  enableAdvanceOrder: false, enablePledge: false, enableRefundBuyer: false, enableCashMoveAccess: false, enablePredefinedDiscounts: false, enablePosRounding: false },
};

export const PAYMENT_MIX_LABEL: Record<PaymentMix, string> = {
  cash_heavy: 'Cash-heavy (>70% cash)',
  card_heavy: 'Card-heavy (<30% cash)',
  split: 'Roughly split',
};

export function getPosDefaults(industry?: string): PosIndustryDefaults {
  return POS_DEFAULTS[industry ?? 'other'] ?? POS_DEFAULTS.other;
}
