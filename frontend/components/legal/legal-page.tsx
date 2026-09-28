import { getTranslations } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { RichText } from "@/components/common/rich-text";
import { Link } from "@/i18n/navigation";
import { getSiteSettings } from "@/services/site.service";

export type LegalDocument = "notice" | "privacy" | "terms";

const PATHS: Record<LegalDocument, string> = {
  notice: "/mentions-legales",
  privacy: "/confidentialite",
  terms: "/conditions-generales",
};

/**
 * Page légale (mentions, confidentialité, conditions générales) : sections
 * traduites (espace « Legal »), coordonnées de l'agence reprises des
 * paramètres du site, sommaire et liens vers les autres documents.
 */
export async function LegalPage({ document }: { document: LegalDocument }) {
  const [t, settings] = await Promise.all([getTranslations("Legal"), getSiteSettings()]);
  const values = {
    agency: settings.agency_name || "Impact Voyage",
    address: settings.address || "—",
    email: settings.email || "—",
    phone: settings.phone || "—",
  };
  // Sections s1, s2… dans l'ordre du fichier de traduction (clés construites : typage relâché).
  const keys = Object.keys(t.raw(`${document}.sections`) as Record<string, unknown>);
  const section = t as unknown as (key: string, params: typeof values) => string;
  const sections = keys.map((key, i) => ({
    id: `section-${i + 1}`,
    title: section(`${document}.sections.${key}.title`, values),
    body: section(`${document}.sections.${key}.body`, values),
  }));
  const others = (Object.keys(PATHS) as LegalDocument[]).filter((d) => d !== document);

  return (
    <>
      <PageHeader title={t(`${document}.title`)} description={t(`${document}.intro`, values)} breadcrumbs={[{ label: t(`${document}.title`) }]} />
      <Container className="grid gap-10 py-10 sm:py-14 lg:grid-cols-[16rem_minmax(0,1fr)] lg:gap-14">
        <nav aria-labelledby="legal-toc" className="lg:sticky lg:top-24 lg:self-start">
          <h2 id="legal-toc" className="mb-3 text-sm font-semibold uppercase tracking-wider text-sunset-700">
            {t("toc")}
          </h2>
          <ol className="flex flex-col gap-2 text-sm">
            {sections.map((section, i) => (
              <li key={section.id}>
                <a href={`#${section.id}`} className="text-ocean-900 hover:underline">
                  {i + 1}. {section.title}
                </a>
              </li>
            ))}
          </ol>
        </nav>
        <div className="flex max-w-3xl flex-col gap-10">
          {sections.map((section, i) => (
            <section key={section.id} id={section.id} aria-labelledby={`${section.id}-title`} className="flex scroll-mt-28 flex-col gap-4">
              <h2 id={`${section.id}-title`} className="text-2xl font-bold text-ocean-900">
                {i + 1}. {section.title}
              </h2>
              <RichText text={section.body} className="text-base" />
            </section>
          ))}
          <p className="text-sm text-muted-foreground">{t("updated", { date: t("updatedDate") })}</p>
          <nav aria-label={t("otherDocuments")} className="flex flex-wrap gap-x-6 gap-y-2 border-t pt-6 text-sm font-semibold">
            {others.map((other) => (
              <Link key={other} href={PATHS[other]} className="text-ocean-700 hover:underline">
                {t(`${other}.title`)}
              </Link>
            ))}
          </nav>
        </div>
      </Container>
    </>
  );
}

export async function legalMetadata(document: LegalDocument, locale: string) {
  const t = await getTranslations({ locale, namespace: "Legal" });
  return { title: t(`${document}.title`), description: t(`${document}.metaDescription`), path: PATHS[document] };
}
