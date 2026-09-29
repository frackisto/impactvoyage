import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { ActivityCard } from "@/components/activities/activity-card";
import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/common/pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { CatalogLayout, ResultGrid } from "@/components/search/catalog-layout";
import { FilterPanel, type FilterField, type FilterValues } from "@/components/search/filter-panel";
import { SortSelect } from "@/components/search/sort-select";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { dateParam, intParam, pageParam, param, type SearchParams } from "@/lib/search-params";
import { pageMetadata } from "@/lib/seo";
import { ACTIVITY_SORTS, activityFacets, listActivities, type ActivityFilters } from "@/services/activities.service";
import type { ActivityList, Paginated } from "@/types";

const PATH = "/activites";
const PAGE_SIZE = 12;
const DURATIONS = [2, 3, 4, 6, 8];

/** Filtres lus dans l'URL (noms de l'API et du moteur de recherche) ; valeurs invalides ignorées. */
function parseFilters(params: SearchParams): ActivityFilters {
  const slug = (key: string) => {
    const value = param(params, key);
    return value && /^[\w-]{1,100}$/.test(value) ? value : undefined;
  };
  const ordering = param(params, "ordering");
  const date = dateParam(params, "date");
  return {
    destination: slug("destination"),
    category: slug("category"),
    date,
    participants: date ? intParam(params, "participants", 1, 50) : undefined,
    max_hours: intParam(params, "max_hours", 1, 72),
    max_price: intParam(params, "max_price", 0, 100_000_000),
    ordering: ACTIVITY_SORTS.includes(ordering as (typeof ACTIVITY_SORTS)[number]) ? ordering : undefined,
    page: pageParam(params),
  };
}

function asStrings(filters: ActivityFilters): FilterValues {
  return Object.fromEntries(
    Object.entries(filters)
      .filter(([key]) => key !== "page")
      .map(([key, value]) => [key, value === undefined ? undefined : String(value)]),
  );
}

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/activites">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Activities" });
  const filters = parseFilters(query);
  const filtered = Object.values(asStrings(filters)).some(Boolean) || (filters.page ?? 1) > 1;
  return pageMetadata({ locale, path: PATH, title: t("title"), description: t("metaDescription"), noindex: filtered });
}

/** Activités et excursions (CdC § 7). */
export default async function ActivitiesPage({ params, searchParams }: PageProps<"/[locale]/activites">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const t = await getTranslations("Activities");
  const filters = parseFilters(query);
  const current = asStrings(filters);

  let result: Paginated<ActivityList> | null = null;
  let facets: Awaited<ReturnType<typeof activityFacets>> | null = null;
  try {
    [result, facets] = await Promise.all([listActivities(filters), activityFacets()]);
  } catch {
    // Page hors limites (404 de l'API) ou API indisponible.
    facets = await activityFacets().catch(() => null);
  }

  // La fiche reprend la date et le nombre de participants.
  const carried = { date: filters.date, participants: current.participants };
  const quoteHref = "/devis?service=ACTIVITES";

  const fields: FilterField[] = [
    {
      type: "select", name: "destination", label: t("destination"), anyLabel: t("anyDestination"),
      options: (facets?.destinations ?? []).map((d) => ({ value: d.slug, label: d.name })),
    },
    { type: "date", name: "date", label: t("date") },
    { type: "number", name: "participants", label: t("participantsLabel"), min: 1, max: 50 },
    {
      type: "select", name: "category", label: t("categoryLabel"), anyLabel: t("anyCategory"),
      options: (facets?.categories ?? []).map((c) => ({ value: c.slug, label: c.name })),
    },
    {
      type: "select", name: "max_hours", label: t("duration"), anyLabel: t("anyDuration"),
      options: DURATIONS.map((hours) => ({ value: String(hours), label: t("upToHours", { count: hours }) })),
    },
    { type: "number", name: "max_price", label: t("maxPrice"), min: 0, step: 5000 },
  ];

  return (
    <>
      <PageHeader title={t("title")} description={t("intro")} breadcrumbs={[{ label: t("title") }]} />
      <Container className="flex flex-col gap-8 py-10 sm:py-14">
        {facets === null && result === null ? (
          <ErrorState title={t("errorTitle")} description={t("errorText")} />
        ) : facets?.count === 0 ? (
          <EmptyState
            title={t("noneTitle")}
            description={t("noneText")}
            action={
              <Link href={quoteHref} className={buttonVariants({ variant: "cta" })}>
                {t("askAgency")}
              </Link>
            }
          />
        ) : (
          <CatalogLayout
            heading={t("results", { count: result?.count ?? 0 })}
            filters={
              <FilterPanel
                pathname={PATH}
                fields={fields}
                current={{ ...current, ordering: undefined }}
                keep={{ ordering: current.ordering }}
                labels={{ title: t("filters"), formLabel: t("filtersLabel"), apply: t("apply"), reset: t("reset") }}
              />
            }
            sort={
              result &&
              result.count > 1 && (
                <SortSelect
                  pathname={PATH}
                  query={current}
                  label={t("sortLabel")}
                  options={ACTIVITY_SORTS.map((sort) => ({ value: sort, label: t(`sort.${sort}`) }))}
                />
              )
            }
          >
            {result && result.count > 0 ? (
              <>
                <ResultGrid>
                  {result.results.map((activity, index) => (
                    <li key={activity.id} className="grid">
                      <ActivityCard activity={activity} query={carried} priority={index < 2} />
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
                  <div className="flex flex-wrap justify-center gap-3">
                    <Link href={PATH} className={buttonVariants({ variant: "outline" })}>
                      {t("reset")}
                    </Link>
                    <Link href={quoteHref} className={buttonVariants({ variant: "cta" })}>
                      {t("askAgency")}
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
