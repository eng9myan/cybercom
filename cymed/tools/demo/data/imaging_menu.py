"""Bookable imaging studies (radiology + nuclear + IR) with LOINC or in-house codes and JOD prices."""

from decimal import Decimal

# 40 bookable radiology / nuclear / interventional studies.
# Fields:
#   code            -- LOINC where a public LOINC exists, otherwise in-house SH-xxx.
#   name            -- Human-readable study name.
#   modality        -- DICOM modality code (CR, DX, CT, MR, US, XA, MG, NM, PT).
#   body_part       -- Body region (DICOM Body Part Examined-style).
#   contrast        -- "with", "without", "with_and_without", or "none".
#   duration_minutes-- Typical room time in minutes.
#   price           -- Cash / self-pay price in JOD (Decimal).
IMAGING_MENU = [
    # Plain radiography (CR / DX)
    {"code": "36572-2",  "name": "Chest XR PA and Lateral",              "modality": "CR", "body_part": "CHEST",       "contrast": "none",             "duration_minutes": 10, "price": Decimal("12.00")},
    {"code": "36554-0",  "name": "Chest XR AP portable",                 "modality": "CR", "body_part": "CHEST",       "contrast": "none",             "duration_minutes": 15, "price": Decimal("14.00")},
    {"code": "36849-4",  "name": "Abdomen XR AP supine",                 "modality": "CR", "body_part": "ABDOMEN",     "contrast": "none",             "duration_minutes": 10, "price": Decimal("12.00")},
    {"code": "37633-1",  "name": "Cervical spine XR 3 views",            "modality": "CR", "body_part": "CSPINE",      "contrast": "none",             "duration_minutes": 12, "price": Decimal("18.00")},
    {"code": "37634-9",  "name": "Lumbar spine XR 4 views",              "modality": "CR", "body_part": "LSPINE",      "contrast": "none",             "duration_minutes": 12, "price": Decimal("20.00")},
    {"code": "37639-8",  "name": "Knee XR 3 views",                      "modality": "DX", "body_part": "KNEE",        "contrast": "none",             "duration_minutes": 10, "price": Decimal("15.00")},
    {"code": "37637-2",  "name": "Shoulder XR 2 views",                  "modality": "DX", "body_part": "SHOULDER",    "contrast": "none",             "duration_minutes": 10, "price": Decimal("15.00")},
    {"code": "37636-4",  "name": "Wrist XR 3 views",                     "modality": "DX", "body_part": "WRIST",       "contrast": "none",             "duration_minutes": 10, "price": Decimal("14.00")},
    {"code": "37638-0",  "name": "Ankle XR 3 views",                     "modality": "DX", "body_part": "ANKLE",       "contrast": "none",             "duration_minutes": 10, "price": Decimal("14.00")},
    {"code": "37635-6",  "name": "Hip XR 2 views",                       "modality": "DX", "body_part": "HIP",         "contrast": "none",             "duration_minutes": 10, "price": Decimal("16.00")},

    # Ultrasound (US)
    {"code": "24558-9",  "name": "US Abdomen complete",                  "modality": "US", "body_part": "ABDOMEN",     "contrast": "none",             "duration_minutes": 25, "price": Decimal("35.00")},
    {"code": "24556-3",  "name": "US Pelvis (female) transabdominal",    "modality": "US", "body_part": "PELVIS",      "contrast": "none",             "duration_minutes": 25, "price": Decimal("35.00")},
    {"code": "38047-3",  "name": "US OB 2nd/3rd trimester",              "modality": "US", "body_part": "PELVIS",      "contrast": "none",             "duration_minutes": 30, "price": Decimal("45.00")},
    {"code": "24746-0",  "name": "US Thyroid",                           "modality": "US", "body_part": "NECK",        "contrast": "none",             "duration_minutes": 20, "price": Decimal("30.00")},
    {"code": "24591-0",  "name": "US Breast bilateral",                  "modality": "US", "body_part": "BREAST",      "contrast": "none",             "duration_minutes": 25, "price": Decimal("40.00")},
    {"code": "39102-5",  "name": "US Renal / Kidneys and Bladder",       "modality": "US", "body_part": "ABDOMEN",     "contrast": "none",             "duration_minutes": 25, "price": Decimal("35.00")},
    {"code": "SH-US-DVT","name": "US Doppler lower extremity venous",    "modality": "US", "body_part": "LOWEXT",      "contrast": "none",             "duration_minutes": 30, "price": Decimal("55.00")},
    {"code": "SH-US-CAR","name": "US Carotid Doppler bilateral",         "modality": "US", "body_part": "NECK",        "contrast": "none",             "duration_minutes": 25, "price": Decimal("55.00")},
    {"code": "SH-US-ECH","name": "Echocardiogram transthoracic (2D + Doppler)", "modality": "US", "body_part": "CHEST", "contrast": "none",             "duration_minutes": 35, "price": Decimal("80.00")},

    # Mammography
    {"code": "26346-7",  "name": "Mammogram bilateral screening",        "modality": "MG", "body_part": "BREAST",      "contrast": "none",             "duration_minutes": 20, "price": Decimal("45.00")},

    # CT
    {"code": "24725-4",  "name": "CT Brain without contrast",            "modality": "CT", "body_part": "HEAD",        "contrast": "without",          "duration_minutes": 15, "price": Decimal("85.00")},
    {"code": "30799-1",  "name": "CT Brain with and without contrast",   "modality": "CT", "body_part": "HEAD",        "contrast": "with_and_without", "duration_minutes": 25, "price": Decimal("140.00")},
    {"code": "24628-0",  "name": "CT Chest with contrast",               "modality": "CT", "body_part": "CHEST",       "contrast": "with",             "duration_minutes": 20, "price": Decimal("140.00")},
    {"code": "39057-1",  "name": "CT Pulmonary angiography (PE study)",  "modality": "CT", "body_part": "CHEST",       "contrast": "with",             "duration_minutes": 25, "price": Decimal("180.00")},
    {"code": "24558-9",  "name": "CT Abdomen and Pelvis with contrast",  "modality": "CT", "body_part": "ABDOMEN",     "contrast": "with",             "duration_minutes": 25, "price": Decimal("180.00")},
    {"code": "SH-CT-CAL","name": "CT Coronary calcium score",            "modality": "CT", "body_part": "CHEST",       "contrast": "none",             "duration_minutes": 15, "price": Decimal("120.00")},
    {"code": "SH-CT-CTA","name": "CT Coronary angiography (CCTA)",       "modality": "CT", "body_part": "CHEST",       "contrast": "with",             "duration_minutes": 35, "price": Decimal("280.00")},
    {"code": "24735-3",  "name": "CT Cervical spine without contrast",   "modality": "CT", "body_part": "CSPINE",      "contrast": "without",          "duration_minutes": 15, "price": Decimal("95.00")},

    # MR
    {"code": "36098-8",  "name": "MRI Brain without contrast",           "modality": "MR", "body_part": "HEAD",        "contrast": "without",          "duration_minutes": 35, "price": Decimal("180.00")},
    {"code": "36020-2",  "name": "MRI Brain with and without contrast",  "modality": "MR", "body_part": "HEAD",        "contrast": "with_and_without", "duration_minutes": 50, "price": Decimal("260.00")},
    {"code": "36097-0",  "name": "MRI Cervical spine without contrast",  "modality": "MR", "body_part": "CSPINE",      "contrast": "without",          "duration_minutes": 30, "price": Decimal("180.00")},
    {"code": "36095-4",  "name": "MRI Lumbar spine without contrast",    "modality": "MR", "body_part": "LSPINE",      "contrast": "without",          "duration_minutes": 30, "price": Decimal("180.00")},
    {"code": "36004-6",  "name": "MRI Knee without contrast",            "modality": "MR", "body_part": "KNEE",        "contrast": "without",          "duration_minutes": 30, "price": Decimal("170.00")},
    {"code": "36000-4",  "name": "MRI Shoulder without contrast",        "modality": "MR", "body_part": "SHOULDER",    "contrast": "without",          "duration_minutes": 30, "price": Decimal("170.00")},
    {"code": "SH-MR-CAR","name": "Cardiac MRI with contrast",            "modality": "MR", "body_part": "CHEST",       "contrast": "with",             "duration_minutes": 60, "price": Decimal("380.00")},

    # Nuclear medicine / PET
    {"code": "39632-1",  "name": "PET/CT whole body FDG",                "modality": "PT", "body_part": "WHOLEBODY",   "contrast": "with",             "duration_minutes": 90, "price": Decimal("620.00")},
    {"code": "39820-2",  "name": "Bone scan whole body Tc-99m",          "modality": "NM", "body_part": "WHOLEBODY",   "contrast": "with",             "duration_minutes": 90, "price": Decimal("180.00")},
    {"code": "SH-NM-MPI","name": "Myocardial perfusion SPECT stress/rest","modality": "NM","body_part": "CHEST",       "contrast": "with",             "duration_minutes": 120,"price": Decimal("320.00")},

    # Interventional / cath lab
    {"code": "SH-XA-CAG","name": "Diagnostic coronary angiography",      "modality": "XA", "body_part": "CHEST",       "contrast": "with",             "duration_minutes": 60, "price": Decimal("450.00")},
    {"code": "SH-XA-PCI","name": "PCI single-vessel with stent",         "modality": "XA", "body_part": "CHEST",       "contrast": "with",             "duration_minutes": 90, "price": Decimal("1800.00")},
]
