export type OrgSize = 'small' | 'medium' | 'large';

export type HrIndustryDefaults = {
  orgSize: OrgSize;
  seedDepartments: string[];
  enableBiometricZk: boolean;
  enableSingleDeviceBinding: boolean;
  enableGeofence: boolean;
  enableHealthInsurance: boolean;
  enableEmployeeCode: boolean;
  enableEmployeeSpouse: boolean;
  enableAutoPortal: boolean;
  enableDocumentExpiry: boolean;
  enableEmployeeRequest: boolean;
};

export const HR_DEFAULTS: Record<string, HrIndustryDefaults> = {
  retail: {
    orgSize: 'medium',
    seedDepartments: ['Sales & Retail', 'Logistics', 'Human Resources', 'Finance', 'IT'],
    enableBiometricZk: true, enableSingleDeviceBinding: true, enableGeofence: true,
    enableHealthInsurance: true, enableEmployeeCode: true, enableEmployeeSpouse: true,
    enableAutoPortal: true, enableDocumentExpiry: true, enableEmployeeRequest: true,
  },
  wholesale: {
    orgSize: 'medium',
    seedDepartments: ['Sales', 'Warehouse', 'Logistics', 'Finance', 'Human Resources'],
    enableBiometricZk: true, enableSingleDeviceBinding: false, enableGeofence: true,
    enableHealthInsurance: true, enableEmployeeCode: true, enableEmployeeSpouse: true,
    enableAutoPortal: true, enableDocumentExpiry: true, enableEmployeeRequest: true,
  },
  manufacturing: {
    orgSize: 'large',
    seedDepartments: ['Production', 'Quality', 'Maintenance', 'Engineering', 'Warehouse', 'Finance', 'Human Resources'],
    enableBiometricZk: true, enableSingleDeviceBinding: false, enableGeofence: false,
    enableHealthInsurance: true, enableEmployeeCode: true, enableEmployeeSpouse: true,
    enableAutoPortal: true, enableDocumentExpiry: true, enableEmployeeRequest: true,
  },
  services: {
    orgSize: 'small',
    seedDepartments: ['Delivery', 'Operations', 'Business Development', 'Finance'],
    enableBiometricZk: false, enableSingleDeviceBinding: false, enableGeofence: false,
    enableHealthInsurance: true, enableEmployeeCode: false, enableEmployeeSpouse: false,
    enableAutoPortal: true, enableDocumentExpiry: false, enableEmployeeRequest: true,
  },
  hospitality: {
    orgSize: 'medium',
    seedDepartments: ['Floor', 'Kitchen', 'Reception', 'Housekeeping', 'Maintenance', 'Finance'],
    enableBiometricZk: true, enableSingleDeviceBinding: true, enableGeofence: true,
    enableHealthInsurance: true, enableEmployeeCode: true, enableEmployeeSpouse: false,
    enableAutoPortal: true, enableDocumentExpiry: true, enableEmployeeRequest: true,
  },
  other: {
    orgSize: 'small',
    seedDepartments: ['General'],
    enableBiometricZk: false, enableSingleDeviceBinding: false, enableGeofence: false,
    enableHealthInsurance: false, enableEmployeeCode: false, enableEmployeeSpouse: false,
    enableAutoPortal: false, enableDocumentExpiry: false, enableEmployeeRequest: false,
  },
};

export const ORG_SIZE_LABEL: Record<OrgSize, string> = {
  small: 'Small (under 50 employees)',
  medium: 'Medium (50–500 employees)',
  large: 'Large (500+ employees)',
};

export function getHrDefaults(industry?: string): HrIndustryDefaults {
  return HR_DEFAULTS[industry ?? 'other'] ?? HR_DEFAULTS.other;
}
