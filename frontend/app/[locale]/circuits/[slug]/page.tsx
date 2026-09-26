import {
  BusIcon,
  CheckIcon,
  ClockIcon,
  HotelIcon,
  MapPinIcon,
  TagIcon,
  UsersIcon,
  XIcon,
} from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { ContentCard } from "@/components/common/content-card";
import { Container } from "@/components/common/container";
import { ImmersiveHero } from "@/components/common/immersive-hero";
import { Section, SectionHeader } from "@/components/common/page-section";
import { Price } from "@/components/common/price";
import { Gallery } from "@/components/media/gallery";
import { ReviewList } from "@/components/reviews/review-list";
import { breadcrumbList, JsonLd } from "@/components/seo/json-ld";
import { TourBookingCard } from "@/components/tours/tour-booking-card";
import { TourCard } from "@/components/tours/tour-card";
import { buttonVariants } from "@/components/ui/button";

import { countryFlag } from "@/lib/countries";
import { mediaSrc } from "@/lib/media";
import { absoluteUrl, alternates, SITE_URL } from "@/lib/seo";
import { excerpt, paragraphs } from "@/lib/text";
import { getSiteSettings, whatsappUrl } from "@/services/site.service";
import { getTour, relatedTours, SCOPE_PATHS, tourReviews } from "@/services/tours.service";
import type { TourDetail } from "@/types";

type Props = PageProps<"/[locale]/circuits/[slug]">;

const SCOPE_KEY = { NATIONAL: "national", INTERNATIONAL: "international" } as const;

function summary(tour: TourDetail) {
  return excerpt(tour.short_description || tour.description);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  const tour = await getTour(slug);
  if (!tour) notFound();
  const image = mediaSrc(tour.cover_image);
  return {
    title: tour.title,
    description: summary(tour),
    alternates: alternates(`/circuits/${slug}`, locale),
    openGraph: {
      type: "website",
      title: tour.title,
      description: summary(tour),
      url: absoluteUrl(`/circuits/${slug}`, locale),
      images: image ? [{ url: image, alt: tour.cover_alt || tour.title }] : undefined,
    },
  };
}

/** Données structurées TouristTrip : programme, départs (offres) et note. */
function tripJsonLd(tour: TourDetail, locale: string, agency: string | undefined) {
  const image = mediaSrc(tour.cover_image);
  return {
    "@type": "TouristTrip",
    name: tour.title,
    description: summary(tour),
    url: absoluteUrl(`/circuits/${tour.slug}`, locale),
    image: image ? `${SITE_URL}${image}` : undefined,
    touristType: tour.theme?.name,
    provider: agency ? { "@type": "TravelAgency", name: agency, url: SITE_URL } : undefined,
    itinerary: tour.days.length
      ? {
          "@type": "ItemList",
          numberOfItems: tour.days.length,
          itemListElement: tour.days.map((day) => ({ "@type": "ListItem", position: day.day_number, name: day.title })),
        }
      : undefined,
    offers: tour.departures
      .filter((departure) => departure.price)
      .map((departure) => ({
        "@type": "Offer",
        price: departure.price!.amount,
        priceCurrency: departure.price!.currency,
        availability: departure.seats_left > 5 ? "https://schema.org/InStock" : "https://schema.org/LimitedAvailability",
        availabilityStarts: departure.start_date,
        url: absoluteUrl(`/circuits/${tour.slug}`, locale),
      })),
    aggregateRating:
      tour.rating.count > 0 && tour.rating.average
        ? { "@type": "AggregateRating", ratingValue: tour.rating.average, reviewCount: tour.rating.count, bestRating: 5 }
        : undefined,
  };
}

