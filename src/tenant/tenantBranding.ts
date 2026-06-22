/**
 * CyberCom Mobile — Tenant Branding
 * Applies tenant white-label branding to the app at runtime.
 */

import { TenantBrandingContext } from './tenantContext';

export interface AppliedBranding {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
  };
  appName: string;
  logoSource: { uri: string } | null;
  isRTL: boolean;
  language: string;
  theme: 'light' | 'dark' | 'auto';
}

const DEFAULT: AppliedBranding = {
  colors: { primary: '#1B4F8A', secondary: '#00B4D8', accent: '#90E0EF' },
  appName: 'CyberCom',
  logoSource: null,
  isRTL: true,
  language: 'ar',
  theme: 'auto',
};

let _applied: AppliedBranding = DEFAULT;

/**
 * Apply tenant branding from a fetched TenantBrandingContext.
 * Call after fetchTenantContext() resolves.
 */
export function applyTenantBranding(branding: TenantBrandingContext): AppliedBranding {
  _applied = {
    colors: {
      primary: branding.primaryColor,
      secondary: branding.secondaryColor,
      accent: branding.accentColor,
    },
    appName: branding.appName || 'CyberCom',
    logoSource: branding.logoUrl ? { uri: branding.logoUrl } : null,
    isRTL: branding.rtlDefault,
    language: branding.defaultLanguage,
    theme: branding.theme,
  };
  return _applied;
}

export function getAppliedBranding(): AppliedBranding {
  return _applied;
}

export function resetBranding(): void {
  _applied = DEFAULT;
}

/** Helper for StyleSheet colors in components. */
export function brandColor(key: 'primary' | 'secondary' | 'accent'): string {
  return _applied.colors[key];
}
