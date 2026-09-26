import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { ResidenceCard } from "@/components/accommodations/stay-cards";
import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/common/pagination";
import { SegmentedNav } from "@/components/common/segmented-nav";
import { EmptyState, ErrorState } from "@/components/common/states";
import { CatalogLayout, ResultGrid } from "@/components/search/catalog-layout";
import { FilterPanel, type FilterField, type FilterValues } from "@/components/search/filter-panel";
import { SortSelect } from "@/components/search/sort-select";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { intParam, pageParam, param, type SearchParams } from "@/lib/search-params";
import { alternates } from "@/lib/seo";
import { parseStay, stayQuery } from "@/lib/stay";
import {
  amenities as listAmenities,
  listResidences,
  RESIDENCE_SORTS,
  residenceFacets,
  type ResidenceFilters,
} from "@/services/accommodations.service";
import type { Paginated, ResidenceList } from "@/types";

const PATH = "/residences";
const PAGE_SIZE = 12;

function parseFilters(params: SearchParams): ResidenceFilters {
  const slug = param(params, "destination");
  const amenities = param(params, "amenities");
  const ordering = param(params, "ordering");
  const stay = parseStay(params, { start: "available_from", end: "available_to" });
  return {
    destination: slug && /^[\w-]{1,100}$/.test(slug) ? slug : undefined,
    available_from: stay.start,
    available_to: stay.end,
    min_capacity: intParam(params, "min_capacity", 1, 50),
    min_rooms: intParam(params, "min_rooms", 1, 20),
    amenities: amenities && /^\d+(,\d+)*$/.test(amenities) ? amenities : undefined,
    max_price: intParam(params, "max_price", 0, 100_000_000),
    ordering: RESIDENCE_SORTS.includes(ordering as (typeof RESIDENCE_SORTS)[number]) ? ordering : undefined,
    page: pageParam(params),
  };
}

function asStrings(filters: ResidenceFilters): FilterValues {
  return Object.fromEntries(
    Object.entries(filters)
      .filter(([key]) => key !== "page")
      .map(([key, value]) => [key, value === undefined ? undefined : String(value)]),
  );
}

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/residences">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Stays" });
  const filters = parseFilters(query);
  const filtered = Object.values(asStrings(filters)).some(Boolean) || (filters.page ?? 1) > 1;
  return {
    title: t("residences.title"),
    description: t("residences.metaDescription"),
    alternates: alternates(PATH, locale),
    robots: filtered ? { index: false, follow: true } : undefined,
  };
}

/** Résidences meublées (CdC § 13). */
export default async function ResidencesPage({ params, searchParams }: PageProps<"/[locale]/residences">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const t = await getTranslations("Stays");
  const filters = parseFilters(query);
  const current = asStrings(filters);

  let result: Paginated<ResidenceList> | null = null;
  let facets: Awaited<ReturnType<typeof residenceFacets>> | null = null;
  const amenitiesRequest = listAmenities("residence");
  try {
    [result, facets] = await Promise.all([listResidences(filters), residenceFacets()]);
  } catch {
    // Page hors limites (404 de l'API) ou API indisponible.
    facets = await residenceFacets().catch(() => null);
  }
  const amenities = await amenitiesRequest;

  const stay = stayQuery({ start: filters.available_from, end: filters.available_to });
  const quoteHref = "/devis?service=HEBERGEMENT";

  const fields: FilterField[] = [
    {
      type: "select", name: "destination", label: t("destination"), anyLabel: t("anyDestination"),
      options: (facets?.destinations ?? []).map((d) => ({ value: d.slug, label: d.name })),
    },
    { type: "date", name: "available_from", label: t("arrival") },
    { type: "date", name: "available_to", label: t("departure") },
    { type: "number", name: "min_capacity", label: t("travelers"), min: 1, max: 50 },
    { type: "number", name: "min_rooms", label: t("minRooms"), min: 1, max: 20 },
    {
      type: "checkboxes", name: "amenities", label: t("amenities"),
      options: amenities.map((a) => ({ value: String(a.id), label: a.name })),
    },
    { type: "number", name: "max_price", label: t("maxPrice"), min: 0, step: 5000 },
  ];

  return (
    <>
      <PageHeader
        title={t("residences.title")}
        description={t("residences.intro")}
        breadcrumbs={[{ label: t("hotels.title"), href: "/hotels" }, { label: t("residences.title") }]}
      />
      <Container className="flex flex-col gap-8 py-10 sm:py-14">
        <SegmentedNav
          label={t("kindLabel")}
          current={PATH}
          items={[
            { href: "/hotels", label: t("hotels.short") },
            { href: "/residences", label: t("residences.short") },
          ]}
        />

        {facets === null && result === null ? (
          <ErrorState title={t("errorTitle")} description={t("errorText")} />
        ) : (
          <CatalogLayout
            heading={t("residences.results", { count: result?.count ?? 0 })}
            filters={
              <FilterPanel
                pathname={PATH}
                fields={fields}
                current={{ ...current, ordering: undefined }}
                keep={{ ordering: current.ordering }}
                labels={{ title: t("filters"), formLabel: t("residences.filtersLabel"), apply: t("apply"), reset: t("reset") }}
              />
            }
            sort={
              result &&
              result.count > 1 && (
                <SortSelect
                  pathname={PATH}
                  query={current}
                  label={t("sortLabel")}
                  options={RESIDENCE_SORTS.map((sort) => ({ value: sort, label: t(`sort.${sort}`) }))}
                />
              )
            }
          >
            {result && result.count > 0 ? (
              <>
                <ResultGrid>
                  {result.results.map((residence, index) => (
                    <li key={residence.id} className="grid">
                      <ResidenceCard residence={residence} stay={stay} priority={index < 2} />
                    </li>
                  ))}
                </ResultGrid>
                <Pagination page={filters.page ?? 1} count={result.count} pageSize={PAGE_SIZE} pathname={PATH} query={current} />
              </>
            ) : (
              <EmptyState
                title={t("residences.emptyTitle")}
                description={t("residences.emptyText")}
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
