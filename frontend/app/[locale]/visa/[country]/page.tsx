import { CheckIcon, ClockIcon, FileTextIcon, HourglassIcon, TargetIcon, WalletIcon } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Price } from "@/components/common/price";
import { breadcrumbList, JsonLd } from "@/components/seo/json-ld";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { countryName } from "@/lib/countries";
import { pageMetadata } from "@/lib/seo";
import { paragraphs } from "@/lib/text";
import { visasForCountry } from "@/services/agency.service";
import { getSiteSettings, whatsappUrl } from "@/services/site.service";

type Props = PageProps<"/[locale]/visa/[country]">;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, country } = await params;
  const visas = await visasForCountry(country);
  if (!visas?.length) notFound();
  const t = await getTranslations({ locale, namespace: "Visa" });
  const name = countryName(visas[0].destination_country_code, locale);
  return pageMetadata({
    locale,
    path: `/visa/${country}`,
    title: t("visaFor", { country: name }),
    description: t("countryMeta", { country: name }),
  });
}

/** Formules de visa d'un pays (/visa/france) : délais, frais, pièces à fournir. */
export default async function VisaCountryPage({ params }: Props) {
  const { locale, country } = await params;
  setRequestLocale(locale);
  const visas = await visasForCountry(country);
  if (!visas?.length) notFound();

  const [t, tNav, lang, settings] = await Promise.all([getTranslations("Visa"), getTranslations("Nav"), getLocale(), getSiteSettings()]);
  const code = visas[0].destination_country_code;
  const name = countryName(code, lang);
  const title = t("visaFor", { country: name });
  const breadcrumbs = [{ label: t("title"), href: "/visa" }, { label: name }];
  const nationalities = [...new Set(visas.map((v) => v.nationality_code))].map((c) => countryName(c, lang));
  const whatsapp = whatsappUrl(settings.whatsapp);

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [breadcrumbList([{ label: tNav("home"), href: "/" }, ...breadcrumbs], `/visa/${country}`, locale)],
        }}
      />
      <PageHeader
        title={title}
        description={t("countryIntro", { country: name, nationalities: nationalities.join(", ") })}
        breadcrumbs={breadcrumbs}
      />
      <Container className="grid gap-10 py-10 sm:py-14 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <div className="flex flex-col gap-6">
          <h2 className="text-2xl font-bold text-ocean-900">{t("formulas", { count: visas.length })}</h2>
          {visas.map((visa) => {
            const headingId = `visa-${visa.id}`;
            const facts = [
              { icon: TargetIcon, label: t("purposeLabel"), value: t(`purpose.${visa.purpose}`) },
              visa.validity_duration ? { icon: HourglassIcon, label: t("validity"), value: visa.validity_duration } : null,
              visa.processing_time ? { icon: ClockIcon, label: t("processing"), value: visa.processing_time } : null,
            ].filter((fact) => fact !== null);
            return (
              <article key={visa.id} aria-labelledby={headingId} className="flex flex-col gap-5 rounded-3xl border bg-card p-6 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <h3 id={headingId} className="text-xl font-bold text-ocean-900">
                    {visa.visa_type}
                  </h3>
                  <div className="flex items-center gap-2 text-lg font-bold text-ocean-900">
                    <WalletIcon aria-hidden="true" className="size-5 text-ocean-600" />
                    <span className="sr-only">{t("fees")} :</span>
                    {visa.fees ? <Price value={visa.fees} /> : <span className="text-base font-normal text-muted-foreground">{t("onRequest")}</span>}
                  </div>
                </div>
                <dl className="grid gap-3 sm:grid-cols-3">
                  {facts.map(({ icon: Icon, label, value }) => (
                    <div key={label} className="flex flex-col gap-0.5">
                      <dt className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Icon aria-hidden="true" className="size-4 shrink-0 text-ocean-600" />
                        {label}
                      </dt>
                      <dd className="ps-6 font-semibold text-ocean-950">{value}</dd>
                    </div>
                  ))}
                </dl>
                {paragraphs(visa.description).map((p, i) => (
                  <p key={i} className="text-ocean-950/90">
                    {p}
                  </p>
                ))}
                {visa.required_documents.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <h4 className="flex items-center gap-2 font-semibold text-ocean-900">
                      <FileTextIcon aria-hidden="true" className="size-5 text-ocean-600" />
                      {t("documents")}
                    </h4>
                    <ul className="grid gap-1.5 sm:grid-cols-2">
                      {visa.required_documents.map((doc) => (
                        <li key={doc} className="flex gap-2 text-ocean-950">
                          <CheckIcon aria-hidden="true" className="mt-1 size-4 shrink-0 text-emerald-600" />
                          {doc}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </article>
            );
          })}
          <p className="rounded-2xl bg-sunset-50 p-4 text-sm text-ocean-950">{t("disclaimer")}</p>
        </div>

        <aside aria-labelledby="visa-help" className="lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-4 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <h2 id="visa-help" className="text-xl font-bold text-ocean-900">
              {t("helpTitle")}
            </h2>
            <p className="text-ocean-950/90">{t("helpText")}</p>
            <Link href="/devis?service=VISA" className={buttonVariants({ variant: "cta", size: "lg" })}>
              {t("askHelp")}
            </Link>
            {whatsapp && (
              <a href={whatsapp} target="_blank" rel="noopener noreferrer" className={buttonVariants({ variant: "outline" })}>
                {t("whatsapp")}
                <span className="sr-only">{t("newTab")}</span>
              </a>
            )}
            <Link href="/services#visa-et-formalites" className="text-sm font-semibold text-ocean-700 underline-offset-4 hover:underline">
              {t("seeFees")}
            </Link>
          </div>
        </aside>
      </Container>
    </>
  );
}
