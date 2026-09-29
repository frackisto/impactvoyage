import { BedDoubleIcon, CheckIcon, MapPinIcon, UsersIcon } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { AmenityList } from "@/components/accommodations/amenity-list";
import { ResidenceCard } from "@/components/accommodations/stay-cards";
import { StayForm } from "@/components/accommodations/stay-form";
import { AvailabilityCalendar } from "@/components/booking/availability-calendar";
import { PeriodAvailability } from "@/components/booking/period-availability";
import { Container } from "@/components/common/container";
import { ImmersiveHero } from "@/components/common/immersive-hero";
import { Section, SectionHeader } from "@/components/common/page-section";
import { Price } from "@/components/common/price";
import { SocialIcon } from "@/components/common/social-icons";
import { Gallery } from "@/components/media/gallery";
import { breadcrumbList, JsonLd } from "@/components/seo/json-ld";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { countryFlag } from "@/lib/countries";
import { mediaSrc } from "@/lib/media";
import { pageHref } from "@/lib/pagination";
import { absoluteUrl, pageMetadata, SITE_URL } from "@/lib/seo";
import { addDays, parseStay, stayQuery, today } from "@/lib/stay";
import { excerpt, paragraphs } from "@/lib/text";
import { cn } from "@/lib/utils";
import { getResidence, relatedResidences, residenceAvailability } from "@/services/accommodations.service";
import { getSiteSettings, whatsappUrl } from "@/services/site.service";
import type { ResidenceDetail } from "@/types";

type Props = PageProps<"/[locale]/residences/[slug]">;

function summary(residence: ResidenceDetail) {
  return excerpt(residence.short_description || residence.description);
}

const lines = (text?: string) => (text ?? "").split("\n").map((l) => l.replace(/^[-•\s]+/, "").trim()).filter(Boolean);

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  const residence = await getResidence(slug);
  if (!residence) notFound();
  return pageMetadata({
    locale,
    path: `/residences/${slug}`,
    title: residence.name,
    description: summary(residence),
    image: mediaSrc(residence.cover_image),
    imageAlt: residence.cover_alt || residence.name,
  });
}

