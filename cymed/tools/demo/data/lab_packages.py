"""Bundled lab packages (checkups + condition-specific profiles) priced in JOD."""

from decimal import Decimal

# 15 bundles. Each bundle references LOINC codes from lab_menu.LAB_MENU.
# Fields:
#   code           -- Internal bundle code.
#   name           -- Display name.
#   description    -- One-line clinical purpose.
#   components     -- List of LOINC / in-house codes included.
#   bundle_price   -- Discounted package price in JOD (Decimal).
LAB_PACKAGES = [
    {
        "code": "PKG-BMP",
        "name": "Basic Metabolic Panel",
        "description": "Kidney function, glucose, and core electrolytes.",
        "components": ["2345-7", "2951-2", "2823-3", "2075-0", "2028-9", "3094-0", "2160-0", "17861-6"],
        "bundle_price": Decimal("22.00"),
    },
    {
        "code": "PKG-CMP",
        "name": "Comprehensive Metabolic Panel",
        "description": "BMP plus liver enzymes and proteins.",
        "components": ["2345-7", "2951-2", "2823-3", "2075-0", "2028-9", "3094-0", "2160-0", "17861-6",
                       "1742-6", "1920-8", "6768-6", "1975-2", "1751-7", "2885-2"],
        "bundle_price": Decimal("32.00"),
    },
    {
        "code": "PKG-LIPID",
        "name": "Lipid Profile",
        "description": "Total cholesterol, triglycerides, HDL, calculated LDL.",
        "components": ["2093-3", "2571-8", "2085-9", "13457-7"],
        "bundle_price": Decimal("14.00"),
    },
    {
        "code": "PKG-LFT",
        "name": "Liver Function Tests",
        "description": "Enzymes, bilirubin, and proteins for hepatic screening.",
        "components": ["1742-6", "1920-8", "6768-6", "2324-2", "1975-2", "1968-7", "1751-7", "2885-2"],
        "bundle_price": Decimal("22.00"),
    },
    {
        "code": "PKG-RFT",
        "name": "Renal Function Tests",
        "description": "Kidney workup: BUN, creatinine, electrolytes, uric acid.",
        "components": ["3094-0", "2160-0", "2951-2", "2823-3", "2075-0", "3016-3"],
        "bundle_price": Decimal("18.00"),
    },
    {
        "code": "PKG-THY",
        "name": "Thyroid Profile",
        "description": "TSH, Free T4, Free T3.",
        "components": ["3016-3", "3053-6", "3051-0"],
        "bundle_price": Decimal("34.00"),
    },
    {
        "code": "PKG-DM",
        "name": "Diabetes Follow-up",
        "description": "Glycemic control, kidney and lipid surveillance for DM patients.",
        "components": ["4548-4", "2345-7", "2160-0", "5804-0", "2093-3", "2571-8", "2085-9", "13457-7"],
        "bundle_price": Decimal("38.00"),
    },
    {
        "code": "PKG-HTN",
        "name": "Hypertension Workup",
        "description": "Electrolytes, kidney, lipid, and cardiac markers.",
        "components": ["2951-2", "2823-3", "3094-0", "2160-0", "2093-3", "2571-8", "5804-0"],
        "bundle_price": Decimal("30.00"),
    },
    {
        "code": "PKG-CARD",
        "name": "Cardiac Panel (ED chest pain)",
        "description": "Rule-out ACS with troponins, CK-MB, NT-proBNP, D-dimer.",
        "components": ["10839-9", "13969-1", "33762-6", "48065-7"],
        "bundle_price": Decimal("78.00"),
    },
    {
        "code": "PKG-COAG",
        "name": "Coagulation Screen",
        "description": "PT/INR, aPTT, fibrinogen.",
        "components": ["5902-2", "14979-9", "3255-7"],
        "bundle_price": Decimal("18.00"),
    },
    {
        "code": "PKG-ANEMIA",
        "name": "Anemia Workup",
        "description": "CBC, reticulocyte count, iron studies, B12, folate proxies.",
        "components": ["58410-2", "718-7", "2276-4", "2132-9"],
        "bundle_price": Decimal("34.00"),
    },
    {
        "code": "PKG-PRENATAL",
        "name": "Prenatal Panel",
        "description": "Booking bloods for the first antenatal visit.",
        "components": ["58410-2", "883-9", "5199-5", "13955-0", "5017-9", "5804-0", "10334-1"],
        "bundle_price": Decimal("58.00"),
    },
    {
        "code": "PKG-INFECT",
        "name": "Infection Screen",
        "description": "CBC, CRP, ESR, urinalysis, blood culture.",
        "components": ["58410-2", "11580-8", "4537-7", "5804-0", "600-7"],
        "bundle_price": Decimal("42.00"),
    },
    {
        "code": "PKG-EXEC-M",
        "name": "Executive Checkup - Male",
        "description": "Annual wellness workup including PSA and cardiac risk markers.",
        "components": ["58410-2", "4548-4", "2093-3", "2571-8", "2085-9", "13457-7",
                       "1742-6", "1920-8", "3016-3", "3053-6", "10886-0", "5804-0"],
        "bundle_price": Decimal("95.00"),
    },
    {
        "code": "PKG-EXEC-F",
        "name": "Executive Checkup - Female",
        "description": "Annual wellness workup including thyroid and iron studies.",
        "components": ["58410-2", "4548-4", "2093-3", "2571-8", "2085-9", "13457-7",
                       "1742-6", "1920-8", "3016-3", "3053-6", "2276-4", "5804-0"],
        "bundle_price": Decimal("95.00"),
    },
]
