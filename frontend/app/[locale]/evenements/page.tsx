import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/common/pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { EventCard } from "@/components/events/event-card";
import { CatalogLayout, ResultGrid } from "@/components/search/catalog-layout";
import { FilterPanel, type FilterField } from "@/components/search/filter-panel";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { intParam, pageParam, param, type SearchParams } from "@/lib/search-params";
import { pageMetadata } from "@/lib/seo";
import { EVENT_CATEGORIES, eventFacets, listEvents, type EventFilters } from "@/services/events.service";
import type { EventList, Paginated } from "@/types";

const PATH = "/evenements";
const PAGE_SIZE = 12;

function parseFilters(params: SearchParams): EventFilters {
  const category = param(params, "category");
  return {
    category: EVENT_CATEGORIES.includes(category as (typeof EVENT_CATEGORIES)[number]) ? category : undefined,
    year: intParam(params, "year", 2000, 2100),
    page: pageParam(params),
  };
}

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/evenements">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Events" });
  const filters = parseFilters(query);
  const filtered = Boolean(filters.category || filters.year || (filters.page ?? 1) > 1);
  return pageMetadata({ locale, path: PATH, title: t("title"), description: t("metaDescription"), noindex: filtered });
}

/** Événementiel : voyages de groupe, sorties et événements réalisés par l'agence (CdC § 15). */
export default async function EventsPage({ params, searchParams }: PageProps<"/[locale]/evenements">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const t = await getTranslations("Events");
  const filters = parseFilters(query);
  const current = { category: filters.category, year: filters.year ? String(filters.year) : undefined };

  let result: Paginated<EventList> | null = null;
  let facets: Awaited<ReturnType<typeof eventFacets>> | null = null;
  try {
    [result, facets] = await Promise.all([listEvents(filters), eventFacets()]);
  } catch {
    facets = await eventFacets().catch(() => null);
  }
  const quoteHref = "/devis?service=EVENEMENT";

  const fields: FilterField[] = [
    {
      type: "select", name: "category", label: t("categoryLabel"), anyLabel: t("anyCategory"),
      options: (facets?.categories ?? []).map((c) => ({ value: c, label: t(`category.${c}`) })),
    },
    {
      type: "select", name: "year", label: t("year"), anyLabel: t("anyYear"),
      options: (facets?.years ?? []).map((year) => ({ value: String(year), label: String(year) })),
    },
  ];

  return (
    <>
      <PageHeader title={t("title")} description={t("intro")} breadcrumbs={[{ label: t("title") }]} />
      <Container className="flex flex-col gap-8 py-10 sm:py-14">
        {facets === null && result === null ? (
          <ErrorState title={t("errorTitle")} description={t("errorText")} />
        ) : (
          <CatalogLayout
            heading={t("results", { count: result?.count ?? 0 })}
            filters={
              <div className="flex flex-col gap-4">
                <FilterPanel
                  pathname={PATH}
                  fields={fields}
                  current={current}
                  labels={{ title: t("filters"), formLabel: t("filtersLabel"), apply: t("apply"), reset: t("reset") }}
                />
                <div className="flex flex-col gap-3 rounded-2xl bg-ocean-900 p-5 text-white">
                  <p className="font-heading text-lg font-bold">{t("organizeTitle")}</p>
                  <p className="text-sm text-ocean-100">{t("organizeText")}</p>
                  <Link href={quoteHref} className={buttonVariants({ variant: "cta" })}>
                    {t("organizeCta")}
                  </Link>
                </div>
              </div>
            }
          >
            {result && result.count > 0 ? (
              <>
                <ResultGrid>
                  {result.results.map((event, index) => (
                    <li key={event.id} className="grid">
                      <EventCard event={event} priority={index < 2} />
                    </li>
                  ))}
                </ResultGrid>
                <Pagination page={filters.page ?? 1} count={result.count} pageSize={PAGE_SIZE} pathname={PATH} query={current} />
              </>
            ) : (
              <EmptyState
                title={t("emptyTitle")}
                description={t("emptyText")}
                action={
                  <Link href={PATH} className={buttonVariants({ variant: "outline" })}>
                    {t("reset")}
                  </Link>
                }
              />
            )}
          </CatalogLayout>
        )}
      </Container>
    </>
  );
}
