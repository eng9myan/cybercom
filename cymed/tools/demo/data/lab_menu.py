"""Bookable laboratory tests with LOINC codes (where public) and JOD retail prices."""

from decimal import Decimal

# 60 individual laboratory tests.
# Fields:
#   code       -- LOINC code where publicly known, otherwise in-house SH-LAB-xxx.
#   name       -- Human-readable test name.
#   specimen   -- serum, plasma, whole_blood, urine, stool, csf, swab, sputum.
#   department -- chemistry, hematology, coagulation, immunology, endocrinology,
#                 microbiology, urinalysis, molecular, toxicology, blood_bank.
#   turnaround_hours -- Routine TAT in hours (int).
#   price      -- Cash / self-pay price in JOD (Decimal).
LAB_MENU = [
    # Hematology
    {"code": "58410-2", "name": "Complete Blood Count (CBC) with differential", "specimen": "whole_blood", "department": "hematology", "turnaround_hours": 2, "price": Decimal("6.00")},
    {"code": "789-8",   "name": "Erythrocyte count",                              "specimen": "whole_blood", "department": "hematology", "turnaround_hours": 2, "price": Decimal("3.50")},
    {"code": "718-7",   "name": "Hemoglobin",                                     "specimen": "whole_blood", "department": "hematology", "turnaround_hours": 2, "price": Decimal("3.00")},
    {"code": "4544-3",  "name": "Hematocrit",                                     "specimen": "whole_blood", "department": "hematology", "turnaround_hours": 2, "price": Decimal("3.00")},
    {"code": "777-3",   "name": "Platelet count",                                 "specimen": "whole_blood", "department": "hematology", "turnaround_hours": 2, "price": Decimal("3.50")},
    {"code": "6690-2",  "name": "Leukocyte count",                                "specimen": "whole_blood", "department": "hematology", "turnaround_hours": 2, "price": Decimal("3.50")},
    {"code": "4537-7",  "name": "ESR (Westergren)",                               "specimen": "whole_blood", "department": "hematology", "turnaround_hours": 4, "price": Decimal("4.20")},
    {"code": "4548-4",  "name": "HbA1c",                                          "specimen": "whole_blood", "department": "chemistry",  "turnaround_hours": 4, "price": Decimal("12.00")},
    {"code": "718-7",   "name": "Reticulocyte count",                             "specimen": "whole_blood", "department": "hematology", "turnaround_hours": 6, "price": Decimal("9.00")},

    # Coagulation
    {"code": "5902-2",  "name": "Prothrombin Time (PT/INR)",                      "specimen": "plasma",      "department": "coagulation","turnaround_hours": 3, "price": Decimal("6.50")},
    {"code": "14979-9", "name": "aPTT",                                           "specimen": "plasma",      "department": "coagulation","turnaround_hours": 3, "price": Decimal("6.50")},
    {"code": "3255-7",  "name": "Fibrinogen",                                     "specimen": "plasma",      "department": "coagulation","turnaround_hours": 4, "price": Decimal("10.00")},
    {"code": "48065-7", "name": "D-dimer",                                        "specimen": "plasma",      "department": "coagulation","turnaround_hours": 3, "price": Decimal("18.00")},

    # Chemistry - basic metabolic
    {"code": "2345-7",  "name": "Glucose (fasting)",                              "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.20")},
    {"code": "2951-2",  "name": "Sodium",                                         "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.20")},
    {"code": "2823-3",  "name": "Potassium",                                      "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.20")},
    {"code": "2075-0",  "name": "Chloride",                                       "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.20")},
    {"code": "2028-9",  "name": "Bicarbonate (CO2)",                              "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.20")},
    {"code": "3094-0",  "name": "Blood Urea Nitrogen (BUN)",                      "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.60")},
    {"code": "2160-0",  "name": "Creatinine",                                     "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.60")},
    {"code": "17861-6", "name": "Calcium",                                        "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.80")},
    {"code": "2777-1",  "name": "Phosphorus",                                     "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.80")},
    {"code": "19123-9", "name": "Magnesium",                                      "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("4.20")},
    {"code": "3016-3",  "name": "Uric acid",                                      "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("4.00")},

    # Chemistry - liver
    {"code": "1742-6",  "name": "ALT (SGPT)",                                     "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.80")},
    {"code": "1920-8",  "name": "AST (SGOT)",                                     "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.80")},
    {"code": "6768-6",  "name": "Alkaline phosphatase",                           "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("4.20")},
    {"code": "2324-2",  "name": "GGT",                                            "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("4.60")},
    {"code": "1975-2",  "name": "Bilirubin total",                                "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.80")},
    {"code": "1968-7",  "name": "Bilirubin direct",                               "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.80")},
    {"code": "1751-7",  "name": "Albumin",                                        "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.60")},
    {"code": "2885-2",  "name": "Total protein",                                  "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("3.60")},
    {"code": "1798-8",  "name": "Amylase",                                        "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 3, "price": Decimal("6.20")},
    {"code": "3040-3",  "name": "Lipase",                                         "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 3, "price": Decimal("7.40")},

    # Chemistry - lipids
    {"code": "2093-3",  "name": "Cholesterol total",                              "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("4.20")},
    {"code": "2571-8",  "name": "Triglycerides",                                  "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("4.20")},
    {"code": "2085-9",  "name": "HDL cholesterol",                                "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("4.20")},
    {"code": "13457-7", "name": "LDL cholesterol (calculated)",                   "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("4.20")},

    # Cardiac markers
    {"code": "10839-9", "name": "Troponin I (hs)",                                "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 1, "price": Decimal("22.00")},
    {"code": "6598-7",  "name": "Troponin T (hs)",                                "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 1, "price": Decimal("22.00")},
    {"code": "33762-6", "name": "NT-proBNP",                                      "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("34.00")},
    {"code": "13969-1", "name": "Creatine Kinase MB",                             "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 2, "price": Decimal("12.00")},

    # Endocrinology
    {"code": "3016-3",  "name": "TSH",                                            "specimen": "serum",       "department": "endocrinology","turnaround_hours": 4, "price": Decimal("14.00")},
    {"code": "3053-6",  "name": "Free T4",                                        "specimen": "serum",       "department": "endocrinology","turnaround_hours": 4, "price": Decimal("14.00")},
    {"code": "3051-0",  "name": "Free T3",                                        "specimen": "serum",       "department": "endocrinology","turnaround_hours": 4, "price": Decimal("14.00")},
    {"code": "1986-9",  "name": "Cortisol AM",                                    "specimen": "serum",       "department": "endocrinology","turnaround_hours": 6, "price": Decimal("18.00")},
    {"code": "1968-7",  "name": "Vitamin D 25-OH",                                "specimen": "serum",       "department": "endocrinology","turnaround_hours": 8, "price": Decimal("28.00")},
    {"code": "2132-9",  "name": "Vitamin B12",                                    "specimen": "serum",       "department": "endocrinology","turnaround_hours": 8, "price": Decimal("22.00")},
    {"code": "2276-4",  "name": "Ferritin",                                       "specimen": "serum",       "department": "chemistry",  "turnaround_hours": 6, "price": Decimal("18.00")},
    {"code": "10334-1", "name": "Insulin",                                        "specimen": "serum",       "department": "endocrinology","turnaround_hours": 6, "price": Decimal("20.00")},

    # Serology / Immunology / Tumor markers
    {"code": "11580-8", "name": "CRP quantitative",                               "specimen": "serum",       "department": "immunology", "turnaround_hours": 2, "price": Decimal("8.00")},
    {"code": "5199-5",  "name": "HBsAg screen",                                   "specimen": "serum",       "department": "immunology", "turnaround_hours": 6, "price": Decimal("14.00")},
    {"code": "13955-0", "name": "HCV antibody screen",                            "specimen": "serum",       "department": "immunology", "turnaround_hours": 6, "price": Decimal("14.00")},
    {"code": "5017-9",  "name": "HIV 1+2 antibody/antigen screen",                "specimen": "serum",       "department": "immunology", "turnaround_hours": 6, "price": Decimal("18.00")},
    {"code": "10334-1", "name": "Beta-hCG quantitative",                          "specimen": "serum",       "department": "immunology", "turnaround_hours": 4, "price": Decimal("16.00")},
    {"code": "10886-0", "name": "PSA total",                                      "specimen": "serum",       "department": "immunology", "turnaround_hours": 6, "price": Decimal("24.00")},

    # Urinalysis / microbiology
    {"code": "5804-0",  "name": "Urinalysis complete (macro + micro + dipstick)", "specimen": "urine",       "department": "urinalysis", "turnaround_hours": 2, "price": Decimal("5.00")},
    {"code": "630-4",   "name": "Urine culture and sensitivity",                  "specimen": "urine",       "department": "microbiology","turnaround_hours": 48,"price": Decimal("15.00")},
    {"code": "600-7",   "name": "Blood culture (aerobic + anaerobic set)",        "specimen": "whole_blood", "department": "microbiology","turnaround_hours": 72,"price": Decimal("28.00")},
    {"code": "6463-4",  "name": "Stool culture",                                  "specimen": "stool",       "department": "microbiology","turnaround_hours": 48,"price": Decimal("14.00")},

    # Molecular
    {"code": "94500-6", "name": "SARS-CoV-2 RT-PCR",                              "specimen": "swab",        "department": "molecular",  "turnaround_hours": 12,"price": Decimal("35.00")},

    # Blood bank
    {"code": "883-9",   "name": "ABO group and Rh typing",                        "specimen": "whole_blood", "department": "blood_bank", "turnaround_hours": 2, "price": Decimal("8.00")},
]
