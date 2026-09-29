import { ArrowRightIcon, StampIcon } from "lucide-react";
import type { Metadata } from "next";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Price } from "@/components/common/price";
import { EmptyState, ErrorState } from "@/components/common/states";
import { CatalogLayout } from "@/components/search/catalog-layout";
import { FilterPanel, type FilterField } from "@/components/search/filter-panel";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { countryFlag, countryName } from "@/lib/countries";
import { param, type SearchParams } from "@/lib/search-params";
import { pageMetadata } from "@/lib/seo";
import { listVisas, VISA_PURPOSES, type VisaFilters } from "@/services/agency.service";
import type { VisaService } from "@/types";

const PATH = "/visa";

function parseFilters(params: SearchParams): VisaFilters {
  const country = param(params, "destination_country_code");
  const purpose = param(params, "purpose");
  return {
    destination_country_code: country && /^[A-Za-z]{2}$/.test(country) ? country.toUpperCase() : undefined,
    purpose: VISA_PURPOSES.includes(purpose as (typeof VISA_PURPOSES)[number]) ? purpose : undefined,
  };
}

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/visa">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Visa" });
  const filters = parseFilters(query);
  return pageMetadata({
    locale,
    path: PATH,
    title: t("title"),
    description: t("metaDescription"),
    noindex: Boolean(filters.destination_country_code || filters.purpose),
  });
}

/** Formules de visa par pays (CdC § 7 « Visa », § 11), filtrables par pays et motif. */
export default async function VisaListPage({ params, searchParams }: PageProps<"/[locale]/visa">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const [t, lang] = await Promise.all([getTranslations("Visa"), getLocale()]);
  const filters = parseFilters(query);

  // Toutes les formules (options des filtres) et celles qui correspondent.
  const [all, filtered] = await Promise.all([
    listVisas().catch(() => null),
    listVisas(filters).catch(() => null),
  ]);
  const countries = [...new Map((all?.results ?? []).map((v) => [v.destination_country_code, v])).values()]
    .map((v) => ({ code: v.destination_country_code, name: countryName(v.destination_country_code, lang) }))
    .sort((a, b) => a.name.localeCompare(b.name, lang));
  const purposes = VISA_PURPOSES.filter((p) => all?.results.some((v) => v.purpose === p));

  // Regroupement par pays de destination.
  const groups = new Map<string, VisaService[]>();
  for (const visa of filtered?.results ?? []) {
    groups.set(visa.country_slug, [...(groups.get(visa.country_slug) ?? []), visa]);
  }
  const byCountry = [...groups.values()].sort((a, b) =>
    countryName(a[0].destination_country_code, lang).localeCompare(countryName(b[0].destination_country_code, lang), lang),
  );

  const fields: FilterField[] = [
    {
      type: "select", name: "destination_country_code", label: t("country"), anyLabel: t("anyCountry"),
      options: countries.map((c) => ({ value: c.code, label: c.name })),
    },
    {
      type: "select", name: "purpose", label: t("purposeLabel"), anyLabel: t("anyPurpose"),
      options: purposes.map((p) => ({ value: p, label: t(`purpose.${p}`) })),
    },
  ];

  return (
    <>
      <PageHeader title={t("title")} description={t("intro")} breadcrumbs={[{ label: t("title") }]} />
      <Container className="flex flex-col gap-8 py-10 sm:py-14">
        {filtered === null ? (
          <ErrorState title={t("errorTitle")} description={t("errorText")} />
        ) : (
          <CatalogLayout
            heading={t("results", { count: byCountry.length })}
            filters={
              <div className="flex flex-col gap-4">
                <FilterPanel
                  pathname={PATH}
                  fields={fields}
                  current={{ destination_country_code: filters.destination_country_code, purpose: filters.purpose }}
                  labels={{ title: t("filters"), formLabel: t("filtersLabel"), apply: t("apply"), reset: t("reset") }}
                />
                <div className="flex flex-col gap-3 rounded-2xl bg-ocean-900 p-5 text-white">
                  <p className="font-heading text-lg font-bold">{t("helpTitle")}</p>
                  <p className="text-sm text-ocean-100">{t("helpText")}</p>
                  <Link href="/devis?service=VISA" className={buttonVariants({ variant: "cta" })}>
                    {t("askHelp")}
                  </Link>
                </div>
              </div>
            }
          >
            {byCountry.length > 0 ? (
              <ul className="grid gap-5 sm:grid-cols-2">
                {byCountry.map((visas) => {
                  const first = visas[0];
                  const name = countryName(first.destination_country_code, lang);
                  const fees = visas.map((v) => v.fees).filter((f) => f !== null);
                  const cheapest = fees.sort((a, b) => Number(a.amount) - Number(b.amount))[0];
                  return (
                    <li key={first.country_slug} className="grid">
                      <article className="relative flex flex-col gap-4 rounded-2xl border bg-card p-5 transition-shadow focus-within:ring-2 focus-within:ring-ring hover:shadow-lg hover:shadow-ocean-900/5">
                        <div className="flex items-center gap-4">
                          <span aria-hidden="true" className="text-5xl leading-none">
                            {countryFlag(first.destination_country_code)}
                          </span>
                          <div className="flex flex-col">
                            <h3 className="font-heading text-xl font-semibold text-ocean-950">
                              <Link href={`/visa/${first.country_slug}`} className="after:absolute after:inset-0 focus-visible:outline-none">
                                {t("visaFor", { country: name })}
                              </Link>
                            </h3>
                            <p className="text-sm text-muted-foreground">{t("formulas", { count: visas.length })}</p>
                          </div>
                        </div>
                        <ul className="flex flex-col gap-1.5 text-sm text-ocean-950">
                          {visas.map((visa) => (
                            <li key={visa.id} className="flex items-center gap-2">
                              <StampIcon aria-hidden="true" className="size-4 shrink-0 text-ocean-600" />
                              {visa.visa_type} · {t(`purpose.${visa.purpose}`)}
                            </li>
                          ))}
                        </ul>
                        <div className="mt-auto flex items-end justify-between gap-2">
                          {cheapest ? <Price value={cheapest} from /> : <span className="text-sm text-muted-foreground">{t("onRequest")}</span>}
                          <ArrowRightIcon aria-hidden="true" className="size-5 text-ocean-600 rtl:rotate-180" />
                        </div>
                      </article>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <EmptyState
                title={t("emptyTitle")}
                description={t("emptyText")}
                action={
                  <Link href="/devis?service=VISA" className={buttonVariants({ variant: "cta" })}>
                    {t("askHelp")}
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
