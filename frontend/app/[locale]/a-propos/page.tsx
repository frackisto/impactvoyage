import type { Metadata } from "next";
import Image from "next/image";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Section, SectionHeader } from "@/components/common/page-section";
import { ServiceIcon } from "@/components/common/service-icon";
import { AgencyDetails, travelAgencyJsonLd } from "@/components/contact/agency-details";
import { PILLARS, WhyUsSection } from "@/components/home/sections";
import { JsonLd } from "@/components/seo/json-ld";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { pageMetadata } from "@/lib/seo";
import { paragraphs } from "@/lib/text";
import { listServices } from "@/services/agency.service";
import { getSiteSettings } from "@/services/site.service";

export async function generateMetadata({ params }: PageProps<"/[locale]/a-propos">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "About" });
  return pageMetadata({ locale, path: "/a-propos", title: t("title"), description: t("metaDescription") });
}

/** Présentation de l'agence : texte saisi dans l'administration, équipe, engagements, coordonnées. */
export default async function AboutPage({ params }: PageProps<"/[locale]/a-propos">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const [t, tHome, settings, services] = await Promise.all([
    getTranslations("About"),
    getTranslations("Home"),
    getSiteSettings(),
    listServices().catch(() => []),
  ]);
  // Texte de l'agence (administration), sinon la présentation de l'accueil.
  const story = paragraphs(settings.about_content);

  return (
    <>
      {settings.agency_name && (
        <JsonLd
          data={{
            "@context": "https://schema.org",
            "@type": "AboutPage",
            name: t("title"),
            mainEntity: { ...travelAgencyJsonLd(settings), slogan: settings.slogan || undefined },
          }}
        />
      )}
      <PageHeader title={t("title")} description={settings.slogan || t("intro")} breadcrumbs={[{ label: t("title") }]} />

      <Section aria-labelledby="about-story">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <Image
            src="/images/equipe-impact-voyage.jpg"
            alt={tHome("teamAlt")}
            width={1080}
            height={810}
            priority
            sizes="(min-width: 1024px) 50vw, 100vw"
            className="rounded-3xl object-cover shadow-xl"
          />
          <div className="flex flex-col gap-5">
            <p className="text-sm font-semibold uppercase tracking-wider text-sunset-700">{tHome("aboutEyebrow")}</p>
            <h2 id="about-story" className="text-balance text-3xl font-bold text-ocean-900 sm:text-4xl">
              {settings.agency_name || tHome("aboutTitle")}
            </h2>
            {(story.length ? story : [tHome("aboutText")]).map((p, i) => (
              <p key={i} className="text-lg leading-relaxed text-ocean-950/90">
                {p}
              </p>
            ))}
          </div>
        </div>
        <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {PILLARS.map(({ key, icon: Icon }) => (
            <li key={key} className="flex flex-col gap-3 rounded-2xl border bg-card p-5">
              <Icon aria-hidden="true" className="size-8 text-sunset-600" />
              <h3 className="font-semibold text-ocean-950">{tHome(`${key}Title`)}</h3>
              <p className="text-sm text-muted-foreground">{tHome(`${key}Text`)}</p>
            </li>
          ))}
        </ul>
      </Section>

      <WhyUsSection />

      {services.length > 0 && (
        <Section tone="tint" aria-labelledby="about-services">
          <SectionHeader id="about-services" eyebrow={t("servicesEyebrow")} title={t("servicesTitle")} href="/services" linkLabel={t("allServices")} />
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {services.map((service) => (
              <li key={service.id}>
                <Link
                  href={`/services#${service.slug}`}
                  className="flex items-center gap-3 rounded-2xl border bg-card p-4 font-semibold text-ocean-950 transition-colors hover:border-ocean-300 hover:bg-ocean-50"
                >
                  <ServiceIcon name={service.icon} className="size-6 shrink-0 text-ocean-600" />
                  {service.title}
                </Link>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Container className="py-16 sm:py-20">
        <section aria-labelledby="about-visit" className="grid gap-8 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5 sm:p-10 lg:grid-cols-2">
          <div className="flex flex-col gap-4">
            <h2 id="about-visit" className="text-3xl font-bold text-ocean-900">
              {t("visitTitle")}
            </h2>
            <p className="text-lg text-ocean-950/90">{t("visitText")}</p>
            <div className="flex flex-wrap gap-3">
              <Link href="/contact" className={buttonVariants({ size: "lg" })}>
                {t("contactUs")}
              </Link>
              <Link href="/devis" className={buttonVariants({ variant: "cta", size: "lg" })}>
                {t("askQuote")}
              </Link>
            </div>
          </div>
          <AgencyDetails settings={settings} />
        </section>
      </Container>
    </>
  );
}
