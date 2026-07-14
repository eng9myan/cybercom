import type { Metadata } from "next";
import { buildMetadata } from "@/lib/metadata";

interface Props {
  params: Promise<{ locale: string }>;
  children: React.ReactNode;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  return buildMetadata({
    title: "CyMed — Intelligent Healthcare Platform",
    description:
      "CyMed is a FHIR-native clinical platform for hospitals, clinics, laboratories, pharmacies, and imaging centers. ICD-11 and SNOMED CT coded, with CyAI advisory-only clinical decision support.",
    path: "/cymed",
    locale,
  });
}

export default function CyMedLayout({ children }: { children: React.ReactNode }) {
  return children;
}
