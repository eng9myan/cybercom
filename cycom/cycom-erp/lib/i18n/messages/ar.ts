// Arabic (العربية) message catalog. Mirrors en.ts exactly.
// ERP terminology reviewed for correctness (accounting/POS/tax terms are not
// safely machine-translatable — see RTL_AUDIT.md item 3). Professional review
// still recommended before an Arabic-market GA.

import type { Messages } from "./en";

const ar: Messages = {
  common: {
    save: "حفظ",
    cancel: "إلغاء",
    delete: "حذف",
    edit: "تعديل",
    add: "إضافة",
    search: "بحث",
    loading: "جارٍ التحميل…",
    total: "الإجمالي",
    subtotal: "المجموع الفرعي",
    tax: "ضريبة القيمة المضافة",
    discount: "الخصم",
    quantity: "الكمية",
    price: "السعر",
    date: "التاريخ",
    status: "الحالة",
    actions: "إجراءات",
    language: "اللغة",
    yes: "نعم",
    no: "لا",
  },
  pos: {
    title: "نقطة البيع",
    newSale: "عملية بيع جديدة",
    openSession: "فتح الجلسة",
    closeSession: "إغلاق الجلسة",
    cart: "السلة",
    checkout: "إتمام الدفع",
    pay: "دفع",
    cash: "نقداً",
    card: "بطاقة",
    wallet: "محفظة",
    change: "الباقي المستحق",
    ring: "تسجيل البيع",
    emptyCart: "السلة فارغة",
    paid: "مدفوع",
    receiptPrinted: "تمت طباعة الإيصال",
    kitchen: "شاشة المطبخ",
    bump: "تم التحضير",
    ready: "جاهز",
    preparing: "قيد التحضير",
  },
  receipt: {
    heading: "فاتورة ضريبية",
    simplified: "فاتورة ضريبية مبسطة",
    invoiceNo: "رقم الفاتورة",
    seller: "البائع",
    buyer: "المشتري",
    vatNo: "الرقم الضريبي",
    thankYou: "شكراً لتعاملكم معنا",
    scanToVerify: "امسح للتحقق",
  },
};

export default ar;
