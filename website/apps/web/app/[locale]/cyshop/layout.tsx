import type { Metadata } from "next";
import { buildMetadata } from "@/lib/metadata";

interface Props {
  params: Promise<{ locale: string }>;
  children: React.ReactNode;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  return buildMetadata({
    title: "CyShop — Retail & Commerce OS",
    description:
      "CyShop is the complete retail and commerce operating system for restaurants, grocery, bakeries, coffee shops, supermarkets, and convenience stores. AI-powered POS, inventory, loyalty, and multi-location management.",
    path: "/cyshop",
    locale,
  });
}

export default function CyShopLayout({ children }: { children: React.ReactNode }) {
  return children;
}
