import {
  CalendarRangeIcon,
  CheckCircle2Icon,
  GlobeIcon,
  LightbulbIcon,
  MapPinIcon,
  StampIcon,
} from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { Section, SectionHeader } from "@/components/common/page-section";
import { Price } from "@/components/common/price";
import { SocialIcon } from "@/components/common/social-icons";
import { DestinationCard } from "@/components/destinations/destination-card";
import { DestinationHero } from "@/components/destinations/destination-hero";
import { DestinationOffers, hasOffers } from "@/components/destinations/destination-offers";
import { Gallery } from "@/components/media/gallery";
import { ReviewList } from "@/components/reviews/review-list";
import { breadcrumbList, JsonLd } from "@/components/seo/json-ld";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { countryFlag, countryName } from "@/lib/countries";
import { mediaSrc } from "@/lib/media";
import { absoluteUrl, alternates, SITE_URL } from "@/lib/seo";
import { cn } from "@/lib/utils";
import {
  allDestinations,
  destinationReviews,
  getDestination,
  visasForCountry,
} from "@/services/destinations.service";
import { getSiteSettings, whatsappUrl } from "@/services/site.service";
import type { DestinationDetail, DestinationList } from "@/types";

type Props = PageProps<"/[locale]/destinations/[slug]">;

/** Paragraphes séparés par une ligne vide dans l'admin. */
function paragraphs(text: string) {
  return text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
}

function summary(destination: DestinationDetail) {
  const text = destination.short_description || destination.description;
  return text.length > 160 ? `${text.slice(0, 157).trimEnd()}…` : text;
}

/** Trois autres destinations, du même continent d'abord. */
function related(current: DestinationDetail, all: DestinationList[]) {
  const others = all.filter((d) => d.slug !== current.slug);
  const sameContinent = others.filter((d) => d.continent === current.continent);
  return [...sameContinent, ...others.filter((d) => d.continent !== current.continent)].slice(0, 3);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  const destination = await getDestination(slug);
  if (!destination) notFound();
  const image = mediaSrc(destination.cover_image);
  return {
    title: destination.name,
    description: summary(destination),
    alternates: alternates(`/destinations/${slug}`, locale),
    openGraph: {
      type: "website",
      title: destination.name,
      description: summary(destination),
      url: absoluteUrl(`/destinations/${slug}`, locale),
      images: image ? [{ url: image, alt: destination.cover_alt || destination.name }] : undefined,
    },
  };
}

