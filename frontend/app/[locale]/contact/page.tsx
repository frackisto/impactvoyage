import { FileTextIcon, StampIcon } from "lucide-react";
import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { AgencyDetails, travelAgencyJsonLd } from "@/components/contact/agency-details";
import { ContactForm } from "@/components/contact/contact-form";
import { JsonLd } from "@/components/seo/json-ld";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { pageMetadata } from "@/lib/seo";
import { cn } from "@/lib/utils";
import { getSiteSettings } from "@/services/site.service";

export async function generateMetadata({ params }: PageProps<"/[locale]/contact">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "Contact" });
  return pageMetadata({ locale, path: "/contact", title: t("title"), description: t("metaDescription") });
}

/** Contact (CdC § 19) : formulaire, coordonnées et horaires de l'agence. */
export default async function ContactPage({ params }: PageProps<"/[locale]/contact">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const [t, settings] = await Promise.all([getTranslations("Contact"), getSiteSettings()]);

  return (
    <>
      {settings.agency_name && <JsonLd data={{ "@context": "https://schema.org", ...travelAgencyJsonLd(settings) }} />}
      <PageHeader title={t("title")} description={t("intro")} breadcrumbs={[{ label: t("title") }]} />
      <Container className="grid gap-10 py-10 sm:py-14 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <ContactForm />
        <aside aria-labelledby="contact-agency" className="flex flex-col gap-6 lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-5 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <h2 id="contact-agency" className="text-xl font-bold text-ocean-900">
              {t("agencyTitle")}
            </h2>
            <AgencyDetails settings={settings} />
          </div>
          <div className="flex flex-col gap-3 rounded-3xl bg-ocean-900 p-6 text-white">
            <p className="font-heading text-lg font-bold">{t("shortcutsTitle")}</p>
            <Link href="/devis" className={cn(buttonVariants({ variant: "cta" }), "w-full")}>
              <FileTextIcon aria-hidden="true" data-icon="inline-start" />
              {t("quoteShortcut")}
            </Link>
            <Link
              href="/visa"
              className={cn(buttonVariants({ variant: "outline" }), "w-full border-white/40 bg-transparent text-white hover:bg-white/10 hover:text-white")}
            >
              <StampIcon aria-hidden="true" data-icon="inline-start" />
              {t("visaShortcut")}
            </Link>
          </div>
        </aside>
      </Container>
    </>
  );
}
