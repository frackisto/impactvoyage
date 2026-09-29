import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { HotelCard } from "@/components/accommodations/stay-cards";
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
import { pageMetadata } from "@/lib/seo";
import { parseStay, stayQuery } from "@/lib/stay";
import {
  amenities as listAmenities,
  HOTEL_SORTS,
  HOTEL_TYPES,
  hotelFacets,
  listHotels,
  type HotelFilters,
} from "@/services/accommodations.service";
import type { HotelList, Paginated } from "@/types";

const PATH = "/hotels";
const PAGE_SIZE = 12;

/** Filtres lus dans l'URL (noms de l'API et du moteur de recherche) ; valeurs invalides ignorées. */
function parseFilters(params: SearchParams): HotelFilters {
  const slug = param(params, "destination");
  const type = param(params, "accommodation_type");
  const amenities = param(params, "amenities");
  const ordering = param(params, "ordering");
  const stay = parseStay(params, { start: "available_from", end: "available_to" });
  return {
    destination: slug && /^[\w-]{1,100}$/.test(slug) ? slug : undefined,
    accommodation_type: HOTEL_TYPES.includes(type as (typeof HOTEL_TYPES)[number]) ? type : undefined,
    stars: intParam(params, "stars", 1, 5),
    amenities: amenities && /^\d+(,\d+)*$/.test(amenities) ? amenities : undefined,
    travelers: stay.travelers,
    rooms: stay.rooms,
    available_from: stay.start,
    available_to: stay.end,
    max_price: intParam(params, "max_price", 0, 100_000_000),
    ordering: HOTEL_SORTS.includes(ordering as (typeof HOTEL_SORTS)[number]) ? ordering : undefined,
    page: pageParam(params),
  };
}

function asStrings(filters: HotelFilters): FilterValues {
  return Object.fromEntries(
    Object.entries(filters)
      .filter(([key]) => key !== "page")
      .map(([key, value]) => [key, value === undefined ? undefined : String(value)]),
  );
}

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/hotels">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Stays" });
  const filters = parseFilters(query);
  const filtered = Object.values(asStrings(filters)).some(Boolean) || (filters.page ?? 1) > 1;
  return pageMetadata({ locale, path: PATH, title: t("hotels.title"), description: t("hotels.metaDescription"), noindex: filtered });
}

export default async function HotelsPage({ params, searchParams }: PageProps<"/[locale]/hotels">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const t = await getTranslations("Stays");
  const filters = parseFilters(query);
  const current = asStrings(filters);

  let result: Paginated<HotelList> | null = null;
  let facets: Awaited<ReturnType<typeof hotelFacets>> | null = null;
  const amenitiesRequest = listAmenities("hotel");
  try {
    [result, facets] = await Promise.all([listHotels(filters), hotelFacets()]);
  } catch {
    // Page hors limites (404 de l'API) ou API indisponible.
    facets = await hotelFacets().catch(() => null);
  }
  const amenities = await amenitiesRequest;

  // La fiche reprend les dates et le nombre de voyageurs pour afficher les disponibilités.
  const stay = stayQuery({
    start: filters.available_from,
    end: filters.available_to,
    travelers: filters.travelers,
    rooms: filters.rooms,
  });
  const quoteHref = "/devis?service=HEBERGEMENT";

  const fields: FilterField[] = [
    {
      type: "select", name: "destination", label: t("destination"), anyLabel: t("anyDestination"),
      options: (facets?.destinations ?? []).map((d) => ({ value: d.slug, label: d.name })),
    },
    { type: "date", name: "available_from", label: t("arrival") },
    { type: "date", name: "available_to", label: t("departure") },
    { type: "number", name: "travelers", label: t("travelers"), min: 1, max: 20 },
    { type: "number", name: "rooms", label: t("rooms"), min: 1, max: 10 },
    {
      type: "select", name: "accommodation_type", label: t("typeLabel"), anyLabel: t("anyType"),
      options: (facets?.types ?? []).map((type) => ({ value: type, label: t(`type.${type}`) })),
    },
    {
      type: "select", name: "stars", label: t("category"), anyLabel: t("anyCategory"),
      options: (facets?.stars ?? []).map((count) => ({ value: String(count), label: t("stars", { count }) })),
    },
    {
      type: "checkboxes", name: "amenities", label: t("amenities"),
      options: amenities.map((a) => ({ value: String(a.id), label: a.name })),
    },
    { type: "number", name: "max_price", label: t("maxPrice"), min: 0, step: 5000 },
  ];

  return (
    <>
      <PageHeader title={t("hotels.title")} description={t("hotels.intro")} breadcrumbs={[{ label: t("hotels.title") }]} />
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
            heading={t("hotels.results", { count: result?.count ?? 0 })}
            filters={
              <FilterPanel
                pathname={PATH}
                fields={fields}
                current={{ ...current, ordering: undefined }}
                keep={{ ordering: current.ordering }}
                labels={{ title: t("filters"), formLabel: t("hotels.filtersLabel"), apply: t("apply"), reset: t("reset") }}
              />
            }
            sort={
              result &&
              result.count > 1 && (
                <SortSelect
                  pathname={PATH}
                  query={current}
                  label={t("sortLabel")}
                  options={HOTEL_SORTS.map((sort) => ({ value: sort, label: t(`sort.${sort}`) }))}
                />
              )
            }
          >
            {result && result.count > 0 ? (
              <>
                <ResultGrid>
                  {result.results.map((hotel, index) => (
                    <li key={hotel.id} className="grid">
                      <HotelCard hotel={hotel} stay={stay} priority={index < 2} />
                    </li>
                  ))}
                </ResultGrid>
                <Pagination page={filters.page ?? 1} count={result.count} pageSize={PAGE_SIZE} pathname={PATH} query={current} />
              </>
            ) : (
              <EmptyState
                title={t("hotels.emptyTitle")}
                description={t("hotels.emptyText")}
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
