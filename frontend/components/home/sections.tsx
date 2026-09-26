import {
  ArrowRightIcon,
  CalendarDaysIcon,
  CheckCircle2Icon,
  ClockIcon,
  GlobeIcon,
  HeadsetIcon,
  HeartHandshakeIcon,
  MapPinIcon,
  MedalIcon,
  PhoneIcon,
  QuoteIcon,
  RefreshCwIcon,
  UsersIcon,
  WalletIcon,
  ZapIcon,
  type LucideIcon,
} from "lucide-react";
import Image from "next/image";
import { getLocale, getTranslations } from "next-intl/server";

import { Container } from "@/components/common/container";
import { ContentCard } from "@/components/common/content-card";
import { OfferBadge, type OfferBadgeCode } from "@/components/common/offer-badge";
import { Price } from "@/components/common/price";
import { Rating } from "@/components/common/rating";
import { SectionHeading } from "@/components/common/section-heading";
import { ServiceIcon } from "@/components/common/service-icon";
import { SocialIcon } from "@/components/common/social-icons";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { countryFlag, countryName } from "@/lib/countries";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import { whatsappUrl } from "@/services/site.service";
import type {
  DestinationList,
  EventList,
  OfferList,
  ResidenceList,
  Review,
  Service,
  SiteSettings,
  TourList,
  VisaService,
} from "@/types";

function Section({ children, className, tone = "light" }: { children: React.ReactNode; className?: string; tone?: "light" | "tint" }) {
  return (
    <section className={cn("py-16 sm:py-20", tone === "tint" && "bg-ocean-50/60", className)}>
      <Container className="flex flex-col gap-10">{children}</Container>
    </section>
  );
}

function SectionHeader({ eyebrow, title, text, href, linkLabel }: { eyebrow: string; title: string; text?: string; href?: string; linkLabel?: string }) {
  return (
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <SectionHeading eyebrow={eyebrow} title={title} description={text} />
      {href && linkLabel && (
        <Link href={href} className={cn(buttonVariants({ variant: "outline" }), "shrink-0")}>
          {linkLabel}
          <ArrowRightIcon aria-hidden="true" data-icon="inline-end" className="rtl:rotate-180" />
        </Link>
      )}
    </div>
  );
}

const grid = "grid gap-6 sm:grid-cols-2 lg:grid-cols-3";

export async function ServicesSection({ services }: { services: Service[] }) {
  if (!services.length) return null;
  const t = await getTranslations("Home");
  return (
    <Section className="pt-24">
      <SectionHeader eyebrow={t("servicesEyebrow")} title={t("servicesTitle")} text={t("servicesText")} href="/services" linkLabel={t("allServices")} />
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {services.map((service) => (
          <li key={service.id} className="flex gap-4 rounded-2xl border bg-card p-5 transition-shadow hover:shadow-lg hover:shadow-ocean-900/5">
            <span className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-ocean-50 text-ocean-600">
              <ServiceIcon name={service.icon} className="size-6" />
            </span>
            <div className="flex flex-col gap-1">
              <h3 className="text-base font-semibold leading-snug text-ocean-950">{service.title}</h3>
              <p className="line-clamp-3 text-sm text-muted-foreground">{service.short_description}</p>
            </div>
          </li>
        ))}
      </ul>
    </Section>
  );
}

export async function DestinationsSection({ destinations }: { destinations: DestinationList[] }) {
  if (!destinations.length) return null;
  const [t, locale] = await Promise.all([getTranslations("Home"), getLocale()]);
  return (
    <Section tone="tint">
      <SectionHeader eyebrow={t("destinationsEyebrow")} title={t("destinationsTitle")} href="/destinations" linkLabel={t("allDestinations")} />
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {destinations.map((destination, index) => (
          <ContentCard
            key={destination.id}
            href={`/destinations/${destination.slug}`}
            title={destination.name}
            eyebrow={`${countryFlag(destination.country_code)} ${countryName(destination.country_code, locale)}`}
            description={destination.short_description}
            image={destination.cover_image}
            imageAlt={destination.cover_alt || destination.name}
            priority={index === 0}
          />
        ))}
      </div>
    </Section>
  );
}

