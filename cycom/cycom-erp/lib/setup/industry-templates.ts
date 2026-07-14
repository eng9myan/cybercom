/**
 * Cycom Industry Templates.
 *
 * Each template encodes "what a typical business in this vertical needs out of the box" so a
 * non-technical user picks an industry and the wizard pre-fills sensible defaults. Templates are
 * intentionally light at the Company Setup stage — deeper templates (chart of accounts, payroll
 * structure, warehouse layout, POS config) live in their own wizards and inherit from the industry
 * choice persisted on the company.
 *
 * Doctrine reminder: a user selecting an industry must be able to ship a working tenant in <20%
 * of the clicks a raw Cycom configurator would take. Anything more here than is strictly necessary
 * to start is over-engineering.
 */

export type IndustryKey =
  | 'retail'
  | 'wholesale'
  | 'manufacturing'
  | 'services'
  | 'hospitality'
  | 'other';

export type IndustryTemplate = {
  key: IndustryKey;
  label: string;
  blurb: string;
  /** Suggested defaults the wizard pre-fills (the user can always override). */
  defaults: {
    multiSite: boolean;
    typicalSiteCount: number;
    fiscalYearStartMonth: number; // 1 = January
    paymentTerms: 'net_30' | 'net_15' | 'on_delivery' | 'cash';
    pricingMode: 'tax_inclusive' | 'tax_exclusive';
  };
  /** Lines shown in the inline AI Recommendation panel when this industry is selected. */
  advisor: string[];
};

export const INDUSTRY_TEMPLATES: IndustryTemplate[] = [
  {
    key: 'retail',
    label: 'Retail',
    blurb: 'Stores, branches, point-of-sale, walk-in customers.',
    defaults: {
      multiSite: true,
      typicalSiteCount: 3,
      fiscalYearStartMonth: 1,
      paymentTerms: 'cash',
      pricingMode: 'tax_inclusive',
    },
    advisor: [
      'Retail tenants almost always want a separate company per legal entity, with branches as warehouses under each company.',
      'POS pricing is usually tax-inclusive on the shelf label; the wizard will set that for you.',
      'You can run all stores under one company if they are not separately registered.',
    ],
  },
  {
    key: 'wholesale',
    label: 'Wholesale & Distribution',
    blurb: 'Bulk orders, vendors, B2B customers, longer payment terms.',
    defaults: {
      multiSite: true,
      typicalSiteCount: 2,
      fiscalYearStartMonth: 1,
      paymentTerms: 'net_30',
      pricingMode: 'tax_exclusive',
    },
    advisor: [
      'Wholesale runs on Net-30 or Net-60 by default — the wizard pre-sets Net-30 and you can change it per customer later.',
      'Pricing is typically tax-exclusive (tax appears as a line on the invoice).',
      'Most wholesalers need at least one warehouse separate from the office; the wizard will create that automatically.',
    ],
  },
  {
    key: 'manufacturing',
    label: 'Manufacturing',
    blurb: 'BOMs, work orders, raw materials, production runs.',
    defaults: {
      multiSite: false,
      typicalSiteCount: 1,
      fiscalYearStartMonth: 1,
      paymentTerms: 'net_30',
      pricingMode: 'tax_exclusive',
    },
    advisor: [
      'Manufacturing typically has one legal entity and multiple internal warehouses (raw materials, WIP, finished goods).',
      'The BOM and routing wizard is the next thing you will run after this one.',
      'Costing method defaults to standard cost for discrete manufacturing; switch to average cost for process/food.',
    ],
  },
  {
    key: 'services',
    label: 'Services / Consulting',
    blurb: 'Projects, timesheets, milestone billing, no physical inventory.',
    defaults: {
      multiSite: false,
      typicalSiteCount: 1,
      fiscalYearStartMonth: 1,
      paymentTerms: 'net_15',
      pricingMode: 'tax_exclusive',
    },
    advisor: [
      'Services tenants do not need inventory or warehouses — the wizard will skip those steps.',
      'Project-based revenue recognition and timesheet-to-invoice flow are the relevant downstream wizards.',
      'Net-15 is the typical service-industry payment term.',
    ],
  },
  {
    key: 'hospitality',
    label: 'Hospitality',
    blurb: 'Restaurants, cafés, hotels — POS-heavy, multi-shift staffing.',
    defaults: {
      multiSite: true,
      typicalSiteCount: 2,
      fiscalYearStartMonth: 1,
      paymentTerms: 'cash',
      pricingMode: 'tax_inclusive',
    },
    advisor: [
      'Hospitality typically operates one company per brand and one POS terminal per outlet.',
      'Multi-shift staffing and tip handling are configured in the Payroll wizard.',
      'Daily cash closeout is enabled on POS by default — disable it in POS settings if you do split-shift cash counts.',
    ],
  },
  {
    key: 'other',
    label: 'Other',
    blurb: 'I will configure manually.',
    defaults: {
      multiSite: false,
      typicalSiteCount: 1,
      fiscalYearStartMonth: 1,
      paymentTerms: 'net_30',
      pricingMode: 'tax_exclusive',
    },
    advisor: [
      'No defaults pre-applied. The wizard will still complete setup, but you may want to review every step.',
    ],
  },
];

export function getIndustry(key: IndustryKey): IndustryTemplate {
  return INDUSTRY_TEMPLATES.find((t) => t.key === key) ?? INDUSTRY_TEMPLATES[INDUSTRY_TEMPLATES.length - 1];
}

/** Country → suggested primary currency (ISO 4217). Used by the wizard, user can override. */
export const COUNTRY_CURRENCY: Record<string, string> = {
  JO: 'JOD',
  AE: 'AED',
  SA: 'SAR',
  EG: 'EGP',
  KW: 'KWD',
  QA: 'QAR',
  BH: 'BHD',
  OM: 'OMR',
  LB: 'LBP',
  IQ: 'IQD',
  SY: 'SYP',
  YE: 'YER',
  PS: 'JOD',
  US: 'USD',
  GB: 'GBP',
  DE: 'EUR',
  FR: 'EUR',
  IT: 'EUR',
  ES: 'EUR',
};

export const COUNTRIES: Array<{ code: string; name: string }> = [
  { code: 'JO', name: 'Jordan' },
  { code: 'AE', name: 'United Arab Emirates' },
  { code: 'SA', name: 'Saudi Arabia' },
  { code: 'EG', name: 'Egypt' },
  { code: 'KW', name: 'Kuwait' },
  { code: 'QA', name: 'Qatar' },
  { code: 'BH', name: 'Bahrain' },
  { code: 'OM', name: 'Oman' },
  { code: 'LB', name: 'Lebanon' },
  { code: 'PS', name: 'Palestine' },
  { code: 'US', name: 'United States' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'DE', name: 'Germany' },
  { code: 'FR', name: 'France' },
];
