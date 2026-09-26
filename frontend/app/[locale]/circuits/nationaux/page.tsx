import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";

import { TourListPage, tourListMetadata } from "@/components/tours/tour-list-page";

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/circuits/nationaux">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  return tourListMetadata("NATIONAL", locale, query);
}

export default async function Page({ params, searchParams }: PageProps<"/[locale]/circuits/nationaux">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  return <TourListPage scope="NATIONAL" query={query} />;
}