export default async function TourPage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const tour = await getTour(slug);
  if (!tour) notFound();

  const [t, tNav, reviews, related, settings] = await Promise.all([
    getTranslations("Tours"),
    getTranslations("Nav"),
    tourReviews(slug),
    relatedTours(tour),
    getSiteSettings(),
  ]);

  const scope = SCOPE_KEY[tour.scope];
  const breadcrumbs = [{ label: t(`${scope}.title`), href: SCOPE_PATHS[tour.scope] }, { label: tour.title }];
  const whatsapp = whatsappUrl(settings.whatsapp);
  const min = tour.min_travelers ?? 1;
  const group =
    tour.max_travelers && tour.max_travelers !== min
      ? t("groupRange", { min, max: tour.max_travelers })
      : t("groupMin", { count: min });

  const facts = [
    { icon: ClockIcon, label: t("duration"), value: t("days", { count: tour.duration_days }) },
    { icon: MapPinIcon, label: t("departFrom"), value: tour.departure_points.join(" · ") || null },
    { icon: UsersIcon, label: t("group"), value: group },
    { icon: BusIcon, label: t("transport"), value: tour.transport_info || null },
    { icon: HotelIcon, label: t("accommodation"), value: tour.accommodation_info || null },
  ].filter((fact) => fact.value);

  return (
    <div className="pb-20 lg:pb-0">
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            tripJsonLd(tour, locale, settings.agency_name),
            breadcrumbList([{ label: tNav("home"), href: "/" }, ...breadcrumbs], `/circuits/${slug}`, locale),
          ],
        }}
      />

      <ImmersiveHero
        image={tour.cover_image}
        imageAlt={tour.cover_alt || tour.title}
        breadcrumbs={breadcrumbs}
        badge={
          <>
            <MapPinIcon aria-hidden="true" className="size-4 text-sunset-300" />
            {countryFlag(tour.destination.country_code)} {tour.destination.name} · {t(`${scope}.short`)}
          </>
        }
        title={tour.title}
        subtitle={tour.short_description}
        rating={tour.rating}
      >
        <ul className="flex flex-wrap gap-2 text-sm font-semibold">
          <li className="inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1 text-ocean-900">
            <ClockIcon aria-hidden="true" className="size-4" /> {t("days", { count: tour.duration_days })}
          </li>
          {tour.theme && (
            <li className="inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1 text-ocean-900">
              <TagIcon aria-hidden="true" className="size-4" /> {tour.theme.name}
            </li>
          )}
          {tour.is_custom && <li className="rounded-full bg-cta px-3 py-1 text-cta-foreground">{t("custom")}</li>}
        </ul>
      </ImmersiveHero>

      <Container className="grid gap-10 py-12 sm:py-16 lg:grid-cols-[minmax(0,1fr)_24rem] lg:gap-14">
        <div className="flex flex-col gap-12">
          <section aria-labelledby="tour-about" className="flex flex-col gap-4">
            <h2 id="tour-about" className="text-3xl font-bold text-ocean-900">
              {t("about")}
            </h2>
            <div className="flex flex-col gap-4 text-lg leading-relaxed text-ocean-950/90">
              {paragraphs(tour.description).map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>
            <dl className="mt-2 grid gap-4 rounded-2xl bg-ocean-50/70 p-5 sm:grid-cols-2">
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
          </section>

          {tour.days.length > 0 && (
            <section aria-labelledby="tour-program" className="flex flex-col gap-6">
              <h2 id="tour-program" className="text-3xl font-bold text-ocean-900">
                {t("program")}
              </h2>
              <ol className="relative flex flex-col gap-6 border-s-2 border-ocean-100 ps-8">
                {tour.days.map((day) => (
                  <li key={day.day_number} className="relative">
                    <span
                      aria-hidden="true"
                      className="absolute -start-[calc(3.25rem+1px)] top-0 flex size-10 items-center justify-center rounded-full bg-ocean-600 text-sm font-bold text-white ring-4 ring-background"
                    >
                      {day.day_number}
                    </span>
                    <h3 className="text-lg font-semibold text-ocean-950">
                      <span className="text-sunset-700">{t("day", { number: day.day_number })}</span> — {day.title}
                    </h3>
                    {day.description && <p className="mt-1 text-ocean-950/80">{day.description}</p>}
                  </li>
                ))}
              </ol>
            </section>
          )}

          {(tour.inclusions.length > 0 || tour.exclusions.length > 0) && (
            <section aria-labelledby="tour-included" className="flex flex-col gap-4">
              <h2 id="tour-included" className="text-3xl font-bold text-ocean-900">
                {t("included")}
              </h2>
              <div className="grid gap-6 sm:grid-cols-2">
                {[
                  { title: t("inclusions"), items: tour.inclusions, icon: CheckIcon, tone: "text-emerald-700 bg-emerald-50" },
                  { title: t("exclusions"), items: tour.exclusions, icon: XIcon, tone: "text-rose-700 bg-rose-50" },
                ].map(({ title, items, icon: Icon, tone }) =>
                  items.length ? (
                    <div key={title} className="flex flex-col gap-3 rounded-2xl border p-5">
                      <h3 className="font-semibold text-ocean-900">{title}</h3>
                      <ul className="flex flex-col gap-2">
                        {items.map((item) => (
                          <li key={item} className="flex gap-2.5 text-ocean-950">
                            <span className={`mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full ${tone}`}>
                              <Icon aria-hidden="true" className="size-3.5" />
                            </span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null,
                )}
              </div>
            </section>
          )}

          {tour.conditions && (
            <section aria-labelledby="tour-conditions" className="flex flex-col gap-2 rounded-2xl border border-sunset-200 bg-sunset-50 p-6">
              <h2 id="tour-conditions" className="text-xl font-bold text-ocean-900">
                {t("conditions")}
              </h2>
              {paragraphs(tour.conditions).map((p, i) => (
                <p key={i} className="text-ocean-950">
                  {p}
                </p>
              ))}
            </section>
          )}
        </div>

        <aside id="reserver" aria-labelledby="tour-booking" className="scroll-mt-24 lg:sticky lg:top-24 lg:self-start">
          <TourBookingCard tour={tour} whatsapp={whatsapp} />
        </aside>
      </Container>

      {tour.images.length > 0 && (
        <Section tone="tint" aria-labelledby="tour-gallery">
          <SectionHeader id="tour-gallery" eyebrow={t("galleryEyebrow")} title={t("galleryTitle")} />
          <Gallery
            title={tour.title}
            photos={tour.images.map((img) => ({ id: img.id, image: img.image, alt: img.alt_text || tour.title }))}
          />
        </Section>
      )}

      {tour.activities.length > 0 && (
        <Section aria-labelledby="tour-activities">
          <SectionHeader id="tour-activities" eyebrow={t("activitiesEyebrow")} title={t("activitiesTitle")} />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {tour.activities.map((activity) => (
              <ContentCard
                key={activity.id}
                href={`/activites/${activity.slug}`}
                title={activity.title}
                description={activity.short_description}
                image={activity.cover_image}
                imageAlt={activity.cover_alt || activity.title}
              />
            ))}
          </div>
        </Section>
      )}

      {reviews.length > 0 && (
        <Section aria-labelledby="tour-reviews">
          <SectionHeader id="tour-reviews" eyebrow={t("reviewsEyebrow")} title={t("reviewsTitle")} />
          <ReviewList reviews={reviews} />
        </Section>
      )}

      {related.length > 0 && (
        <Section tone="tint" aria-labelledby="tour-related">
          <SectionHeader
            id="tour-related"
            eyebrow={t("relatedEyebrow")}
            title={t("relatedTitle")}
            href={SCOPE_PATHS[tour.scope]}
            linkLabel={t(`${scope}.see`)}
          />
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((other) => (
              <li key={other.id} className="grid">
                <TourCard tour={other} />
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Mobile : prix et accès aux dates toujours visibles. */}
      <div className="fixed inset-x-0 bottom-0 z-30 flex items-center justify-between gap-3 border-t bg-background/95 px-4 py-3 backdrop-blur lg:hidden">
        <Price value={tour.promo_price ?? tour.price} from={!tour.promo_price} unit="person" compact />
        <a href="#reserver" className={buttonVariants({ variant: "cta" })}>
          {tour.departures.length ? t("seeDates") : t("quote")}
        </a>
      </div>
    </div>
  );
}
