import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";

import { LegalPage, legalMetadata } from "@/components/legal/legal-page";
import { alternates } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/confidentialite">): Promise<Metadata> {
  const { locale } = await params;
  const { title, description, path } = await legalMetadata("privacy", locale);
  return { title, description, alternates: alternates(path, locale) };
}

export default async function PrivacyPage({ params }: PageProps<"/[locale]/confidentialite">) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <LegalPage document="privacy" />;
}
