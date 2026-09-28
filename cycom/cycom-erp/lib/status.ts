/**
 * Canonical order/claim status keys, shared by the sales / purchase / expenses
 * list screens. Pages map their backend `state` string to one of these keys,
 * then render the label via `t('status.' + key)` and the badge colour via
 * `statusTone(key)` — so the visual logic never depends on a localized string.
 */
export type StatusKey =
  | "draft"
  | "pendingApproval"
  | "waitingApproval"
  | "confirmed"
  | "done"
  | "cancelled"
  | "sent"
  | "rfqSent"
  | "submitted"
  | "approved"
  | "reimbursed"
  | "declined"
  | "waiting"
  | "ready"
  | "completed"
  | "delivered"
  | "invoiced"
  | "rejected"
  | "partiallyReceived"
  | "unknown";

const GREEN: StatusKey[] = ["confirmed", "done", "approved", "reimbursed", "completed", "delivered", "invoiced"];
const RED: StatusKey[] = ["cancelled", "declined", "rejected"];
const YELLOW: StatusKey[] = [
  "draft",
  "pendingApproval",
  "waitingApproval",
  "sent",
  "rfqSent",
  "submitted",
  "waiting",
  "partiallyReceived",
];

/** Tailwind badge class for a status key (matches the design-system badges). */
export function statusTone(key: StatusKey): string {
  if (GREEN.includes(key)) return "badge-green";
  if (RED.includes(key)) return "badge-red";
  if (YELLOW.includes(key)) return "badge-yellow";
  return "badge-cyan";
}

export const SALES_STATE: Record<string, StatusKey> = {
  draft: "draft",
  sent: "pendingApproval",
  sale: "confirmed",
  done: "done",
  cancel: "cancelled",
};

export const PURCHASE_STATE: Record<string, StatusKey> = {
  draft: "draft",
  sent: "rfqSent",
  to_approve: "waitingApproval",
  purchase: "confirmed",
  done: "done",
  cancel: "cancelled",
};

export const EXPENSE_STATE: Record<string, StatusKey> = {
  draft: "submitted",
  reported: "submitted",
  approved: "approved",
  done: "reimbursed",
  cancel: "declined",
  refused: "declined",
};

export const TRANSFER_STATE: Record<string, StatusKey> = {
  draft: "draft",
  waiting: "waiting",
  confirmed: "confirmed",
  assigned: "ready",
  done: "completed",
  cancel: "cancelled",
};

// The two maps below are for pages reading the *real* backend REST
// endpoints directly (products.cycom.sales / products.cycom.procurement),
// not the legacy Odoo-shaped RPC shim -- their status vocab is different
// from SALES_STATE / PURCHASE_STATE above, which map Odoo's state strings.
export const REAL_SALES_ORDER_STATE: Record<string, StatusKey> = {
  draft: "draft",
  confirmed: "confirmed",
  delivered: "delivered",
  invoiced: "invoiced",
  cancelled: "cancelled",
};

export const REAL_PURCHASE_ORDER_STATE: Record<string, StatusKey> = {
  draft: "draft",
  approved: "approved",
  rejected: "rejected",
  received: "completed",
  partially_received: "partiallyReceived",
};
