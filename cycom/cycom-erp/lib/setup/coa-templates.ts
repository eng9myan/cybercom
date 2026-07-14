/**
 * Country-aware Chart-of-Accounts recommendations.
 *
 * Cycom ships per-country localization modules (`l10n_<cc>`) that pre-load a complete chart of
 * accounts plus the standard tax structure for that jurisdiction. Installing the right one is
 * almost always the right answer — the wizard just picks it for the user.
 *
 * Default VAT rates are the headline rate for each country at time of writing. The user can
 * override per-tenant.
 */

export type CoaCountryTemplate = {
  countryCode: string;
  l10nModule: string;
  defaultSalesTaxPct: number;
  defaultPurchaseTaxPct: number;
  advisor: string;
};

export const COA_COUNTRY_TEMPLATES: Record<string, CoaCountryTemplate> = {
  JO: {
    countryCode: 'JO',
    l10nModule: 'l10n_jo',
    defaultSalesTaxPct: 16,
    defaultPurchaseTaxPct: 16,
    advisor: 'Jordan uses a 16% General Sales Tax. The Jordan localization includes the standard chart and tax templates required for ISTD compliance.',
  },
  AE: {
    countryCode: 'AE',
    l10nModule: 'l10n_ae',
    defaultSalesTaxPct: 5,
    defaultPurchaseTaxPct: 5,
    advisor: 'UAE uses a 5% VAT. The FTA-compliant chart and tax codes are included in the UAE localization.',
  },
  SA: {
    countryCode: 'SA',
    l10nModule: 'l10n_sa',
    defaultSalesTaxPct: 15,
    defaultPurchaseTaxPct: 15,
    advisor: 'Saudi Arabia uses a 15% VAT (raised from 5% in 2020). ZATCA e-invoicing fields are in the Saudi localization.',
  },
  EG: {
    countryCode: 'EG',
    l10nModule: 'l10n_eg',
    defaultSalesTaxPct: 14,
    defaultPurchaseTaxPct: 14,
    advisor: 'Egypt uses a 14% VAT. The Egypt localization includes the standard ETA chart.',
  },
  KW: {
    countryCode: 'KW',
    l10nModule: 'l10n_generic_coa',
    defaultSalesTaxPct: 0,
    defaultPurchaseTaxPct: 0,
    advisor: 'Kuwait currently has no VAT. The generic chart is used; add custom taxes only if needed.',
  },
  QA: {
    countryCode: 'QA',
    l10nModule: 'l10n_generic_coa',
    defaultSalesTaxPct: 0,
    defaultPurchaseTaxPct: 0,
    advisor: 'Qatar has no VAT yet. Generic chart with no tax pre-loaded.',
  },
  BH: {
    countryCode: 'BH',
    l10nModule: 'l10n_generic_coa',
    defaultSalesTaxPct: 10,
    defaultPurchaseTaxPct: 10,
    advisor: 'Bahrain uses 10% VAT (raised from 5% in 2022).',
  },
  OM: {
    countryCode: 'OM',
    l10nModule: 'l10n_generic_coa',
    defaultSalesTaxPct: 5,
    defaultPurchaseTaxPct: 5,
    advisor: 'Oman uses a 5% VAT, introduced 2021.',
  },
  LB: {
    countryCode: 'LB',
    l10nModule: 'l10n_generic_coa',
    defaultSalesTaxPct: 11,
    defaultPurchaseTaxPct: 11,
    advisor: 'Lebanon uses an 11% VAT. No dedicated Cycom localization yet — generic chart with manual tax.',
  },
  PS: {
    countryCode: 'PS',
    l10nModule: 'l10n_generic_coa',
    defaultSalesTaxPct: 16,
    defaultPurchaseTaxPct: 16,
    advisor: 'Palestine commonly aligns with Jordan-equivalent VAT (16%). Generic chart used.',
  },
  US: {
    countryCode: 'US',
    l10nModule: 'l10n_us',
    defaultSalesTaxPct: 0,
    defaultPurchaseTaxPct: 0,
    advisor: 'The US has no national VAT. Sales tax is state-specific — configure per state in the tax engine after install.',
  },
  GB: {
    countryCode: 'GB',
    l10nModule: 'l10n_uk',
    defaultSalesTaxPct: 20,
    defaultPurchaseTaxPct: 20,
    advisor: 'UK uses 20% VAT. The UK localization includes the standard HMRC categories.',
  },
  DE: {
    countryCode: 'DE',
    l10nModule: 'l10n_de_skr03',
    defaultSalesTaxPct: 19,
    defaultPurchaseTaxPct: 19,
    advisor: 'Germany uses 19% VAT. SKR03 is the typical small/medium business chart; SKR04 is also available.',
  },
  FR: {
    countryCode: 'FR',
    l10nModule: 'l10n_fr',
    defaultSalesTaxPct: 20,
    defaultPurchaseTaxPct: 20,
    advisor: 'France uses 20% VAT. The French localization includes the official PCG chart.',
  },
};

export function getCoaTemplate(countryCode: string): CoaCountryTemplate {
  return (
    COA_COUNTRY_TEMPLATES[countryCode] ?? {
      countryCode,
      l10nModule: 'l10n_generic_coa',
      defaultSalesTaxPct: 0,
      defaultPurchaseTaxPct: 0,
      advisor: 'No country-specific localization mapped — Cycom will install the generic chart of accounts. You can swap modules later if Cycom ships a localization for this country.',
    }
  );
}