export default async function ResidencePage({ params, searchParams }: Props) {
  const [{ locale, slug }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const residence = await getResidence(slug);
  if (!residence) notFound();

  const stay = parseStay(query);
  const [t, tNav, availability, calendar, related, settings] = await Promise.all([
    getTranslations("Stays"),
    getTranslations("Nav"),
    residenceAvailability(slug, stay),
    // Calendrier : périodes réservées sur les deux prochains mois.
    residenceAvailability(slug, { start: today(), end: addDays(today(), 62) }),
    relatedResidences(residence),
    getSiteSettings(),
  ]);

  const breadcrumbs = [
    { label: t("hotels.title"), href: "/hotels" },
    { label: t("residences.title"), href: "/residences" },
    { label: residence.name },
  ];
  const price = residence.promo_price ?? residence.price_per_night;
  const whatsapp = whatsappUrl(settings.whatsapp);
  const periodQuery = { residence: residence.slug, ...stayQuery({ start: stay.start, end: stay.end }) };
  const quoteHref = pageHref("/devis", periodQuery, 1);
  const bookHref = pageHref("/reservation", periodQuery, 1);
  const image = mediaSrc(residence.cover_image);
  const services = lines(residence.services);

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "LodgingBusiness",
              name: residence.name,
              description: summary(residence),
              url: absoluteUrl(`/residences/${slug}`, locale),
              image: image ? `${SITE_URL}${image}` : undefined,
              address: {
                "@type": "PostalAddress",
                streetAddress: residence.address || undefined,
                addressLocality: residence.destination.city || residence.destination.name,
                addressCountry: residence.destination.country_code,
              },
              numberOfRooms: residence.rooms_count,
              amenityFeature: residence.amenities.map((a) => ({ "@type": "LocationFeatureSpecification", name: a.name, value: true })),
              priceRange: price ? `${Number(price.amount)} ${price.currency}` : undefined,
            },
            breadcrumbList([{ label: tNav("home"), href: "/" }, ...breadcrumbs], `/residences/${slug}`, locale),
          ],
        }}
      />

      <ImmersiveHero
        image={residence.cover_image}
        imageAlt={residence.cover_alt || residence.name}
        breadcrumbs={breadcrumbs}
        badge={
          <>
            <MapPinIcon aria-hidden="true" className="size-4 text-sunset-300" />
            {countryFlag(residence.destination.country_code)} {residence.destination.name} · {t("residences.short")}
          </>
        }
        title={residence.name}
        subtitle={residence.short_description}
      >
        <ul className="flex flex-wrap gap-2 text-sm font-semibold">
          <li className="inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1 text-ocean-900">
            <BedDoubleIcon aria-hidden="true" className="size-4" /> {t("bedrooms", { count: residence.rooms_count })}
          </li>
          <li className="inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1 text-ocean-900">
            <UsersIcon aria-hidden="true" className="size-4" /> {t("guests", { count: residence.capacity })}
          </li>
        </ul>
      </ImmersiveHero>

      <Container className="grid gap-10 py-12 sm:py-16 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <div className="flex flex-col gap-12">
          <section aria-labelledby="residence-about" className="flex flex-col gap-4">
            <h2 id="residence-about" className="text-3xl font-bold text-ocean-900">
              {t("about")}
            </h2>
            <div className="flex flex-col gap-4 text-lg leading-relaxed text-ocean-950/90">
              {paragraphs(residence.description).map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>
          </section>

          {residence.amenities.length > 0 && (
            <section aria-labelledby="residence-amenities" className="flex flex-col gap-4">
              <h2 id="residence-amenities" className="text-2xl font-bold text-ocean-900">
                {t("amenities")}
              </h2>
              <AmenityList amenities={residence.amenities} />
            </section>
          )}

          {services.length > 0 && (
            <section aria-labelledby="residence-services" className="flex flex-col gap-4">
              <h2 id="residence-services" className="text-2xl font-bold text-ocean-900">
                {t("services")}
              </h2>
              <ul className="grid gap-2 sm:grid-cols-2">
                {services.map((service) => (
                  <li key={service} className="flex gap-2.5 text-ocean-950">
                    <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald-700">
                      <CheckIcon aria-hidden="true" className="size-3.5" />
                    </span>
                    {service}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section id="disponibilites" aria-labelledby="residence-availability" className="flex scroll-mt-24 flex-col gap-5">
            <h2 id="residence-availability" className="text-3xl font-bold text-ocean-900">
              {t("availabilityTitle")}
            </h2>
            <StayForm pathname={`/residences/${slug}`} current={stay} />
            {stay.start && stay.end && (
              <PeriodAvailability
                availability={availability}
                start={stay.start}
                end={stay.end}
                unitPrice={price}
                unit="night"
                bookHref={bookHref}
                requestHref={quoteHref}
              />
            )}
            <AvailabilityCalendar booked={calendar?.booked_periods ?? []} from={today()} />
          </section>

          {residence.conditions && (
            <section aria-labelledby="residence-conditions" className="flex flex-col gap-2 rounded-2xl border border-sunset-200 bg-sunset-50 p-6">
              <h2 id="residence-conditions" className="text-xl font-bold text-ocean-900">
                {t("conditions")}
              </h2>
              {paragraphs(residence.conditions).map((p, i) => (
                <p key={i} className="text-ocean-950">
                  {p}
                </p>
              ))}
            </section>
          )}
        </div>

        <aside aria-labelledby="residence-booking" className="lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-5 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <h2 id="residence-booking" className="text-xl font-bold text-ocean-900">
              {t("bookStay")}
            </h2>
            {residence.promo_price ? (
              <div className="flex flex-col">
                <Price value={residence.price_per_night} strikethrough />
                <Price value={residence.promo_price} unit="night" />
              </div>
            ) : (
              <Price value={residence.price_per_night} unit="night" />
            )}
            {residence.address && (
              <p className="flex gap-2 text-sm text-ocean-950">
                <MapPinIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-ocean-600" />
                {residence.address}
              </p>
            )}
            <div className="flex flex-col gap-2">
              <a href="#disponibilites" className={cn(buttonVariants({ variant: "cta", size: "lg" }), "w-full")}>
                {t("seeAvailability")}
              </a>
              <Link href={quoteHref} className={cn(buttonVariants({ variant: "outline", size: "lg" }), "w-full")}>
                {t("quote")}
              </Link>
              {whatsapp && (
                <a
                  href={`${whatsapp}?text=${encodeURIComponent(t("whatsappMessage", { name: residence.name }))}`}
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

      {residence.images.length > 0 && (
        <Section tone="tint" aria-labelledby="residence-gallery">
          <SectionHeader id="residence-gallery" eyebrow={t("galleryEyebrow")} title={t("galleryTitle", { name: residence.name })} />
          <Gallery
            title={residence.name}
            photos={residence.images.map((img) => ({ id: img.id, image: img.image, alt: img.alt_text || residence.name }))}
          />
        </Section>
      )}

      {related.length > 0 && (
        <Section aria-labelledby="residence-related">
          <SectionHeader
            id="residence-related"
            eyebrow={t("relatedEyebrow")}
            title={t("relatedTitle")}
            href="/residences"
            linkLabel={t("allResidences")}
          />
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((other) => (
              <li key={other.id} className="grid">
                <ResidenceCard residence={other} stay={stayQuery({ start: stay.start, end: stay.end })} />
              </li>
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}