export default async function DestinationPage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const destination = await getDestination(slug);
  if (!destination) notFound();

  const [t, tNav, reviews, visas, all, settings] = await Promise.all([
    getTranslations("Destinations"),
    getTranslations("Nav"),
    destinationReviews(slug),
    visasForCountry(destination.country_code),
    allDestinations().catch(() => []),
    getSiteSettings(),
  ]);

  const country = countryName(destination.country_code, locale);
  const continent = t(`continent.${destination.continent}`);
  const breadcrumbs = [
    { label: tNav("destinations"), href: "/destinations" },
    { label: destination.name },
  ];
  const visa = visas.find((v) => v.fees) ?? visas[0];
  const whatsapp = whatsappUrl(settings.whatsapp);
  const quoteHref = `/devis?destination=${encodeURIComponent(destination.slug)}`;
  const others = related(destination, all);
  const image = mediaSrc(destination.cover_image);

  const facts = [
    { icon: MapPinIcon, label: t("countryLabel"), value: `${countryFlag(destination.country_code)} ${country}` },
    destination.city && destination.city !== destination.name
      ? { icon: MapPinIcon, label: t("cityLabel"), value: destination.city }
      : null,
    { icon: GlobeIcon, label: t("continentLabel"), value: continent },
    destination.best_period ? { icon: CalendarRangeIcon, label: t("bestPeriod"), value: destination.best_period } : null,
  ].filter((fact) => fact !== null);

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "TouristDestination",
              name: destination.name,
              description: summary(destination),
              url: absoluteUrl(`/destinations/${slug}`, locale),
              image: image ? `${SITE_URL}${image}` : undefined,
              address: { "@type": "PostalAddress", addressCountry: destination.country_code, addressLocality: destination.city || undefined },
              touristType: destination.tags.map((tag) => tag.name),
              includesAttraction: destination.attractions.map((name) => ({ "@type": "TouristAttraction", name })),
              aggregateRating:
                destination.rating.count > 0 && destination.rating.average
                  ? { "@type": "AggregateRating", ratingValue: destination.rating.average, reviewCount: destination.rating.count, bestRating: 5 }
                  : undefined,
            },
            breadcrumbList([{ label: tNav("home"), href: "/" }, ...breadcrumbs], `/destinations/${slug}`, locale),
          ],
        }}
      />

      <DestinationHero destination={destination} country={`${countryFlag(destination.country_code)} ${country}`} continent={continent} breadcrumbs={breadcrumbs} />

      <Container className="grid gap-10 py-12 sm:py-16 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <div className="flex flex-col gap-10">
          <section aria-labelledby="destination-about" className="flex flex-col gap-4">
            <h2 id="destination-about" className="text-3xl font-bold text-ocean-900">
              {t("discover", { name: destination.name })}
            </h2>
            <div className="flex flex-col gap-4 text-lg leading-relaxed text-ocean-950/90">
              {paragraphs(destination.description).map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>
          </section>

          {destination.attractions.length > 0 && (
            <section aria-labelledby="destination-attractions" className="flex flex-col gap-4">
              <h2 id="destination-attractions" className="text-2xl font-bold text-ocean-900">
                {t("attractions")}
              </h2>
              <ul className="grid gap-3 sm:grid-cols-2">
                {destination.attractions.map((attraction) => (
                  <li key={attraction} className="flex gap-3 rounded-xl border bg-card p-4">
                    <CheckCircle2Icon aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-sunset-600" />
                    <span className="text-ocean-950">{attraction}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {destination.tips && (
            <section aria-labelledby="destination-tips" className="flex gap-4 rounded-2xl border border-sunset-200 bg-sunset-50 p-6">
              <LightbulbIcon aria-hidden="true" className="size-7 shrink-0 text-sunset-600" />
              <div className="flex flex-col gap-2">
                <h2 id="destination-tips" className="text-xl font-bold text-ocean-900">
                  {t("tips")}
                </h2>
                {paragraphs(destination.tips).map((p, i) => (
                  <p key={i} className="text-ocean-950">
                    {p}
                  </p>
                ))}
              </div>
            </section>
          )}

          {destination.tags.length > 0 && (
            <ul aria-label={t("tagsLabel")} className="flex flex-wrap gap-2">
              {destination.tags.map((tag) => (
                <li key={tag.slug} className="rounded-full bg-ocean-50 px-3 py-1 text-sm font-medium text-ocean-800">
                  #{tag.name}
                </li>
              ))}
            </ul>
          )}
        </div>

        <aside aria-labelledby="destination-plan" className="lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-5 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <h2 id="destination-plan" className="text-xl font-bold text-ocean-900">
              {t("planTitle")}
            </h2>
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
            {visa && (
              <Link
                href={`/visa/${visa.country_slug}`}
                className="flex items-center gap-3 rounded-2xl bg-ocean-50 p-4 transition-colors hover:bg-ocean-100"
              >
                <StampIcon aria-hidden="true" className="size-6 shrink-0 text-ocean-700" />
                <span className="flex flex-1 flex-col">
                  <span className="font-semibold text-ocean-900">{t("visaLink", { country })}</span>
                  {visa.fees ? (
                    <span className="text-sm text-muted-foreground">
                      {t("visaFees")} <Price value={visa.fees} compact className="inline-flex" />
                    </span>
                  ) : null}
                </span>
              </Link>
            )}
            <div className="flex flex-col gap-2">
              <Link href={quoteHref} className={cn(buttonVariants({ variant: "cta", size: "lg" }), "w-full")}>
                {t("quote")}
              </Link>
              {whatsapp && (
                <a
                  href={`${whatsapp}?text=${encodeURIComponent(t("whatsappMessage", { name: destination.name }))}`}
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

      {destination.images.length > 0 && (
        <Section tone="tint" aria-labelledby="destination-gallery">
          <SectionHeader id="destination-gallery" eyebrow={t("galleryEyebrow")} title={t("galleryTitle", { name: destination.name })} />
          <Gallery
            title={destination.name}
            photos={destination.images.map((img) => ({ id: img.id, image: img.image, alt: img.alt_text || destination.name }))}
          />
        </Section>
      )}

      {hasOffers(destination) ? (
        <DestinationOffers destination={destination} />
      ) : (
        <section aria-labelledby="destination-custom" className="bg-gradient-to-r from-ocean-700 to-ocean-900 py-14 text-white">
          <Container className="flex flex-col items-center justify-between gap-6 text-center lg:flex-row lg:text-start">
            <div className="flex max-w-2xl flex-col gap-2">
              <h2 id="destination-custom" className="text-3xl font-bold">
                {t("customTitle", { name: destination.name })}
              </h2>
              <p className="text-lg text-ocean-100">{t("customText")}</p>
            </div>
            <Link href={quoteHref} className={buttonVariants({ variant: "cta", size: "lg" })}>
              {t("quote")}
            </Link>
          </Container>
        </section>
      )}

      {reviews.length > 0 && (
        <Section aria-labelledby="destination-reviews">
          <SectionHeader id="destination-reviews" eyebrow={t("reviewsEyebrow")} title={t("reviewsTitle")} />
          <ReviewList reviews={reviews} />
        </Section>
      )}

      {others.length > 0 && (
        <Section tone="tint" aria-labelledby="destination-related">
          <SectionHeader
            id="destination-related"
            eyebrow={t("relatedEyebrow")}
            title={t("relatedTitle")}
            href="/destinations"
            linkLabel={t("allDestinations")}
          />
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {others.map((other) => (
              <li key={other.id} className="grid">
                <DestinationCard destination={other} />
              </li>
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}
