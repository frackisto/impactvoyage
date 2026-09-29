import { CalendarIcon, CarIcon, CheckIcon, CogIcon, FuelIcon, SnowflakeIcon, UsersIcon } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

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
import { VehicleCard, vehicleName } from "@/components/vehicles/vehicle-card";
import { Link } from "@/i18n/navigation";
import { mediaSrc } from "@/lib/media";
import { pageHref } from "@/lib/pagination";
import { absoluteUrl, pageMetadata, SITE_URL } from "@/lib/seo";
import { addDays, parseStay, today } from "@/lib/stay";
import { excerpt, paragraphs } from "@/lib/text";
import { cn } from "@/lib/utils";
import { getSiteSettings, whatsappUrl } from "@/services/site.service";
import { getVehicle, relatedVehicles, vehicleAvailability } from "@/services/vehicles.service";
import type { VehicleDetail } from "@/types";

type Props = PageProps<"/[locale]/vehicules/[slug]">;

async function summary(vehicle: VehicleDetail) {
  const t = await getTranslations("Vehicles");
  return excerpt(
    vehicle.description ||
      t("defaultDescription", { name: vehicleName(vehicle), category: t(`category.${vehicle.category}`), seats: vehicle.seats }),
  );
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  const vehicle = await getVehicle(slug);
  if (!vehicle) notFound();
  const t = await getTranslations({ locale, namespace: "Vehicles" });
  return pageMetadata({
    locale,
    path: `/vehicules/${slug}`,
    title: t("metaTitle", { name: vehicleName(vehicle) }),
    description: await summary(vehicle),
    image: mediaSrc(vehicle.cover_image),
    imageAlt: vehicle.cover_alt || vehicleName(vehicle),
  });
}

