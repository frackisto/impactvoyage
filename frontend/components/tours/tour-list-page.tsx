import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/common/pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { dateParam, intParam, pageParam, param, type SearchParams } from "@/lib/search-params";
import { alternates } from "@/lib/seo";
import { cn } from "@/lib/utils";
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
import { TourFilters, type TourFilterValues } from "./tour-filters";
import { TourSort as SortSelect } from "./tour-sort";

const PAGE_SIZE = 12;
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

function asStrings(filters: Filters): TourFilterValues {
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
  return {
    title: t(`${SCOPE_KEY[scope]}.title`),
    description: t(`${SCOPE_KEY[scope]}.metaDescription`),
    alternates: alternates(SCOPE_PATHS[scope], locale),
    // Seule la liste sans filtre est indexée (évite les milliers de variantes).
    robots: filtered ? { index: false, follow: true } : undefined,
  };
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
        <nav aria-label={t("scopeLabel")}>
          <ul className="inline-flex rounded-full border bg-ocean-50 p-1">
            {(["NATIONAL", "INTERNATIONAL"] as const).map((value) => (
              <li key={value}>
                <Link
                  href={SCOPE_PATHS[value]}
                  aria-current={value === scope ? "page" : undefined}
                  className={cn(
                    "inline-flex h-10 items-center rounded-full px-5 text-sm font-semibold transition-colors",
                    value === scope ? "bg-ocean-600 text-white" : "text-ocean-900 hover:bg-white",
                  )}
                >
                  {t(`${SCOPE_KEY[value]}.short`)}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

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
          <div className="grid gap-8 lg:grid-cols-[18rem_minmax(0,1fr)]">
            <aside className="lg:sticky lg:top-24 lg:self-start">
              <TourFilters
                pathname={pathname}
                destinations={facets?.destinations ?? []}
                themes={facets?.themes ?? []}
                current={current}
              />
            </aside>

            <section aria-labelledby="tours-results" className="flex flex-col gap-6">
              <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                <h2 id="tours-results" className="text-lg font-semibold text-ocean-900">
                  {t("results", { count: result?.count ?? 0 })}
                </h2>
                {result && result.count > 1 && <SortSelect pathname={pathname} query={current} />}
              </div>

              {result && result.count > 0 ? (
                <>
                  <ul className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                    {result.results.map((tour, index) => (
                      <li key={tour.id} className="grid">
                        <TourCard tour={tour} priority={index < 2} />
                      </li>
                    ))}
                  </ul>
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
            </section>
          </div>
        )}
      </Container>
    </>
  );
}
