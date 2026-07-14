import type { Metadata } from "next";
import { buildMetadata } from "@/lib/metadata";

interface Props {
  params: Promise<{ locale: string }>;
  children: React.ReactNode;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  return buildMetadata({
    title: "Contact",
    description:
      "Get in touch with the CyberCom team. Sales inquiries, technical support, partnerships, and media requests — we're here to help.",
    path: "/contact",
    locale,
  });
}

export default function ContactLayout({ children }: { children: React.ReactNode }) {
  return children;
}
