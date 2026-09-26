import { MapPinIcon } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { AmenityList } from "@/components/accommodations/amenity-list";
import { RoomList } from "@/components/accommodations/room-list";
import { Stars } from "@/components/accommodations/stars";
import { HotelCard } from "@/components/accommodations/stay-cards";
import { StayForm } from "@/components/accommodations/stay-form";
import { Container } from "@/components/common/container";
import { ImmersiveHero } from "@/components/common/immersive-hero";
import { Section, SectionHeader } from "@/components/common/page-section";
import { Price } from "@/components/common/price";
import { SocialIcon } from "@/components/common/social-icons";
import { Gallery } from "@/components/media/gallery";
import { ReviewList } from "@/components/reviews/review-list";
import { breadcrumbList, JsonLd } from "@/components/seo/json-ld";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { countryFlag } from "@/lib/countries";
import { mediaSrc } from "@/lib/media";
import { pageHref } from "@/lib/pagination";
import { absoluteUrl, alternates, SITE_URL } from "@/lib/seo";
import { parseStay, stayQuery } from "@/lib/stay";
import { excerpt, paragraphs } from "@/lib/text";
import { cn } from "@/lib/utils";
import { getHotel, hotelAvailability, hotelReviews, relatedHotels } from "@/services/accommodations.service";
import { getSiteSettings, whatsappUrl } from "@/services/site.service";
import type { HotelDetail } from "@/types";

type Props = PageProps<"/[locale]/hotels/[slug]">;

function summary(hotel: HotelDetail) {
  return excerpt(hotel.short_description || hotel.description);
}

/** Chambre la moins chère (prix « à partir de » par nuit). */
function cheapest(hotel: HotelDetail) {
  return [...hotel.rooms]
    .filter((room) => room.price_per_night)
    .sort((a, b) => Number(a.price_per_night!.amount) - Number(b.price_per_night!.amount))[0]?.price_per_night;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  const hotel = await getHotel(slug);
  if (!hotel) notFound();
  const image = mediaSrc(hotel.cover_image);
  return {
    title: hotel.name,
    description: summary(hotel),
    alternates: alternates(`/hotels/${slug}`, locale),
    openGraph: {
      type: "website",
      title: hotel.name,
      description: summary(hotel),
      url: absoluteUrl(`/hotels/${slug}`, locale),
      images: image ? [{ url: image, alt: hotel.cover_alt || hotel.name }] : undefined,
    },
  };
}

