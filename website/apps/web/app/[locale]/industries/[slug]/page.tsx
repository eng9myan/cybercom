import { redirect } from "next/navigation";

interface Props {
  params: Promise<{ locale: string; slug: string }>;
}

export default async function IndustryPage({ params }: Props) {
  const { locale } = await params;
  redirect(`/${locale}/solutions`);
}

export async function generateStaticParams() {
  const slugs = [
    "healthcare", "government", "retail", "manufacturing",
    "education", "financial", "insurance", "telecom",
  ];
  return slugs.map((slug) => ({ slug }));
}
