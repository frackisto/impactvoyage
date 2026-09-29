import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { SegmentedNav } from "@/components/common/segmented-nav";
import { Pagination } from "@/components/common/pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { dateParam, intParam, pageParam, param, type SearchParams } from "@/lib/search-params";
import { pageMetadata } from "@/lib/seo";
import {
  listTours,
  SCOPE_PATHS,
  TOUR_SORTS,
  tourFacets,
  type TourFilters as Filters,
  type TourScope,
  type TourSort,
} from "@/services/tours.service";
import type { Paginated, TourList } from "@/types";

import { TourCard } from "./tour-card";
import { CatalogLayout, ResultGrid } from "@/components/search/catalog-layout";
import { FilterPanel, type FilterField, type FilterValues } from "@/components/search/filter-panel";
import { SortSelect } from "@/components/search/sort-select";

const PAGE_SIZE = 12;
const DURATIONS = [1, 2, 3, 5, 7, 10, 15];
const SCOPE_KEY = { NATIONAL: "national", INTERNATIONAL: "international" } as const;

/** Filtres lus dans l'URL ; une valeur invalide est ignorée plutôt que de provoquer une erreur. */
function parseFilters(params: SearchParams): Filters {
  const slug = (key: string) => {
    const value = param(params, key);
    return value && /^[\w-]{1,100}$/.test(value) ? value : undefined;
  };
  const ordering = param(params, "ordering");
  return {
    destination: slug("destination"),
    theme: slug("theme"),
    departure_from: dateParam(params, "departure_from"),
    departure_to: dateParam(params, "departure_to"),
    max_days: intParam(params, "max_days", 1, 365),
    travelers: intParam(params, "travelers", 1, 99),
    max_price: intParam(params, "max_price", 0, 100_000_000),
    ordering: TOUR_SORTS.includes(ordering as TourSort) ? (ordering as TourSort) : undefined,
    page: pageParam(params),
  };
}

function asStrings(filters: Filters): FilterValues {
  const s = (value: string | number | undefined) => (value === undefined ? undefined : String(value));
  return {
    destination: filters.destination,
    theme: filters.theme,
    departure_from: filters.departure_from,
    departure_to: filters.departure_to,
    max_days: s(filters.max_days),
    travelers: s(filters.travelers),
    max_price: s(filters.max_price),
    ordering: filters.ordering === "next_departure" ? undefined : filters.ordering,
  };
}

export async function tourListMetadata(scope: TourScope, locale: string, query: SearchParams): Promise<Metadata> {
  const t = await getTranslations({ locale, namespace: "Tours" });
  const filters = parseFilters(query);
  const filtered = Object.entries(asStrings(filters)).some(([, v]) => v) || (filters.page ?? 1) > 1;
  // Seule la liste sans filtre est indexée (évite les milliers de variantes).
  return pageMetadata({
    locale,
    path: SCOPE_PATHS[scope],
    title: t(`${SCOPE_KEY[scope]}.title`),
    description: t(`${SCOPE_KEY[scope]}.metaDescription`),
    noindex: filtered,
  });
}