export default async function HotelPage({ params, searchParams }: Props) {
  const [{ locale, slug }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const hotel = await getHotel(slug);
  if (!hotel) notFound();

  const stay = parseStay(query);
  const [t, tNav, availability, reviews, related, settings] = await Promise.all([
    getTranslations("Stays"),
    getTranslations("Nav"),
    hotelAvailability(slug, stay),
    hotelReviews(slug),
    relatedHotels(hotel),
    getSiteSettings(),
  ]);

  const breadcrumbs = [{ label: t("hotels.title"), href: "/hotels" }, { label: hotel.name }];
  const priceFrom = cheapest(hotel);
  const whatsapp = whatsappUrl(settings.whatsapp);
  const quoteHref = pageHref("/devis", { hotel: hotel.slug, ...stayQuery(stay) }, 1);
  const image = mediaSrc(hotel.cover_image);
  const type = t(`type.${hotel.accommodation_type ?? "HOTEL"}`);

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": hotel.accommodation_type === "APARTMENT" ? "LodgingBusiness" : "Hotel",
              name: hotel.name,
              description: summary(hotel),
              url: absoluteUrl(`/hotels/${slug}`, locale),
              image: image ? `${SITE_URL}${image}` : undefined,
              address: {
                "@type": "PostalAddress",
                streetAddress: hotel.address || undefined,
                addressLocality: hotel.destination.city || hotel.destination.name,
                addressCountry: hotel.destination.country_code,
              },
              starRating: hotel.stars ? { "@type": "Rating", ratingValue: hotel.stars } : undefined,
              amenityFeature: hotel.amenities.map((a) => ({ "@type": "LocationFeatureSpecification", name: a.name, value: true })),
              priceRange: priceFrom ? `${Number(priceFrom.amount)} ${priceFrom.currency}` : undefined,
              aggregateRating:
                hotel.rating.count > 0 && hotel.rating.average
                  ? { "@type": "AggregateRating", ratingValue: hotel.rating.average, reviewCount: hotel.rating.count, bestRating: 5 }
                  : undefined,
            },
            breadcrumbList([{ label: tNav("home"), href: "/" }, ...breadcrumbs], `/hotels/${slug}`, locale),
          ],
        }}
      />

      <ImmersiveHero
        image={hotel.cover_image}
        imageAlt={hotel.cover_alt || hotel.name}
        breadcrumbs={breadcrumbs}
        badge={
          <>
            <MapPinIcon aria-hidden="true" className="size-4 text-sunset-300" />
            {countryFlag(hotel.destination.country_code)} {hotel.destination.name} · {type}
          </>
        }
        title={hotel.name}
        subtitle={hotel.short_description}
        rating={hotel.rating}
      >
        {hotel.stars ? (
          <span className="inline-flex w-fit rounded-full bg-white/95 px-3 py-1">
            <Stars count={hotel.stars} />
          </span>
        ) : null}
      </ImmersiveHero>

      <Container className="grid gap-10 py-12 sm:py-16 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <div className="flex flex-col gap-12">
          <section aria-labelledby="hotel-about" className="flex flex-col gap-4">
            <h2 id="hotel-about" className="text-3xl font-bold text-ocean-900">
              {t("about")}
            </h2>
            <div className="flex flex-col gap-4 text-lg leading-relaxed text-ocean-950/90">
              {paragraphs(hotel.description).map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>
          </section>

          {hotel.amenities.length > 0 && (
            <section aria-labelledby="hotel-amenities" className="flex flex-col gap-4">
              <h2 id="hotel-amenities" className="text-2xl font-bold text-ocean-900">
                {t("amenities")}
              </h2>
              <AmenityList amenities={hotel.amenities} />
            </section>
          )}

          <section id="disponibilites" aria-labelledby="hotel-rooms" className="flex scroll-mt-24 flex-col gap-5">
            <h2 id="hotel-rooms" className="text-3xl font-bold text-ocean-900">
              {t("roomsTitle")}
            </h2>
            <StayForm pathname={`/hotels/${slug}`} current={stay} withRooms />
            {stay.start && availability === null && (
              <p role="alert" className="text-sm text-rose-700">
                {t("availabilityError")}
              </p>
            )}
            {hotel.rooms.length > 0 ? (
              <RoomList hotel={hotel} stay={stay} availability={availability} />
            ) : (
              <p className="rounded-2xl bg-ocean-50 p-5 text-ocean-900">{t("noRooms")}</p>
            )}
          </section>
        </div>

        <aside aria-labelledby="hotel-booking" className="lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-5 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <h2 id="hotel-booking" className="text-xl font-bold text-ocean-900">
              {t("bookStay")}
            </h2>
            {priceFrom && <Price value={priceFrom} from unit="night" />}
            {hotel.address && (
              <p className="flex gap-2 text-sm text-ocean-950">
                <MapPinIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-ocean-600" />
                {hotel.address}
              </p>
            )}
            <div className="flex flex-col gap-2">
              <a href="#disponibilites" className={cn(buttonVariants({ variant: "outline", size: "lg" }), "w-full")}>
                {t("seeAvailability")}
              </a>
              <Link href={quoteHref} className={cn(buttonVariants({ variant: "cta", size: "lg" }), "w-full")}>
                {t("quote")}
              </Link>
              {whatsapp && (
                <a
                  href={`${whatsapp}?text=${encodeURIComponent(t("whatsappMessage", { name: hotel.name }))}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(buttonVariants({ variant: "outline", size: "lg" }), "w-full")}
                >
                  <SocialIcon network="whatsapp" className="size-5 text-[#128C7E]" />
                  {t("whatsapp")}
                </a>
              )}
            </div>
          </div>
        </aside>
      </Container>

      {hotel.images.length > 0 && (
        <Section tone="tint" aria-labelledby="hotel-gallery">
          <SectionHeader id="hotel-gallery" eyebrow={t("galleryEyebrow")} title={t("galleryTitle", { name: hotel.name })} />
          <Gallery title={hotel.name} photos={hotel.images.map((img) => ({ id: img.id, image: img.image, alt: img.alt_text || hotel.name }))} />
        </Section>
      )}

      {reviews.length > 0 && (
        <Section aria-labelledby="hotel-reviews">
          <SectionHeader id="hotel-reviews" eyebrow={t("reviewsEyebrow")} title={t("reviewsTitle")} />
          <ReviewList reviews={reviews} />
        </Section>
      )}

      {related.length > 0 && (
        <Section tone="tint" aria-labelledby="hotel-related">
          <SectionHeader id="hotel-related" eyebrow={t("relatedEyebrow")} title={t("relatedTitle")} href="/hotels" linkLabel={t("allHotels")} />
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((other) => (
              <li key={other.id} className="grid">
                <HotelCard hotel={other} stay={stayQuery(stay)} />
              </li>
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}
