// English message catalog. Keep keys stable; `ar.ts` mirrors this shape.
// Namespaced by surface: common.*, pos.*, receipt.*. Extend as screens are
// wrapped in t() — see RTL_AUDIT.md for the full plan.

const en = {
  common: {
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    edit: "Edit",
    add: "Add",
    search: "Search",
    loading: "Loading…",
    total: "Total",
    subtotal: "Subtotal",
    tax: "VAT",
    discount: "Discount",
    quantity: "Qty",
    price: "Price",
    date: "Date",
    status: "Status",
    actions: "Actions",
    language: "Language",
    yes: "Yes",
    no: "No",
  },
  pos: {
    title: "Point of Sale",
    newSale: "New Sale",
    openSession: "Open Session",
    closeSession: "Close Session",
    cart: "Cart",
    checkout: "Checkout",
    pay: "Pay",
    cash: "Cash",
    card: "Card",
    wallet: "Wallet",
    change: "Change due",
    ring: "Ring sale",
    emptyCart: "Cart is empty",
    paid: "Paid",
    receiptPrinted: "Receipt printed",
    kitchen: "Kitchen Display",
    bump: "Bump",
    ready: "Ready",
    preparing: "Preparing",
  },
  receipt: {
    heading: "Tax Invoice",
    simplified: "Simplified Tax Invoice",
    invoiceNo: "Invoice No.",
    seller: "Seller",
    buyer: "Buyer",
    vatNo: "VAT No.",
    thankYou: "Thank you for your business",
    scanToVerify: "Scan to verify",
  },
} as const;

export default en;

// The catalog shape with values widened to `string`, so ar.ts (and any future
// locale) can supply its own translations while keeping the exact key structure.
type Widen<T> = { [K in keyof T]: T[K] extends string ? string : Widen<T[K]> };
export type Messages = Widen<typeof en>;
