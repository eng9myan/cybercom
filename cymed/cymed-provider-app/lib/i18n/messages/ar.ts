// Arabic message catalog — mirrors en.ts key-for-key (enforced by
// i18n.test.ts).

const ar = {
  common: {
    loading: "جارٍ التحميل…",
    retry: "إعادة المحاولة",
    logout: "تسجيل الخروج",
    language: "اللغة",
    refresh: "تحديث",
  },
  nav: {
    overview: "نظرة عامة",
    patients: "مرضاي",
    schedule: "الجدول",
  },
  auth: {
    signInTitle: "سجّل الدخول لعرض هذا",
    signInDetail: "تظهر لوحتك هنا بعد تسجيل الدخول بحساب مزوّد الرعاية الخاص بك.",
    signIn: "تسجيل الدخول",
    continueAsDemo: "المتابعة كطبيب تجريبي",
    emailLabel: "البريد الإلكتروني",
    passwordLabel: "كلمة المرور",
    loginFailed: "فشل تسجيل الدخول",
  },
  overview: {
    title: "نظرة عامة على المزوّد",
    subtitle: "لمحة عن اليوم",
    todaysAppointments: "مواعيد اليوم",
    activePatients: "المرضى النشطون",
    pendingResults: "النتائج المعلّقة",
    telemedicineQueue: "طابور الطب عن بُعد",
    criticalAlerts: "تنبيهات حرجة",
    noAlerts: "لا توجد تنبيهات نشطة.",
    acknowledge: "إقرار",
    acknowledged: "تم الإقرار",
    noProviderLinkedTitle: "لا يوجد ملف مزوّد مرتبط",
    noProviderLinkedDetail: "هذا الحساب غير مرتبط بسجل مزوّد رعاية — تواصل مع المسؤول.",
    onCall: "في الخدمة",
    offCall: "خارج الخدمة",
    npi: "الرقم الوطني للمزوّد",
    loadFailed: "تعذّر تحميل لوحة المعلومات",
  },
  patients: {
    title: "مرضاي",
    subtitle: "المرضى الذين لديك زيارة معهم",
    searchPlaceholder: "ابحث بالاسم أو رقم الملف الطبي…",
    name: "الاسم",
    mrn: "رقم الملف الطبي",
    dob: "تاريخ الميلاد",
    gender: "الجنس",
    status: "الحالة",
    active: "نشط",
    inactive: "غير نشط",
    noResults: "لا يوجد مرضى مطابقون لبحثك.",
    empty: "لا يوجد مرضى في قائمتك بعد.",
    loadFailed: "تعذّر تحميل قائمة مرضاك",
    count: "{n} مريض",
  },
} as const;

export default ar;
