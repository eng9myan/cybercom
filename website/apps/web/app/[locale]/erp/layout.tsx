import type { Metadata } from "next";
import { buildMetadata } from "@/lib/metadata";

interface Props {
  params: Promise<{ locale: string }>;
  children: React.ReactNode;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  return buildMetadata({
    title: "CyCom ERP — Unified Enterprise Resource Planning",
    description:
      "CyCom ERP delivers Finance, Accounting, HR, Payroll, Procurement, Inventory, CRM, Manufacturing, and BI in one unified platform. IFRS, GAAP, WPS, ZATCA, and UAE FTA VAT compliant.",
    path: "/erp",
    locale,
  });
}

export default function ErpLayout({ children }: { children: React.ReactNode }) {
  return children;
}