export async function ToursSection({ tours }: { tours: TourList[] }) {
  if (!tours.length) return null;
  const [t, tSearch, locale] = await Promise.all([getTranslations("Home"), getTranslations("Search"), getLocale()]);
  return (
    <Section>
      <SectionHeader eyebrow={t("toursEyebrow")} title={t("toursTitle")} href="/circuits/nationaux" linkLabel={t("allTours")} />
      <div className={grid}>
        {tours.map((tour) => (
          <ContentCard
            key={tour.id}
            href={`/circuits/${tour.slug}`}
            title={tour.title}
            eyebrow={tour.destination.name}
            description={tour.short_description}
            image={tour.cover_image}
            imageAlt={tour.cover_alt || tour.title}
            meta={
              <>
                <span className="inline-flex items-center gap-1">
                  <ClockIcon aria-hidden="true" className="size-4" /> {tSearch("days", { count: tour.duration_days })}
                </span>
                {tour.next_departure && (
                  <span className="inline-flex items-center gap-1">
                    <CalendarDaysIcon aria-hidden="true" className="size-4" />
                    {formatDate(tour.next_departure, locale, { day: "numeric", month: "short" })}
                  </span>
                )}
                {tour.rating_count > 0 && <Rating value={tour.rating_avg} count={tour.rating_count} />}
              </>
            }
            footer={<Price value={tour.price} from unit="person" />}
          />
        ))}
      </div>
    </Section>
  );
}

export async function OffersSection({ offers }: { offers: OfferList[] }) {
  if (!offers.length) return null;
  const t = await getTranslations("Home");
  return (
    <Section tone="tint">
      <SectionHeader eyebrow={t("offersEyebrow")} title={t("offersTitle")} href="/offres" linkLabel={t("allOffers")} />
      <div className={grid}>
        {offers.map((offer) => (
          <ContentCard
            key={offer.id}
            href={`/offres/${offer.slug}`}
            title={offer.title}
            description={offer.short_description}
            image={offer.cover_image}
            imageAlt={offer.cover_alt || offer.title}
            badges={
              <>
                <OfferBadge code={offer.badge as OfferBadgeCode} />
                {offer.discount_percent > 0 && (
                  <span className="rounded-4xl bg-white px-2 py-0.5 text-xs font-bold text-ocean-900">−{offer.discount_percent} %</span>
                )}
              </>
            }
            footer={
              <span className="flex flex-col">
                <Price value={offer.initial_price} strikethrough />
                <Price value={offer.promo_price} />
              </span>
            }
          />
        ))}
      </div>
    </Section>
  );
}

