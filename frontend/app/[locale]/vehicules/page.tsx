import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/common/pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { CatalogLayout, ResultGrid } from "@/components/search/catalog-layout";
import { FilterPanel, type FilterField, type FilterValues } from "@/components/search/filter-panel";
import { SortSelect } from "@/components/search/sort-select";
import { buttonVariants } from "@/components/ui/button";
import { VehicleCard } from "@/components/vehicles/vehicle-card";
import { Link } from "@/i18n/navigation";
import { intParam, pageParam, param, type SearchParams } from "@/lib/search-params";
import { alternates } from "@/lib/seo";
import { parseStay } from "@/lib/stay";
import {
  listVehicles,
  TRANSMISSIONS,
  VEHICLE_CATEGORIES,
  VEHICLE_SORTS,
  vehicleFacets,
  type VehicleFilters,
} from "@/services/vehicles.service";
import type { Paginated, VehicleList } from "@/types";

const PATH = "/vehicules";
const PAGE_SIZE = 12;
const SEATS = [2, 4, 5, 7, 9, 15];

const oneOf = <T extends string>(values: readonly T[], value: string | undefined) =>
  values.includes(value as T) ? (value as T) : undefined;

/** Filtres lus dans l'URL (noms de l'API) ; valeurs invalides ignorées. */
function parseFilters(params: SearchParams): VehicleFilters {
  const period = parseStay(params, { start: "available_from", end: "available_to" });
  return {
    category: oneOf(VEHICLE_CATEGORIES, param(params, "category")),
    transmission: oneOf(TRANSMISSIONS, param(params, "transmission")),
    min_seats: intParam(params, "min_seats", 1, 60),
    max_price: intParam(params, "max_price", 0, 100_000_000),
    available_from: period.start,
    available_to: period.end,
    ordering: oneOf(VEHICLE_SORTS, param(params, "ordering")),
    page: pageParam(params),
  };
}

function asStrings(filters: VehicleFilters): FilterValues {
  return Object.fromEntries(
    Object.entries(filters)
      .filter(([key]) => key !== "page")
      .map(([key, value]) => [key, value === undefined ? undefined : String(value)]),
  );
}

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/vehicules">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Vehicles" });
  const filters = parseFilters(query);
  const filtered = Object.values(asStrings(filters)).some(Boolean) || (filters.page ?? 1) > 1;
  return {
    title: t("title"),
    description: t("metaDescription"),
    alternates: alternates(PATH, locale),
    robots: filtered ? { index: false, follow: true } : undefined,
  };
}

/** Location de véhicules (CdC § 12). */
export default async function VehiclesPage({ params, searchParams }: PageProps<"/[locale]/vehicules">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const t = await getTranslations("Vehicles");
  const filters = parseFilters(query);
  const current = asStrings(filters);

  let result: Paginated<VehicleList> | null = null;
  let facets: Awaited<ReturnType<typeof vehicleFacets>> | null = null;
  try {
    [result, facets] = await Promise.all([listVehicles(filters), vehicleFacets()]);
  } catch {
    // Page hors limites (404 de l'API) ou API indisponible.
    facets = await vehicleFacets().catch(() => null);
  }

  // La fiche reprend la période pour afficher la disponibilité.
  const period = { start: filters.available_from, end: filters.available_to };
  const quoteHref = "/devis?service=LOCATION_VEHICULE";

  const fields: FilterField[] = [
    { type: "date", name: "available_from", label: t("pickup") },
    { type: "date", name: "available_to", label: t("dropoff") },
    {
      type: "select", name: "category", label: t("categoryLabel"), anyLabel: t("anyCategory"),
      options: (facets?.categories ?? []).map((c) => ({ value: c, label: t(`category.${c}`) })),
    },
    {
      type: "select", name: "min_seats", label: t("minSeats"), anyLabel: t("anySeats"),
      options: SEATS.filter((n) => n <= (facets?.maxSeats ?? 0)).map((n) => ({ value: String(n), label: t("atLeastSeats", { count: n }) })),
    },
    {
      type: "select", name: "transmission", label: t("transmissionLabel"), anyLabel: t("anyTransmission"),
      options: (facets?.transmissions ?? []).map((v) => ({ value: v, label: t(`transmission.${v}`) })),
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
                  options={VEHICLE_SORTS.map((sort) => ({ value: sort, label: t(`sort.${sort}`) }))}
                />
              )
            }
          >
            {filters.available_from && result && result.count > 0 && (
              <p className="-mt-3 text-sm text-emerald-800">{t("availableOnPeriod")}</p>
            )}
            {result && result.count > 0 ? (
              <>
                <ResultGrid>
                  {result.results.map((vehicle, index) => (
                    <li key={vehicle.id} className="grid">
                      <VehicleCard vehicle={vehicle} period={period} priority={index < 2} />
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
