import { ArrowRightIcon, CalendarClockIcon, CarFrontIcon, UsersIcon } from "lucide-react";
import type { Metadata } from "next";
import Image from "next/image";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/common/pagination";
import { Price } from "@/components/common/price";
import { EmptyState, ErrorState } from "@/components/common/states";
import { CatalogLayout } from "@/components/search/catalog-layout";
import { FilterPanel, type FilterField } from "@/components/search/filter-panel";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { mediaSrc } from "@/lib/media";
import { pageHref } from "@/lib/pagination";
import { dateParam, intParam, pageParam, param, type SearchParams } from "@/lib/search-params";
import { alternates } from "@/lib/seo";
import { paragraphs } from "@/lib/text";
import { listTransport, TRANSPORT_TYPES, type TransportFilters } from "@/services/agency.service";
import type { Paginated, TransportService } from "@/types";

const PATH = "/transport";
const PAGE_SIZE = 12;

function parseFilters(params: SearchParams): TransportFilters {
  const type = param(params, "transport_type");
  const text = (key: string) => param(params, key)?.trim().slice(0, 150) || undefined;
  return {
    transport_type: TRANSPORT_TYPES.includes(type as (typeof TRANSPORT_TYPES)[number]) ? type : undefined,
    origin: text("origin"),
    destination: text("destination"),
    passengers: intParam(params, "passengers", 1, 99),
    page: pageParam(params),
  };
}

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/transport">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Transport" });
  const { page, ...filters } = parseFilters(query);
  const filtered = Object.values(filters).some(Boolean) || (page ?? 1) > 1;
  return {
    title: t("title"),
    description: t("metaDescription"),
    alternates: alternates(PATH, locale),
    robots: filtered ? { index: false, follow: true } : undefined,
  };
}

/**
 * Transferts, navettes et véhicules avec chauffeur (CdC § 7 « Transport »),
 * cible de l'onglet Transport du moteur de recherche de l'accueil.
 */
export default async function TransportPage({ params, searchParams }: PageProps<"/[locale]/transport">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const t = await getTranslations("Transport");
  const filters = parseFilters(query);
  const current = {
    transport_type: filters.transport_type,
    origin: filters.origin,
    destination: filters.destination,
    passengers: filters.passengers ? String(filters.passengers) : undefined,
  };
  // La date et le nombre de voyageurs du moteur de recherche sont repris dans la demande de devis.
  const quoteHref = pageHref(
    "/devis",
    { service: "TRANSPORT", start: dateParam(query, "date"), travelers: filters.passengers && filters.passengers <= 20 ? String(filters.passengers) : undefined },
    1,
  );

  let result: Paginated<TransportService> | null = null;
  try {
    result = await listTransport(filters);
  } catch {
    result = null;
  }

  const fields: FilterField[] = [
    {
      type: "select", name: "transport_type", label: t("typeLabel"), anyLabel: t("anyType"),
      options: TRANSPORT_TYPES.map((type) => ({ value: type, label: t(`type.${type}`) })),
    },
    { type: "text", name: "origin", label: t("origin"), placeholder: t("originPlaceholder") },
    { type: "text", name: "destination", label: t("destination"), placeholder: t("destinationPlaceholder") },
    { type: "number", name: "passengers", label: t("passengers"), min: 1, max: 99 },
  ];

  return (
    <>
      <PageHeader title={t("title")} description={t("intro")} breadcrumbs={[{ label: t("title") }]} />
      <Container className="flex flex-col gap-8 py-10 sm:py-14">
        {result === null ? (
          <ErrorState title={t("errorTitle")} description={t("errorText")} />
        ) : (
          <CatalogLayout
            heading={t("results", { count: result.count })}
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
                  <Link href={quoteHref} className={buttonVariants({ variant: "cta" })}>
                    {t("askQuote")}
                  </Link>
                </div>
              </div>
            }
          >
            {result.count > 0 ? (
              <>
                <ul className="flex flex-col gap-5">
                  {result.results.map((service, index) => (
                    <li key={service.id}>
                      <TransportCard service={service} quoteHref={quoteHref} priority={index === 0} />
                    </li>
                  ))}
                </ul>
                <Pagination page={filters.page ?? 1} count={result.count} pageSize={PAGE_SIZE} pathname={PATH} query={current} />
              </>
            ) : (
              <EmptyState
                title={t("emptyTitle")}
                description={t("emptyText")}
                action={
                  <Link href={quoteHref} className={buttonVariants({ variant: "cta" })}>
                    {t("askQuote")}
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

async function TransportCard({ service, quoteHref, priority }: { service: TransportService; quoteHref: string; priority?: boolean }) {
  const t = await getTranslations("Transport");
  const image = mediaSrc(service.cover_image);
  const headingId = `transport-${service.slug}`;
  return (
    <article aria-labelledby={headingId} className="grid overflow-hidden rounded-2xl border bg-card shadow-sm sm:grid-cols-[14rem_minmax(0,1fr)]">
      <div className="relative aspect-video bg-ocean-50 sm:aspect-auto">
        {image ? (
          <Image src={image} alt={service.cover_alt || service.title} fill priority={priority} sizes="(min-width: 640px) 224px, 100vw" className="object-cover" />
        ) : (
          <div className="flex size-full min-h-32 items-center justify-center text-ocean-300">
            <CarFrontIcon aria-hidden="true" className="size-12" />
          </div>
        )}
      </div>
      <div className="flex flex-col gap-3 p-5">
        <p className="text-sm font-medium text-ocean-700">{t(`type.${service.transport_type}`)}</p>
        <h3 id={headingId} className="text-xl font-semibold text-ocean-950">
          {service.title}
        </h3>
        <p className="flex flex-wrap items-center gap-2 font-medium text-ocean-900">
          {service.origin}
          <ArrowRightIcon aria-label={t("to")} className="size-4 text-sunset-600 rtl:rotate-180" />
          {service.destination}
        </p>
        {paragraphs(service.description).map((p, i) => (
          <p key={i} className="text-sm text-muted-foreground">
            {p}
          </p>
        ))}
        <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted-foreground">
          {service.max_passengers && (
            <span className="inline-flex items-center gap-1.5">
              <UsersIcon aria-hidden="true" className="size-4 text-ocean-600" />
              {t("maxPassengers", { count: service.max_passengers })}
            </span>
          )}
          {service.schedule_info && (
            <span className="inline-flex items-center gap-1.5">
              <CalendarClockIcon aria-hidden="true" className="size-4 text-ocean-600" />
              {service.schedule_info}
            </span>
          )}
        </div>
        <div className="mt-auto flex flex-wrap items-end justify-between gap-3 pt-1">
          {service.price_from ? <Price value={service.price_from} from /> : <span className="text-sm text-muted-foreground">{t("onRequest")}</span>}
          <Link href={quoteHref} className={buttonVariants({ variant: "outline" })}>
            {t("request")}
            <span className="sr-only"> : {service.title}</span>
          </Link>
        </div>
      </div>
    </article>
  );
}
