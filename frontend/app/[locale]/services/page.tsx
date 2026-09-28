import { ArrowRightIcon } from "lucide-react";
import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Price } from "@/components/common/price";
import { ServiceIcon } from "@/components/common/service-icon";
import { ErrorState } from "@/components/common/states";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { alternates } from "@/lib/seo";
import { paragraphs } from "@/lib/text";
import { cn } from "@/lib/utils";
import { listServices } from "@/services/agency.service";
import type { Service } from "@/types";

/** Rubrique du site qui détaille une prestation (catalogue, formules visa...). */
const CATALOG: Record<string, string> = {
  "circuits-et-excursions": "/circuits/nationaux",
  hebergement: "/hotels",
  "residences-meublees": "/residences",
  "location-de-voitures": "/vehicules",
  "visa-et-formalites": "/visa",
  evenementiel: "/evenements",
};

export async function generateMetadata({ params }: PageProps<"/[locale]/services">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "Services" });
  return { title: t("title"), description: t("metaDescription"), alternates: alternates("/services", locale) };
}

/** Prestations de l'agence (CdC § 11), dans l'ordre défini dans l'administration. */
export default async function ServicesPage({ params }: PageProps<"/[locale]/services">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("Services");
  const services = await listServices().catch(() => null);

  return (
    <>
      <PageHeader title={t("title")} description={t("intro")} breadcrumbs={[{ label: t("title") }]} />
      <Container className="flex flex-col gap-12 py-10 sm:py-14">
        {services === null ? (
          <ErrorState title={t("errorTitle")} description={t("errorText")} />
        ) : (
          <>
            <nav aria-label={t("summary")} className="flex flex-wrap gap-2">
              {services.map((service) => (
                <a
                  key={service.id}
                  href={`#${service.slug}`}
                  className="rounded-full border bg-card px-3.5 py-1.5 text-sm font-medium text-ocean-900 transition-colors hover:border-ocean-300 hover:bg-ocean-50"
                >
                  {service.title}
                </a>
              ))}
            </nav>
            <ul className="grid gap-6 md:grid-cols-2">
              {services.map((service) => (
                <li key={service.id} className="grid">
                  <ServiceBlock service={service} />
                </li>
              ))}
            </ul>
          </>
        )}

        <section aria-labelledby="services-cta" className="flex flex-col items-center gap-4 rounded-3xl bg-ocean-900 px-6 py-10 text-center text-white">
          <h2 id="services-cta" className="text-3xl font-bold">
            {t("ctaTitle")}
          </h2>
          <p className="max-w-2xl text-lg text-ocean-100">{t("ctaText")}</p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link href="/devis" className={buttonVariants({ variant: "cta", size: "lg" })}>
              {t("ctaQuote")}
            </Link>
            <Link href="/contact" className={cn(buttonVariants({ variant: "outline", size: "lg" }), "border-white/40 bg-transparent text-white hover:bg-white/10 hover:text-white")}>
              {t("ctaContact")}
            </Link>
          </div>
        </section>
      </Container>
    </>
  );
}

async function ServiceBlock({ service }: { service: Service }) {
  const t = await getTranslations("Services");
  const catalog = CATALOG[service.slug];
  const quoteHref = service.quote_service_type ? `/devis?service=${service.quote_service_type}` : "/devis";
  const headingId = `service-${service.slug}`;

  return (
    <article
      id={service.slug}
      aria-labelledby={headingId}
      className="flex scroll-mt-28 flex-col gap-4 rounded-3xl border bg-card p-6 shadow-sm"
    >
      <div className="flex items-start gap-4">
        <span className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-ocean-50 text-ocean-600">
          <ServiceIcon name={service.icon} className="size-7" />
        </span>
        <div className="flex flex-col gap-1">
          <h2 id={headingId} className="text-xl font-bold text-ocean-900">
            {service.title}
          </h2>
          {service.short_description && <p className="text-muted-foreground">{service.short_description}</p>}
        </div>
      </div>
      {paragraphs(service.description).map((p, i) => (
        <p key={i} className="text-ocean-950/90">
          {p}
        </p>
      ))}
      {service.prices.length > 0 && (
        <table className="w-full text-sm">
          <caption className="sr-only">{t("pricesCaption", { service: service.title })}</caption>
          <thead className="sr-only">
            <tr>
              <th scope="col">{t("formula")}</th>
              <th scope="col">{t("price")}</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {service.prices.map((price) => (
              <tr key={price.id}>
                <th scope="row" className="py-2 pe-3 text-start font-medium text-ocean-950">
                  {price.label}
                </th>
                <td className="py-2 text-end font-semibold text-ocean-900">
                  {price.price ? (
                    <span className="inline-flex items-baseline justify-end gap-1">
                      <Price value={price.price} compact />
                      {price.unit && <span className="text-xs font-normal text-muted-foreground">{price.unit}</span>}
                    </span>
                  ) : (
                    <span className="font-normal text-muted-foreground">{t("onRequest")}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="mt-auto flex flex-wrap gap-3 pt-2">
        <Link href={quoteHref} className={buttonVariants({ variant: "cta" })}>
          {t("askQuote")}
          <span className="sr-only"> : {service.title}</span>
        </Link>
        {catalog && (
          <Link href={catalog} className={buttonVariants({ variant: "outline" })}>
            {t("seeCatalog")}
            <span className="sr-only"> : {service.title}</span>
            <ArrowRightIcon aria-hidden="true" data-icon="inline-end" className="rtl:rotate-180" />
          </Link>
        )}
      </div>
    </article>
  );
}
