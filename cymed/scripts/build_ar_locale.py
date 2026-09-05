"""
Build locale/ar/LC_MESSAGES/django.{po,mo} for the server-rendered portals.

The deploy/CI pipeline has no GNU gettext (`msgfmt`), so Django's
`compilemessages` can't run there — this script uses `polib` (pure Python) to
write both the source catalog and the compiled binary. Commit both outputs.

Regenerate after adding/changing a `{% trans %}` / `gettext` string:

    cd cymed && python scripts/build_ar_locale.py

`polib` is in requirements-dev.txt. The `.mo` is what Django loads at runtime.
"""
from __future__ import annotations

from pathlib import Path

import polib

OUT_DIR = Path(__file__).resolve().parent.parent / "locale" / "ar" / "LC_MESSAGES"

# msgid -> Arabic. Keep in sync with the templates + core/views/portals.py.
AR: dict[str, str] = {
    # base / brand
    "Hakeem — Next-Gen Healthcare": "حكيم — رعاية صحية من الجيل القادم",
    "Hakeem": "حكيم",
    "Hakeem Command Center": "مركز قيادة حكيم",
    "Hakeem Patient Portal": "بوابة مرضى حكيم",
    "Hakeem Patient": "مريض حكيم",
    "Hakeem Provider Portal": "بوابة مقدّمي الرعاية في حكيم",
    "Hakeem Provider": "مقدّم رعاية حكيم",
    "CyMed Patient": "مريض CyMed",
    "Loading your health…": "جارٍ تحميل بياناتك الصحية…",
    # nav
    "Dashboard": "لوحة التحكم",
    "Patient Portal": "بوابة المريض",
    "Provider Portal": "بوابة مقدّم الرعاية",
    "API Docs": "توثيق الواجهة البرمجية",
    # status
    "System Online": "النظام متصل",
    "Not signed in": "غير مسجّل الدخول",
    "Connected": "متصل",
    "On call": "في المناوبة",
    "Off call": "خارج المناوبة",
    "Live": "مباشر",
    # dashboard
    "Modules": "الوحدات",
    "Hospital": "المستشفى",
    "Clinic": "العيادة",
    "Pharmacy": "الصيدلية",
    "Laboratory": "المختبر",
    "Imaging": "الأشعة",
    "Integrations": "التكاملات",
    "ICD-11 Terminology": "مصطلحات ICD-11",
    "JoFawTra (JO)": "جوفوترة (الأردن)",
    "ZATCA (SA)": "هيئة الزكاة والضريبة (السعودية)",
    "Command Center": "مركز القيادة",
    "Real-time overview of your healthcare network": "نظرة لحظية على شبكتك الصحية",
    "Active admissions": "حالات الإدخال النشطة",
    "Occupied beds": "الأسرّة المشغولة",
    "Emergency waiting": "منتظرو الطوارئ",
    "ICU occupancy": "إشغال العناية المركزة",
    "Capacity & staffing": "السعة والملاك الوظيفي",
    "Indicator": "المؤشر",
    "Value": "القيمة",
    "Scheduled procedures today": "العمليات المجدولة اليوم",
    "Bed occupancy": "إشغال الأسرّة",
    "ICU / ventilator utilization": "استخدام العناية المركزة / أجهزة التنفس",
    "Nurse-to-patient ratio adherence": "الالتزام بنسبة الممرض إلى المريض",
    "Physician duty-hours compliance": "الالتزام بساعات عمل الأطباء",
    "Within policy": "ضمن السياسة",
    "Sign in to see live network data": "سجّل الدخول لعرض بيانات الشبكة المباشرة",
    "This command center reads live figures from your tenant's hospital, clinic, pharmacy, lab and imaging modules once you are authenticated.":
        "يعرض مركز القيادة أرقامًا مباشرة من وحدات المستشفى والعيادة والصيدلية والمختبر والأشعة الخاصة بك بعد تسجيل الدخول.",
    "Open the API console": "فتح وحدة تحكم الواجهة البرمجية",
    # patient portal
    "Sign in to your patient portal": "سجّل الدخول إلى بوابة المريض",
    "Your appointments, health records, prescriptions, NFC emergency card and bills load here once you authenticate with your Hakeem account.":
        "تظهر هنا مواعيدك وسجلاتك الصحية ووصفاتك وبطاقة الطوارئ NFC وفواتيرك بعد تسجيل الدخول بحساب حكيم.",
    "Sign in": "تسجيل الدخول",
    "MRN": "رقم السجل الطبي",
    "Overview": "نظرة عامة",
    "Appointments": "المواعيد",
    "Health Records": "السجلات الصحية",
    "Prescriptions": "الوصفات الطبية",
    "NFC Emergency Card": "بطاقة الطوارئ NFC",
    "Billing": "الفوترة",
    "Welcome back, %(name)s": "مرحبًا بعودتك، %(name)s",
    "Your health at a glance": "صحتك في لمحة",
    "Next appointment": "الموعد التالي",
    "Active prescriptions": "الوصفات النشطة",
    "Pending lab results": "نتائج المختبر المعلّقة",
    "NFC card": "بطاقة NFC",
    "Active": "نشطة",
    "Not set up": "غير مُهيّأة",
    "Instant health access for emergencies": "وصول صحي فوري في الطوارئ",
    "Paramedics can tap your NFC card or scan its QR to see your allergies, medications, conditions, blood type and emergency contacts. Manage the card from the CyMed patient mobile app or via the API.":
        "يمكن للمسعفين لمس بطاقة NFC أو مسح رمز QR لرؤية الحساسيات والأدوية والحالات وفصيلة الدم وجهات اتصال الطوارئ. تُدار البطاقة من تطبيق مرضى CyMed أو عبر الواجهة البرمجية.",
    "Manage NFC cards": "إدارة بطاقات NFC",
    "Your upcoming and past appointments. Load them from /api/v1/scheduling/.":
        "مواعيدك القادمة والسابقة. حمّلها من ‎/api/v1/scheduling/‎.",
    "Your ICD-11-coded conditions, encounters and clinical documents from /api/v1/clinical/.":
        "حالاتك المرمّزة وفق ICD-11 وزياراتك ووثائقك السريرية من ‎/api/v1/clinical/‎.",
    "Active and historical prescriptions with e-Rx tracking from /api/v1/pharmacy/.":
        "الوصفات النشطة والسابقة مع تتبّع الوصفة الإلكترونية من ‎/api/v1/pharmacy/‎.",
    "Invoices, insurance claims and payment history from /api/v1/payments/.":
        "الفواتير ومطالبات التأمين وسجل المدفوعات من ‎/api/v1/payments/‎.",
    # provider portal
    "Sign in to your provider portal": "سجّل الدخول إلى بوابة مقدّم الرعاية",
    "Your schedule, patient roster, priority alerts, orders and credentialing status load here once you authenticate with your Hakeem provider account.":
        "يظهر هنا جدولك وقائمة مرضاك والتنبيهات ذات الأولوية والطلبات وحالة الاعتماد المهني بعد تسجيل الدخول بحساب مقدّم الرعاية في حكيم.",
    "NPI": "رقم المزوّد الوطني",
    "My Patients": "مرضاي",
    "Schedule": "الجدول",
    "Orders & Results": "الطلبات والنتائج",
    "Credentialing": "الاعتماد المهني",
    "Telemedicine": "الطب عن بُعد",
    "Provider Command Center": "مركز قيادة مقدّم الرعاية",
    "Today's appointments": "مواعيد اليوم",
    "Pending results": "النتائج المعلّقة",
    "Active patients": "المرضى النشطون",
    "Telemedicine queue": "قائمة انتظار الطب عن بُعد",
    "Priority patient alerts": "تنبيهات المرضى ذات الأولوية",
    "No priority alerts right now.": "لا توجد تنبيهات ذات أولوية حاليًا.",
    "Credentialing status": "حالة الاعتماد المهني",
    "Verify and track your professional credentials": "تحقّق من مؤهلاتك المهنية وتابعها",
    "No credentialing records yet. Add them via the API or your admin.":
        "لا توجد سجلات اعتماد بعد. أضِفها عبر الواجهة البرمجية أو المسؤول.",
    "Open credentialing API": "فتح واجهة الاعتماد البرمجية",
    "Your patient roster with active conditions and care plans from /api/v1/clinical/.":
        "قائمة مرضاك مع الحالات النشطة وخطط الرعاية من ‎/api/v1/clinical/‎.",
    "Calendar and availability from /api/v1/scheduling/.":
        "التقويم والإتاحة من ‎/api/v1/scheduling/‎.",
    "Lab, imaging and pharmacy orders with results from /api/v1/lab/, /api/v1/imaging/, /api/v1/pharmacy/.":
        "طلبات المختبر والأشعة والصيدلية مع النتائج من ‎/api/v1/lab/‎ و‎/api/v1/imaging/‎ و‎/api/v1/pharmacy/‎.",
    "Virtual consultations from /api/v1/clinic/telemedicine/.":
        "الاستشارات الافتراضية من ‎/api/v1/clinic/telemedicine/‎.",
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    po = polib.POFile()
    po.metadata = {
        "Project-Id-Version": "cymed-portals 1.0",
        "Report-Msgid-Bugs-To": "",
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
        "Language": "ar",
        "Plural-Forms": "nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : "
        "n%100>=3 && n%100<=10 ? 3 : n%100>=11 ? 4 : 5);",
    }
    for msgid, msgstr in AR.items():
        po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))

    po.save(str(OUT_DIR / "django.po"))
    po.save_as_mofile(str(OUT_DIR / "django.mo"))
    print(f"wrote {len(AR)} entries to {OUT_DIR}/django.{{po,mo}}")


if __name__ == "__main__":
    main()