export default async function VehiclePage({ params, searchParams }: Props) {
  const [{ locale, slug }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const vehicle = await getVehicle(slug);
  if (!vehicle) notFound();

  const period = parseStay(query);
  const [t, tNav, availability, calendar, related, settings, description] = await Promise.all([
    getTranslations("Vehicles"),
    getTranslations("Nav"),
    period.start && period.end ? vehicleAvailability(slug, period.start, period.end) : Promise.resolve(null),
    // Calendrier : périodes réservées sur les deux prochains mois.
    vehicleAvailability(slug, today(), addDays(today(), 62)),
    relatedVehicles(vehicle),
    getSiteSettings(),
    summary(vehicle),
  ]);

  const name = vehicleName(vehicle);
  const breadcrumbs = [{ label: t("title"), href: "/vehicules" }, { label: name }];
  const price = vehicle.promo_price ?? vehicle.price_per_day;
  const whatsapp = whatsappUrl(settings.whatsapp);
  const periodQuery = { vehicle: vehicle.slug, start: period.start, end: period.end };
  const requestHref = pageHref("/devis", periodQuery, 1);
  const bookHref = pageHref("/reservation", periodQuery, 1);
  const image = mediaSrc(vehicle.cover_image);

  const specs = [
    { icon: CarIcon, label: t("categoryLabel"), value: t(`category.${vehicle.category}`) },
    { icon: CalendarIcon, label: t("year"), value: String(vehicle.year) },
    { icon: UsersIcon, label: t("seatsLabel"), value: t("seats", { count: vehicle.seats }) },
    { icon: CogIcon, label: t("transmissionLabel"), value: t(`transmission.${vehicle.transmission}`) },
    { icon: FuelIcon, label: t("fuelLabel"), value: t(`fuel.${vehicle.fuel}`) },
    { icon: SnowflakeIcon, label: t("airConditioning"), value: vehicle.air_conditioning ? t("yes") : t("no") },
  ];

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "Car",
              name,
              description,
              url: absoluteUrl(`/vehicules/${slug}`, locale),
              image: image ? `${SITE_URL}${image}` : undefined,
              brand: { "@type": "Brand", name: vehicle.brand },
              model: vehicle.model,
              vehicleModelDate: String(vehicle.year),
              vehicleSeatingCapacity: vehicle.seats,
              vehicleTransmission: t(`transmission.${vehicle.transmission}`),
              fuelType: t(`fuel.${vehicle.fuel}`),
              offers: price
                ? {
                    "@type": "Offer",
                    priceSpecification: {
                      "@type": "UnitPriceSpecification",
                      price: price.amount,
                      priceCurrency: price.currency,
                      unitCode: "DAY",
                    },
                  }
                : undefined,
            },
            breadcrumbList([{ label: tNav("home"), href: "/" }, ...breadcrumbs], `/vehicules/${slug}`, locale),
          ],
        }}
      />

      <ImmersiveHero
        image={vehicle.cover_image}
        imageAlt={vehicle.cover_alt || name}
        breadcrumbs={breadcrumbs}
        badge={
          <>
            <CarIcon aria-hidden="true" className="size-4 text-sunset-300" />
            {t("categoryYear", { category: t(`category.${vehicle.category}`), year: vehicle.year })}
          </>
        }
        title={name}
      >
        <ul className="flex flex-wrap gap-2 text-sm font-semibold">
          <li className="inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1 text-ocean-900">
            <UsersIcon aria-hidden="true" className="size-4" /> {t("seats", { count: vehicle.seats })}
          </li>
          <li className="inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1 text-ocean-900">
            <CogIcon aria-hidden="true" className="size-4" /> {t(`transmission.${vehicle.transmission}`)}
          </li>
          <li className="inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1 text-ocean-900">
            <FuelIcon aria-hidden="true" className="size-4" /> {t(`fuel.${vehicle.fuel}`)}
          </li>
        </ul>
      </ImmersiveHero>

      <Container className="grid gap-10 py-12 sm:py-16 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <div className="flex flex-col gap-12">
          <section aria-labelledby="vehicle-about" className="flex flex-col gap-5">
            <h2 id="vehicle-about" className="text-3xl font-bold text-ocean-900">
              {t("about")}
            </h2>
            {paragraphs(vehicle.description).map((p, i) => (
              <p key={i} className="text-lg leading-relaxed text-ocean-950/90">
                {p}
              </p>
            ))}
            <dl className="grid gap-4 rounded-2xl bg-ocean-50/70 p-5 sm:grid-cols-2 lg:grid-cols-3">
              {specs.map(({ icon: Icon, label, value }) => (
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

          {vehicle.features.length > 0 && (
            <section aria-labelledby="vehicle-features" className="flex flex-col gap-4">
              <h2 id="vehicle-features" className="text-2xl font-bold text-ocean-900">
                {t("features")}
              </h2>
              <ul className="grid gap-2 sm:grid-cols-2">
                {vehicle.features.map((feature) => (
                  <li key={feature} className="flex gap-2.5 text-ocean-950">
                    <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald-700">
                      <CheckIcon aria-hidden="true" className="size-3.5" />
                    </span>
                    {feature}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section id="disponibilites" aria-labelledby="vehicle-availability" className="flex scroll-mt-24 flex-col gap-5">
            <h2 id="vehicle-availability" className="text-3xl font-bold text-ocean-900">
              {t("availabilityTitle")}
            </h2>
            <StayForm pathname={`/vehicules/${slug}`} current={period} labels={{ start: t("pickup"), end: t("dropoff") }} />
            {period.start && period.end && (
              <PeriodAvailability
                availability={availability}
                start={period.start}
                end={period.end}
                unitPrice={price}
                unit="day"
                bookHref={bookHref}
                requestHref={requestHref}
              />
            )}
            <AvailabilityCalendar booked={calendar?.booked_periods ?? []} from={today()} />
          </section>
        </div>

        <aside aria-labelledby="vehicle-booking" className="lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-5 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <h2 id="vehicle-booking" className="text-xl font-bold text-ocean-900">
              {t("bookTitle")}
            </h2>
            {vehicle.promo_price ? (
              <div className="flex flex-col">
                <Price value={vehicle.price_per_day} strikethrough />
                <Price value={vehicle.promo_price} unit="day" />
              </div>
            ) : (
              <Price value={vehicle.price_per_day} unit="day" />
            )}
            <p className="text-sm text-muted-foreground">{t("rentalNote")}</p>
            <div className="flex flex-col gap-2">
              <a href="#disponibilites" className={cn(buttonVariants({ variant: "cta", size: "lg" }), "w-full")}>
                {t("seeAvailability")}
              </a>
              <Link href={requestHref} className={cn(buttonVariants({ variant: "outline", size: "lg" }), "w-full")}>
                {t("request")}
              </Link>
              {whatsapp && (
                <a
                  href={`${whatsapp}?text=${encodeURIComponent(t("whatsappMessage", { name }))}`}
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

      {vehicle.images.length > 0 && (
        <Section tone="tint" aria-labelledby="vehicle-gallery">
          <SectionHeader id="vehicle-gallery" eyebrow={t("galleryEyebrow")} title={t("galleryTitle")} />
          <Gallery title={name} photos={vehicle.images.map((img) => ({ id: img.id, image: img.image, alt: img.alt_text || name }))} />
        </Section>
      )}

      {related.length > 0 && (
        <Section aria-labelledby="vehicle-related">
          <SectionHeader id="vehicle-related" eyebrow={t("relatedEyebrow")} title={t("relatedTitle")} href="/vehicules" linkLabel={t("allVehicles")} />
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((other) => (
              <li key={other.id} className="grid">
                <VehicleCard vehicle={other} period={{ start: period.start, end: period.end }} />
              </li>
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}
