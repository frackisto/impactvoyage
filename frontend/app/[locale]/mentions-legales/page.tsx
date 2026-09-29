import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";

import { LegalPage, legalMetadata } from "@/components/legal/legal-page";
import { pageMetadata } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/mentions-legales">): Promise<Metadata> {
  const { locale } = await params;
  const { title, description, path } = await legalMetadata("notice", locale);
  return pageMetadata({ locale, path, title, description });
}

export default async function LegalNoticePage({ params }: PageProps<"/[locale]/mentions-legales">) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <LegalPage document="notice" />;
}
