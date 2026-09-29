import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/common/pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { DestinationCard } from "@/components/destinations/destination-card";
import { DestinationFilters, type FilterValues } from "@/components/destinations/destination-filters";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { pageParam, param, type SearchParams } from "@/lib/search-params";
import { pageMetadata } from "@/lib/seo";
import {
  allDestinations,
  CONTINENTS,
  listDestinations,
  type Continent,
} from "@/services/destinations.service";
import type { DestinationList, Paginated } from "@/types";

const PAGE_SIZE = 12;

/** Filtres lus dans l'URL ; une valeur invalide est ignorée plutôt que de provoquer une erreur. */
function parseFilters(params: SearchParams) {
  const continent = param(params, "continent")?.toUpperCase();
  const country = param(params, "country")?.toUpperCase();
  return {
    continent: CONTINENTS.includes(continent as Continent) ? (continent as Continent) : undefined,
    country: country && /^[A-Z]{2}$/.test(country) ? country : undefined,
    search: param(params, "search")?.slice(0, 100),
    page: pageParam(params),
  };
}

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/destinations">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Destinations" });
  const filters = parseFilters(query);
  const filtered = Boolean(filters.country || filters.search || filters.page > 1);
  // Seules la liste complète et les pages par continent sont indexées.
  return pageMetadata({
    locale,
    path: filters.continent ? `/destinations?continent=${filters.continent}` : "/destinations",
    title: filters.continent ? t("metaTitleContinent", { continent: t(`continent.${filters.continent}`) }) : t("metaTitle"),
    description: t("metaDescription"),
    noindex: filtered,
  });
}

export default async function DestinationsPage({ params, searchParams }: PageProps<"/[locale]/destinations">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const t = await getTranslations("Destinations");
  const filters = parseFilters(query);

  let result: Paginated<DestinationList> | null = null;
  let all: DestinationList[] = [];
  try {
    [result, all] = await Promise.all([listDestinations(filters), allDestinations()]);
  } catch {
    // Page hors limites (404 de l'API) ou API indisponible : traités plus bas.
    all = await allDestinations().catch(() => []);
  }

  const continents = CONTINENTS.map((value) => ({ value, count: all.filter((d) => d.continent === value).length })).filter(
    (c) => c.count > 0,
  );
  const countries = [...new Map(all.map((d) => [d.country_code, { code: d.country_code, continent: d.continent }])).values()];
  const current: FilterValues = { continent: filters.continent, country: filters.country, search: filters.search };

  return (
    <>
      <PageHeader title={t("title")} description={t("intro")} breadcrumbs={[{ label: t("title") }]} />
      <Container className="flex flex-col gap-10 py-12 sm:py-16">
        {all.length > 0 && <DestinationFilters continents={continents} countries={countries} current={current} />}

        {result === null && all.length === 0 ? (
          <ErrorState title={t("errorTitle")} description={t("errorText")} />
        ) : result && result.count > 0 ? (
          <section aria-labelledby="destinations-results" className="flex flex-col gap-8">
            <h2 id="destinations-results" className="text-lg font-semibold text-ocean-900">
              {t("results", { count: result.count })}
            </h2>
            <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {result.results.map((destination, index) => (
                <li key={destination.id} className="grid">
                  <DestinationCard destination={destination} priority={index < 3} />
                </li>
              ))}
            </ul>
            <Pagination
              page={filters.page}
              count={result.count}
              pageSize={PAGE_SIZE}
              pathname="/destinations"
              query={{ continent: filters.continent, country: filters.country, search: filters.search }}
            />
          </section>
        ) : (
          <EmptyState
            title={t("emptyTitle")}
            description={t("emptyText")}
            action={
              <div className="flex flex-wrap justify-center gap-3">
                <Link href="/destinations" className={buttonVariants({ variant: "outline" })}>
                  {t("reset")}
                </Link>
                <Link href="/devis" className={buttonVariants({ variant: "cta" })}>
                  {t("customTrip")}
                </Link>
              </div>
            }
          />
        )}
      </Container>
    </>
  );
}