export async function VisaSection({ visas, services }: { visas: VisaService[]; services: Service[] }) {
  if (!visas.length) return null;
  const [t, locale] = await Promise.all([getTranslations("Home"), getLocale()]);
  const formalities = services.find((s) => s.slug === "visa-et-formalites");
  const insurance = services.find((s) => s.slug === "assurance-voyage");
  const countries = [...new Map(visas.map((v) => [v.destination_country_code, v])).values()];

  return (
    <Section>
      <SectionHeader eyebrow={t("visaEyebrow")} title={t("visaTitle")} text={t("visaText")} />
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {countries.map((visa) => (
          <li key={visa.id}>
            <Link
              href={`/visa/${visa.country_slug}`}
              className="group flex items-center gap-4 rounded-2xl border bg-card p-5 transition-all hover:-translate-y-0.5 hover:border-ocean-300 hover:shadow-lg motion-reduce:hover:translate-y-0"
            >
              <span aria-hidden="true" className="text-4xl leading-none">{countryFlag(visa.destination_country_code)}</span>
              <span className="flex flex-1 flex-col">
                <span className="font-heading text-lg font-semibold text-ocean-950">
                  {countryName(visa.destination_country_code, locale)}
                </span>
                <span className="text-sm text-muted-foreground">{visa.visa_type}</span>
              </span>
              <span className="text-end">
                {visa.fees ? (
                  <>
                    <span className="block text-xs text-muted-foreground">{t("visaFrom")}</span>
                    <Price value={visa.fees} />
                  </>
                ) : (
                  <span className="text-sm font-medium text-ocean-700">{t("visaOnRequest")}</span>
                )}
              </span>
            </Link>
          </li>
        ))}
      </ul>

      {(formalities?.prices.length || insurance?.prices.length) && (
        <div className="grid gap-6 lg:grid-cols-2">
          {[
            { service: formalities, title: t("formalitiesTitle"), note: null },
            { service: insurance, title: t("insuranceTitle"), note: t("insuranceZones") },
          ].map(({ service, title, note }) =>
            service?.prices.length ? (
              <div key={service.slug} className="rounded-2xl border bg-ocean-50/60 p-6">
                <h3 className="text-xl font-semibold text-ocean-900">{title}</h3>
                {note && <p className="mt-1 text-sm text-muted-foreground">{note}</p>}
                <dl className="mt-4 divide-y divide-ocean-100">
                  {service.prices.map((price) => (
                    <div key={price.id} className="flex items-baseline justify-between gap-4 py-2.5">
                      <dt className="text-sm text-ocean-950">{price.label}</dt>
                      <dd className="shrink-0 text-end">
                        <Price value={price.price} compact />
                        {price.unit && <span className="text-sm text-muted-foreground"> / {price.unit}</span>}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            ) : null,
          )}
        </div>
      )}
    </Section>
  );
}

const PILLARS: { key: string; icon: LucideIcon }[] = [
  { key: "pillar1", icon: MedalIcon },
  { key: "pillar2", icon: HeartHandshakeIcon },
  { key: "pillar3", icon: GlobeIcon },
  { key: "pillar4", icon: HeadsetIcon },
];

export async function AboutSection() {
  const t = await getTranslations("Home");
  return (
    <Section tone="tint">
      <div className="grid items-center gap-10 lg:grid-cols-2">
        <div className="relative">
          <Image
            src="/images/equipe-impact-voyage.jpg"
            alt={t("teamAlt")}
            width={1080}
            height={810}
            sizes="(min-width: 1024px) 50vw, 100vw"
            className="rounded-3xl object-cover shadow-xl"
          />
          <span className="absolute -bottom-4 start-6 rounded-2xl bg-cta px-4 py-2 font-script text-2xl text-cta-foreground shadow-lg">
            Impact Voyage
          </span>
        </div>
        <div className="flex flex-col gap-6">
          <SectionHeading eyebrow={t("aboutEyebrow")} title={t("aboutTitle")} description={t("aboutText")} />
          <ul className="grid gap-4 sm:grid-cols-2">
            {PILLARS.map(({ key, icon: Icon }) => (
              <li key={key} className="flex gap-3">
                <Icon aria-hidden="true" className="mt-0.5 size-6 shrink-0 text-sunset-600" />
                <div>
                  <h3 className="font-semibold text-ocean-950">{t(`${key}Title`)}</h3>
                  <p className="text-sm text-muted-foreground">{t(`${key}Text`)}</p>
                </div>
              </li>
            ))}
          </ul>
          <Link href="/a-propos" className={cn(buttonVariants({ size: "lg" }), "w-fit")}>
            {t("aboutCta")}
          </Link>
        </div>
      </div>
    </Section>
  );
}

const REASONS: { key: string; icon: LucideIcon }[] = [
  { key: "why1", icon: GlobeIcon },
  { key: "why2", icon: ZapIcon },
  { key: "why3", icon: WalletIcon },
  { key: "why4", icon: MapPinIcon },
  { key: "why5", icon: RefreshCwIcon },
  { key: "why6", icon: HeadsetIcon },
];

export async function WhyUsSection() {
  const t = await getTranslations("Home");
  return (
    <section className="bg-ocean-950 py-16 text-white sm:py-20">
      <Container className="flex flex-col gap-10">
        <div className="flex max-w-3xl flex-col gap-2">
          <p className="text-sm font-semibold uppercase tracking-wider text-sunset-400">{t("whyEyebrow")}</p>
          <h2 className="text-balance text-3xl font-bold sm:text-4xl">{t("whyTitle")}</h2>
          <p className="text-lg text-ocean-100">{t("whyText")}</p>
        </div>
        <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {REASONS.map(({ key, icon: Icon }) => (
            <li key={key} className="flex flex-col gap-3 rounded-2xl bg-white/5 p-6 ring-1 ring-white/10">
              <span className="flex size-12 items-center justify-center rounded-xl bg-sunset-500 text-ocean-950">
                <Icon aria-hidden="true" className="size-6" />
              </span>
              <h3 className="text-lg font-semibold">{t(`${key}Title`)}</h3>
              <p className="text-sm text-ocean-100">{t(`${key}Text`)}</p>
            </li>
          ))}
        </ul>
      </Container>
    </section>
  );
}

export async function ResidencesSection({ residences }: { residences: ResidenceList[] }) {
  if (!residences.length) return null;
  const t = await getTranslations("Home");
  return (
    <Section>
      <SectionHeader eyebrow={t("stayEyebrow")} title={t("stayTitle")} href="/residences" linkLabel={t("allResidences")} />
      <div className={grid}>
        {residences.map((residence) => (
          <ContentCard
            key={residence.id}
            href={`/residences/${residence.slug}`}
            title={residence.name}
            eyebrow={residence.destination.name}
            description={residence.short_description}
            image={residence.cover_image}
            imageAlt={residence.cover_alt || residence.name}
            meta={
              <span className="inline-flex items-center gap-1">
                <UsersIcon aria-hidden="true" className="size-4" /> {residence.capacity}
              </span>
            }
            footer={<Price value={residence.price_per_night} from unit="night" />}
          />
        ))}
      </div>
    </Section>
  );
}

export async function EventsSection({ events }: { events: EventList[] }) {
  if (!events.length) return null;
  const [t, locale] = await Promise.all([getTranslations("Home"), getLocale()]);
  return (
    <Section tone="tint">
      <SectionHeader eyebrow={t("eventsEyebrow")} title={t("eventsTitle")} href="/evenements" linkLabel={t("allEvents")} />
      <div className={grid}>
        {events.map((event) => (
          <ContentCard
            key={event.id}
            href={`/evenements/${event.slug}`}
            title={event.title}
            description={event.short_description}
            image={event.cover_image}
            imageAlt={event.cover_alt || event.title}
            meta={
              <>
                <span className="inline-flex items-center gap-1">
                  <CalendarDaysIcon aria-hidden="true" className="size-4" /> {formatDate(event.date, locale)}
                </span>
                <span className="inline-flex items-center gap-1">
                  <MapPinIcon aria-hidden="true" className="size-4" /> {event.location}
                </span>
              </>
            }
          />
        ))}
      </div>
    </Section>
  );
}

export async function ReviewsSection({ reviews }: { reviews: Review[] }) {
  if (!reviews.length) return null;
  const t = await getTranslations("Home");
  return (
    <Section>
      <SectionHeader eyebrow={t("reviewsEyebrow")} title={t("reviewsTitle")} />
      <ul className={grid}>
        {reviews.map((review) => (
          <li key={review.id} className="flex flex-col gap-4 rounded-2xl border bg-card p-6">
            <QuoteIcon aria-hidden="true" className="size-8 text-sunset-500" />
            <blockquote className="flex-1 text-ocean-950">{review.comment}</blockquote>
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold text-ocean-900">{review.author_name}</span>
              <Rating value={review.rating} />
            </div>
          </li>
        ))}
      </ul>
    </Section>
  );
}

export async function ContactBand({ settings }: { settings: Partial<SiteSettings> }) {
  const t = await getTranslations();
  const whatsapp = whatsappUrl(settings.whatsapp);
  return (
    <section className="bg-gradient-to-r from-ocean-700 to-ocean-900 py-14 text-white">
      <Container className="flex flex-col items-center justify-between gap-6 text-center lg:flex-row lg:text-start">
        <div className="flex flex-col gap-2">
          <h2 className="text-3xl font-bold">{t("Home.ctaTitle")}</h2>
          <p className="text-lg text-ocean-100">{t("Home.ctaText")}</p>
          <ul className="mt-2 flex flex-wrap justify-center gap-x-6 gap-y-1 text-sm text-ocean-100 lg:justify-start">
            <li className="inline-flex items-center gap-1.5"><CheckCircle2Icon aria-hidden="true" className="size-4 text-sunset-400" /> {t("Home.pillar2Title")}</li>
            <li className="inline-flex items-center gap-1.5"><CheckCircle2Icon aria-hidden="true" className="size-4 text-sunset-400" /> {t("Home.why3Title")}</li>
            <li className="inline-flex items-center gap-1.5"><CheckCircle2Icon aria-hidden="true" className="size-4 text-sunset-400" /> {t("Home.why6Title")}</li>
          </ul>
        </div>
        <div className="flex flex-wrap justify-center gap-3">
          <Link href="/devis" className={buttonVariants({ variant: "cta", size: "lg" })}>
            {t("Nav.quote")}
          </Link>
          {whatsapp && (
            <a href={whatsapp} target="_blank" rel="noopener noreferrer" className={buttonVariants({ variant: "inverse", size: "lg" })}>
              <SocialIcon network="whatsapp" className="size-5" />
              {t("Home.ctaWhatsapp")}
            </a>
          )}
          {settings.phone && (
            <a
              href={`tel:${settings.phone.replace(/\s/g, "")}`}
              className={cn(buttonVariants({ variant: "outline", size: "lg" }), "border-white/40 bg-transparent text-white hover:bg-white/10 hover:text-white")}
            >
              <PhoneIcon aria-hidden="true" data-icon="inline-start" />
              {t("Home.ctaCall")}
            </a>
          )}
        </div>
      </Container>
    </section>
  );
}
