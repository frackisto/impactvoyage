import { CalendarDaysIcon, ClockIcon, HeadsetIcon, ShieldCheckIcon, WalletIcon } from "lucide-react";
import type { Metadata } from "next";
import Image from "next/image";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { SocialIcon } from "@/components/common/social-icons";
import { QuoteForm } from "@/components/quotes/quote-form";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { formatDate } from "@/lib/format";
import { mediaSrc } from "@/lib/media";
import { alternates } from "@/lib/seo";
import { cn } from "@/lib/utils";
import { allDestinations } from "@/services/destinations.service";
import { quotePrefill, type QuoteContext } from "@/services/quotes.service";
import { getSiteSettings, whatsappUrl } from "@/services/site.service";

type Props = PageProps<"/[locale]/devis">;

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Quote" });
  return {
    title: t("title"),
    description: t("metaDescription"),
    alternates: alternates("/devis", locale),
    // Seule la page sans préremplissage est indexée.
    robots: Object.keys(query).length ? { index: false, follow: true } : undefined,
  };
}

/** Demande de devis (CdC § 18), préremplie depuis la fiche d'origine. */
export default async function QuotePage({ params, searchParams }: Props) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const [t, { values, context }, destinations, settings] = await Promise.all([
    getTranslations("Quote"),
    quotePrefill(query),
    allDestinations().catch(() => []),
    getSiteSettings(),
  ]);
  const whatsapp = whatsappUrl(settings.whatsapp);

  return (
    <>
      <PageHeader title={t("title")} description={t("intro")} breadcrumbs={[{ label: t("title") }]} />
      <Container className="grid gap-10 py-10 sm:py-14 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <div className="flex flex-col gap-8">
          {context && <ContextCard context={context} />}
          <QuoteForm destinations={destinations.map(({ slug, name }) => ({ slug, name }))} initial={values} />
        </div>

        <aside aria-labelledby="quote-why" className="flex flex-col gap-6 lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-4 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <h2 id="quote-why" className="text-xl font-bold text-ocean-900">
              {t("whyTitle")}
            </h2>
            <ul className="flex flex-col gap-3 text-sm text-ocean-950">
              {[
                { icon: ClockIcon, text: t("why1") },
                { icon: WalletIcon, text: t("why2") },
                { icon: ShieldCheckIcon, text: t("why3") },
                { icon: HeadsetIcon, text: t("why4") },
              ].map(({ icon: Icon, text }) => (
                <li key={text} className="flex gap-3">
                  <Icon aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-sunset-600" />
                  {text}
                </li>
              ))}
            </ul>
          </div>
          {(settings.phone || whatsapp) && (
            <div className="flex flex-col gap-3 rounded-3xl bg-ocean-900 p-6 text-white">
              <p className="font-heading text-lg font-bold">{t("preferTalking")}</p>
              {settings.phone && (
                <a href={`tel:${settings.phone.replace(/\s/g, "")}`} className={cn(buttonVariants({ variant: "inverse" }), "w-full")}>
                  {settings.phone}
                </a>
              )}
              {whatsapp && (
                <a
                  href={whatsapp}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(buttonVariants({ variant: "outline" }), "w-full border-white/40 bg-transparent text-white hover:bg-white/10 hover:text-white")}
                >
                  <SocialIcon network="whatsapp" className="size-5" />
                  WhatsApp
                </a>
              )}
            </div>
          )}
        </aside>
      </Container>
    </>
  );
}

/** Résumé de l'objet d'origine (circuit, hôtel, véhicule...) repris dans la demande. */
async function ContextCard({ context }: { context: QuoteContext }) {
  const [t, locale] = await Promise.all([getTranslations("Quote"), getLocale()]);
  const date = (value: string) => formatDate(`${value}T00:00:00Z`, locale, { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const image = mediaSrc(context.image);
  const details = [
    context.start && context.end ? t("period", { start: date(context.start), end: date(context.end) }) : context.start ? date(context.start) : null,
    context.room ?? null,
    context.rooms && context.rooms > 1 ? t("roomsCount", { count: context.rooms }) : null,
    context.travelers ? t("travelersCount", { count: context.travelers }) : null,
    context.participants ? t("participantsCount", { count: context.participants }) : null,
  ].filter(Boolean);

  return (
    <section aria-labelledby="quote-context" className="flex items-center gap-4 rounded-3xl border bg-ocean-50/70 p-4">
      {image && (
        <span className="relative size-20 shrink-0 overflow-hidden rounded-2xl sm:h-24 sm:w-32">
          <Image src={image} alt="" fill sizes="128px" className="object-cover" />
        </span>
      )}
      <div className="flex min-w-0 flex-col gap-1">
        <p className="text-xs font-semibold uppercase tracking-wider text-sunset-700">{t(`contextKind.${context.kind}`)}</p>
        <h2 id="quote-context" className="text-lg font-bold text-ocean-900">
          <Link href={context.href} className="hover:underline">
            {context.title}
          </Link>
        </h2>
        {details.length > 0 && (
          <p className="flex flex-wrap items-center gap-x-3 text-sm text-ocean-950">
            <CalendarDaysIcon aria-hidden="true" className="size-4 text-ocean-600" />
            {details.join(" · ")}
          </p>
        )}
      </div>
    </section>
  );
}
