import { CalendarClockIcon, MapPinIcon, TagIcon, UsersIcon } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { ImmersiveHero } from "@/components/common/immersive-hero";
import { OfferBadge, type OfferBadgeCode } from "@/components/common/offer-badge";
import { Section, SectionHeader } from "@/components/common/page-section";
import { Price } from "@/components/common/price";
import { OfferCard } from "@/components/offers/offer-card";
import { breadcrumbList, JsonLd } from "@/components/seo/json-ld";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { formatDate } from "@/lib/format";
import { mediaSrc } from "@/lib/media";
import { absoluteUrl, alternates, SITE_URL } from "@/lib/seo";
import { excerpt, paragraphs } from "@/lib/text";
import { getOffer, relatedOffers } from "@/services/agency.service";
import type { OfferDetail } from "@/types";

type Props = PageProps<"/[locale]/offres/[slug]">;

/** Fiche visée par l'offre (circuit, hôtel...). */
const TARGET_PATHS: Record<string, string> = {
  tour: "/circuits",
  hotel: "/hotels",
  residence: "/residences",
  vehicle: "/vehicules",
  activity: "/activites",
};

function summary(offer: OfferDetail) {
  return excerpt(offer.short_description || offer.description || offer.title);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  const offer = await getOffer(slug);
  if (!offer) notFound();
  const image = mediaSrc(offer.cover_image);
  return {
    title: offer.title,
    description: summary(offer),
    alternates: alternates(`/offres/${slug}`, locale),
    openGraph: {
      title: offer.title,
      description: summary(offer),
      url: absoluteUrl(`/offres/${slug}`, locale),
      images: image ? [{ url: image, alt: offer.cover_alt || offer.title }] : undefined,
    },
  };
}

/** Offre promotionnelle (CdC § 17) : prix, réduction, validité, conditions et demande. */
export default async function OfferPage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const offer = await getOffer(slug);
  if (!offer) notFound();

  const [t, tNav, lang, related] = await Promise.all([getTranslations("Offers"), getTranslations("Nav"), getLocale(), relatedOffers(offer)]);
  const breadcrumbs = [{ label: t("title"), href: "/offres" }, { label: offer.title }];
  const date = (value: string) => formatDate(`${value}T00:00:00Z`, lang, { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const targetPath = offer.target && TARGET_PATHS[offer.target.type];
  const image = mediaSrc(offer.cover_image);

  const facts = [
    { icon: TagIcon, label: t("typeLabel"), value: t(`type.${offer.offer_type}`) },
    offer.destination ? { icon: MapPinIcon, label: t("destination"), value: offer.destination.name } : null,
    { icon: CalendarClockIcon, label: t("validity"), value: t("period", { start: date(offer.start_date), end: date(offer.end_date) }) },
    offer.seats_available != null ? { icon: UsersIcon, label: t("seatsLabel"), value: t("seats", { count: offer.seats_available }) } : null,
  ].filter((fact) => fact !== null);

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "Offer",
              name: offer.title,
              description: summary(offer),
              url: absoluteUrl(`/offres/${slug}`, locale),
              image: image ? `${SITE_URL}${image}` : undefined,
              price: offer.promo_price?.amount,
              priceCurrency: offer.promo_price?.currency,
              validFrom: offer.start_date,
              priceValidUntil: offer.end_date,
              availability: offer.seats_available === 0 ? "https://schema.org/SoldOut" : "https://schema.org/InStock",
            },
            breadcrumbList([{ label: tNav("home"), href: "/" }, ...breadcrumbs], `/offres/${slug}`, locale),
          ],
        }}
      />

      <ImmersiveHero
        image={offer.cover_image}
        imageAlt={offer.cover_alt || offer.title}
        breadcrumbs={breadcrumbs}
        badge={
          <>
            <TagIcon aria-hidden="true" className="size-4 text-sunset-300" />
            {t(`type.${offer.offer_type}`)}
            {offer.destination && ` · ${offer.destination.name}`}
          </>
        }
        title={offer.title}
        subtitle={offer.short_description}
      />

      <Container className="grid gap-10 py-12 sm:py-16 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <div className="flex flex-col gap-10">
          <section aria-labelledby="offer-about" className="flex flex-col gap-5">
            <h2 id="offer-about" className="text-3xl font-bold text-ocean-900">
              {t("about")}
            </h2>
            {paragraphs(offer.description).map((p, i) => (
              <p key={i} className="text-lg leading-relaxed text-ocean-950/90">
                {p}
              </p>
            ))}
            {offer.target && targetPath && (
              <p>
                <Link href={`${targetPath}/${offer.target.slug}`} className="font-semibold text-ocean-700 underline-offset-4 hover:underline">
                  {t("seeTarget", { title: offer.target.title })}
                </Link>
              </p>
            )}
          </section>
          {offer.conditions && (
            <section aria-labelledby="offer-conditions" className="flex flex-col gap-3 rounded-3xl bg-ocean-50/70 p-6">
              <h2 id="offer-conditions" className="text-xl font-bold text-ocean-900">
                {t("conditions")}
              </h2>
              {paragraphs(offer.conditions).map((p, i) => (
                <p key={i} className="text-ocean-950/90">
                  {p}
                </p>
              ))}
            </section>
          )}
        </div>

        <aside aria-labelledby="offer-price" className="lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-5 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <div className="flex flex-wrap items-center gap-2">
              <OfferBadge code={offer.badge as OfferBadgeCode} />
              {offer.discount_percent > 0 && (
                <span className="rounded-4xl bg-sunset-100 px-2 py-0.5 text-xs font-bold text-sunset-800">−{offer.discount_percent} %</span>
              )}
            </div>
            <h2 id="offer-price" className="sr-only">
              {t("priceTitle")}
            </h2>
            <div className="flex flex-col gap-1 text-2xl font-bold text-ocean-900">
              <Price value={offer.initial_price} strikethrough />
              <Price value={offer.promo_price} />
            </div>
            <dl className="flex flex-col gap-3">
              {facts.map(({ icon: Icon, label, value }) => (
                <div key={label} className="flex flex-col gap-0.5">
                  <dt className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Icon aria-hidden="true" className="size-5 shrink-0 text-ocean-600" />
                    {label}
                  </dt>
                  <dd className="ps-7 font-semibold text-ocean-950">{value}</dd>
                </div>
              ))}
            </dl>
            <Link href={`/devis?offer=${encodeURIComponent(offer.slug)}`} className={buttonVariants({ variant: "cta", size: "lg" })}>
              {t("book")}
            </Link>
          </div>
        </aside>
      </Container>

      {related.length > 0 && (
        <Section tone="tint" aria-labelledby="offer-related">
          <SectionHeader id="offer-related" eyebrow={t("relatedEyebrow")} title={t("relatedTitle")} href="/offres" linkLabel={t("allOffers")} />
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((other) => (
              <li key={other.id} className="grid">
                <OfferCard offer={other} />
              </li>
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}