/** Liste des circuits nationaux ou internationaux (CdC § 9, § 10). */
export async function TourListPage({ scope, query }: { scope: TourScope; query: SearchParams }) {
  const t = await getTranslations("Tours");
  const pathname = SCOPE_PATHS[scope];
  const filters = parseFilters(query);
  const current = asStrings(filters);

  let result: Paginated<TourList> | null = null;
  let facets: Awaited<ReturnType<typeof tourFacets>> | null = null;
  try {
    [result, facets] = await Promise.all([listTours(scope, filters), tourFacets(scope)]);
  } catch {
    // Page hors limites (404 de l'API) ou API indisponible.
    facets = await tourFacets(scope).catch(() => null);
  }

  const fields: FilterField[] = [
    {
      type: "select", name: "destination", label: t("destination"), anyLabel: t("anyDestination"),
      options: (facets?.destinations ?? []).map((d) => ({ value: d.slug, label: d.name })),
    },
    {
      type: "select", name: "theme", label: t("theme"), anyLabel: t("anyTheme"),
      options: (facets?.themes ?? []).map((theme) => ({ value: theme.slug, label: theme.name })),
    },
    { type: "date", name: "departure_from", label: t("departureFrom") },
    { type: "date", name: "departure_to", label: t("departureTo") },
    {
      type: "select", name: "max_days", label: t("maxDays"), anyLabel: t("anyDuration"),
      options: DURATIONS.map((days) => ({ value: String(days), label: t("upToDays", { count: days }) })),
    },
    { type: "number", name: "travelers", label: t("travelers"), min: 1, max: 99 },
    { type: "number", name: "max_price", label: t("maxPrice"), min: 0, step: 5000 },
  ];

  const other: TourScope = scope === "NATIONAL" ? "INTERNATIONAL" : "NATIONAL";
  const quoteHref = "/devis?service=CIRCUIT";

  return (
    <>
      <PageHeader
        title={t(`${SCOPE_KEY[scope]}.title`)}
        description={t(`${SCOPE_KEY[scope]}.intro`)}
        breadcrumbs={[{ label: t(`${SCOPE_KEY[scope]}.title`) }]}
      />
      <Container className="flex flex-col gap-8 py-10 sm:py-14">
        <SegmentedNav
          label={t("scopeLabel")}
          current={pathname}
          items={(["NATIONAL", "INTERNATIONAL"] as const).map((value) => ({
            href: SCOPE_PATHS[value],
            label: t(`${SCOPE_KEY[value]}.short`),
          }))}
        />

        {facets === null && result === null ? (
          <ErrorState title={t("errorTitle")} description={t("errorText")} />
        ) : facets?.count === 0 ? (
          <EmptyState
            title={t("noneTitle")}
            description={t("noneText")}
            action={
              <div className="flex flex-wrap justify-center gap-3">
                <Link href={SCOPE_PATHS[other]} className={buttonVariants({ variant: "outline" })}>
                  {t(`${SCOPE_KEY[other]}.see`)}
                </Link>
                <Link href={quoteHref} className={buttonVariants({ variant: "cta" })}>
                  {t("customTour")}
                </Link>
              </div>
            }
          />
        ) : (
          <CatalogLayout
            heading={t("results", { count: result?.count ?? 0 })}
            filters={
              <FilterPanel
                pathname={pathname}
                fields={fields}
                current={{ ...current, ordering: undefined }}
                keep={{ ordering: current.ordering }}
                labels={{ title: t("filters"), formLabel: t("filtersLabel"), apply: t("apply"), reset: t("reset") }}
              />
            }
            sort={
              result && result.count > 1 && (
                <SortSelect
                  pathname={pathname}
                  query={current}
                  label={t("sortLabel")}
                  options={TOUR_SORTS.map((sort) => ({ value: sort, label: t(`sort.${sort}`) }))}
                />
              )
            }
          >
              {result && result.count > 0 ? (
                <>
                  <ResultGrid>
                    {result.results.map((tour, index) => (
                      <li key={tour.id} className="grid">
                        <TourCard tour={tour} priority={index < 2} />
                      </li>
                    ))}
                  </ResultGrid>
                  <Pagination page={filters.page ?? 1} count={result.count} pageSize={PAGE_SIZE} pathname={pathname} query={current} />
                </>
              ) : (
                <EmptyState
                  title={t("emptyTitle")}
                  description={t("emptyText")}
                  action={
                    <div className="flex flex-wrap justify-center gap-3">
                      <Link href={pathname} className={buttonVariants({ variant: "outline" })}>
                        {t("reset")}
                      </Link>
                      <Link href={quoteHref} className={buttonVariants({ variant: "cta" })}>
                        {t("customTour")}
                      </Link>
                    </div>
                  }
                />
              )}
          </CatalogLayout>
        )}
      </Container>
    </>
  );
}
