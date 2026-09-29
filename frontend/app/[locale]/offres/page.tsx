import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/common/pagination";
import { EmptyState, ErrorState } from "@/components/common/states";
import { OfferCard } from "@/components/offers/offer-card";
import { CatalogLayout, ResultGrid } from "@/components/search/catalog-layout";
import { FilterPanel, type FilterField } from "@/components/search/filter-panel";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { pageParam, param, type SearchParams } from "@/lib/search-params";
import { pageMetadata } from "@/lib/seo";
import { listOffers, OFFER_TYPES, offerFacets, type OfferFilters } from "@/services/agency.service";
import type { OfferList, Paginated } from "@/types";

const PATH = "/offres";
const PAGE_SIZE = 12;

function parseFilters(params: SearchParams): OfferFilters {
  const type = param(params, "offer_type");
  return {
    offer_type: OFFER_TYPES.includes(type as (typeof OFFER_TYPES)[number]) ? type : undefined,
    page: pageParam(params),
  };
}

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/offres">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Offers" });
  const filters = parseFilters(query);
  return pageMetadata({
    locale,
    path: PATH,
    title: t("title"),
    description: t("metaDescription"),
    noindex: Boolean(filters.offer_type || (filters.page ?? 1) > 1),
  });
}

/** Offres promotionnelles en cours (CdC § 17), les plus proches de leur fin en premier. */
export default async function OffersPage({ params, searchParams }: PageProps<"/[locale]/offres">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const t = await getTranslations("Offers");
  const filters = parseFilters(query);
  const current = { offer_type: filters.offer_type };

  let result: Paginated<OfferList> | null = null;
  let facets: Awaited<ReturnType<typeof offerFacets>> | null = null;
  try {
    [result, facets] = await Promise.all([listOffers(filters), offerFacets()]);
  } catch {
    facets = await offerFacets().catch(() => null);
  }

  const fields: FilterField[] = [
    {
      type: "select", name: "offer_type", label: t("typeLabel"), anyLabel: t("anyType"),
      options: (facets?.types ?? []).map((type) => ({ value: type, label: t(`type.${type}`) })),
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
                  <p className="font-heading text-lg font-bold">{t("customTitle")}</p>
                  <p className="text-sm text-ocean-100">{t("customText")}</p>
                  <Link href="/devis" className={buttonVariants({ variant: "cta" })}>
                    {t("customCta")}
                  </Link>
                </div>
              </div>
            }
          >
            {result && result.count > 0 ? (
              <>
                <ResultGrid>
                  {result.results.map((offer, index) => (
                    <li key={offer.id} className="grid">
                      <OfferCard offer={offer} priority={index < 2} />
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
                  <Link href="/devis" className={buttonVariants({ variant: "cta" })}>
                    {t("customCta")}
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
