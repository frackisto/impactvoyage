import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";

import { LegalPage, legalMetadata } from "@/components/legal/legal-page";
import { pageMetadata } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/conditions-generales">): Promise<Metadata> {
  const { locale } = await params;
  const { title, description, path } = await legalMetadata("terms", locale);
  return pageMetadata({ locale, path, title, description });
}

export default async function TermsPage({ params }: PageProps<"/[locale]/conditions-generales">) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <LegalPage document="terms" />;
}
